"""
NEO Guardian - Router de NEOs
==============================
Endpoints para consultar Near Earth Objects.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.models import User, NEOObject, CloseApproach
from app.services.nasa_client import (
    nasa_client,
    NEOWithApproaches,
    CloseApproachData
)
from app.api.dependencies import (
    get_current_user,
    get_optional_user,
    log_audit_event
)
from app.middleware.rate_limit import limiter


router = APIRouter(prefix="/neo", tags=["Near Earth Objects"])


class NEOResponse(BaseModel):
    """Respuesta de NEO."""
    neo_id: str
    name: str
    estimated_diameter_min_km: Optional[float]
    estimated_diameter_max_km: Optional[float]
    is_potentially_hazardous: bool
    absolute_magnitude: Optional[float]
    nasa_jpl_url: Optional[str]


class CloseApproachResponse(BaseModel):
    """Respuesta de aproximación cercana."""
    date: str
    velocity_kmh: Optional[float]
    velocity_kms: Optional[float]
    distance_km: Optional[float]
    distance_lunar: Optional[float]
    orbiting_body: str


class NEODetailResponse(NEOResponse):
    """Respuesta detallada de NEO."""
    close_approaches: List[CloseApproachResponse]


class NEOFeedResponse(BaseModel):
    """Respuesta de feed de NEOs."""
    start_date: str
    end_date: str
    total_count: int
    hazardous_count: int
    neos: List[NEODetailResponse]


class TodayStatsResponse(BaseModel):
    """Estadísticas del día."""
    date: str
    total_count: int
    hazardous_count: int
    closest_neo: Optional[str]
    closest_distance_km: Optional[float]
    closest_distance_lunar: Optional[float]
    threat_level: str  # "low", "medium", "high"


def _convert_neo_to_response(neo: NEOWithApproaches) -> NEODetailResponse:
    """Convierte NEO del cliente a respuesta API."""
    approaches = [
        CloseApproachResponse(
            date=a.close_approach_date,
            velocity_kmh=a.relative_velocity_kmh,
            velocity_kms=a.relative_velocity_kms,
            distance_km=a.miss_distance_km,
            distance_lunar=a.miss_distance_lunar,
            orbiting_body=a.orbiting_body
        )
        for a in neo.close_approaches
    ]
    
    return NEODetailResponse(
        neo_id=neo.neo_id,
        name=neo.name,
        estimated_diameter_min_km=neo.estimated_diameter_min_km,
        estimated_diameter_max_km=neo.estimated_diameter_max_km,
        is_potentially_hazardous=neo.is_potentially_hazardous_asteroid,
        absolute_magnitude=neo.absolute_magnitude_h,
        nasa_jpl_url=neo.nasa_jpl_url,
        close_approaches=approaches
    )


def _calculate_threat_level(
    hazardous_count: int,
    closest_distance_km: Optional[float]
) -> str:
    """
    Calcula el nivel de amenaza basado en datos.
    
    Criterios:
    - LOW: Sin objetos peligrosos o distancia > 5 millones km
    - MEDIUM: 1-2 objetos peligrosos o distancia 1-5 millones km
    - HIGH: >2 objetos peligrosos o distancia < 1 millón km
    """
    if closest_distance_km is None:
        return "low"
    
    if closest_distance_km < 1_000_000 or hazardous_count > 2:
        return "high"
    elif closest_distance_km < 5_000_000 or hazardous_count >= 1:
        return "medium"
    else:
        return "low"


@router.get("/today", response_model=TodayStatsResponse)
@limiter.limit("60/minute")
async def get_today_stats(
    request: Request,
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Obtiene estadísticas de NEOs para hoy.
    
    Endpoint público con información general.
    Usuarios autenticados obtienen datos adicionales.
    """
    try:
        stats = await nasa_client.get_today_stats()
        
        threat_level = _calculate_threat_level(
            stats["hazardous_count"],
            stats["closest_distance_km"]
        )
        
        return TodayStatsResponse(
            date=stats["date"],
            total_count=stats["total_count"],
            hazardous_count=stats["hazardous_count"],
            closest_neo=stats["closest_neo"],
            closest_distance_km=stats["closest_distance_km"],
            closest_distance_lunar=stats["closest_distance_lunar"],
            threat_level=threat_level
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener datos de NASA: {str(e)}"
        )


@router.get("/feed", response_model=NEOFeedResponse)
@limiter.limit("30/minute")
async def get_neo_feed(
    request: Request,
    start_date: date = Query(
        default=None,
        description="Fecha de inicio (YYYY-MM-DD). Default: hoy"
    ),
    end_date: date = Query(
        default=None,
        description="Fecha de fin (máximo 7 días desde start). Default: start + 7 días"
    ),
    hazardous_only: bool = Query(
        default=False,
        description="Solo mostrar asteroides potencialmente peligrosos"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene feed de NEOs para un rango de fechas.
    
    Requiere autenticación.
    Máximo 7 días por consulta (limitación de NASA).
    """
    if start_date is None:
        start_date = date.today()
    
    if end_date is None:
        end_date = start_date + timedelta(days=7)
    
    # Validar rango
    if (end_date - start_date).days > 7:
        raise HTTPException(
            status_code=400,
            detail="El rango máximo es de 7 días"
        )
    
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="La fecha de fin debe ser posterior a la de inicio"
        )
    
    try:
        if hazardous_only:
            neos = await nasa_client.get_hazardous_neos(start_date, end_date)
        else:
            neos = await nasa_client.get_neo_feed(start_date, end_date)
        
        # Log de consulta
        await log_audit_event(
            db=db,
            action="neo_feed_query",
            status="success",
            request=request,
            user_id=current_user.id,
            details=f"start={start_date}, end={end_date}, hazardous_only={hazardous_only}"
        )
        
        neo_responses = [_convert_neo_to_response(neo) for neo in neos]
        hazardous_count = sum(1 for n in neo_responses if n.is_potentially_hazardous)
        
        return NEOFeedResponse(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            total_count=len(neo_responses),
            hazardous_count=hazardous_count,
            neos=neo_responses
        )
    
    except Exception as e:
        await log_audit_event(
            db=db,
            action="neo_feed_query",
            status="failure",
            request=request,
            user_id=current_user.id,
            error_message=str(e)
        )
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener datos: {str(e)}"
        )


@router.get("/hazardous", response_model=List[NEODetailResponse])
@limiter.limit("30/minute")
async def get_hazardous_neos(
    request: Request,
    days: int = Query(default=7, ge=1, le=7, description="Días a consultar"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene solo NEOs potencialmente peligrosos.
    
    Útil para sistemas de alerta.
    """
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    try:
        neos = await nasa_client.get_hazardous_neos(start_date, end_date)
        
        await log_audit_event(
            db=db,
            action="hazardous_neo_query",
            status="success",
            request=request,
            user_id=current_user.id,
            details=f"days={days}, found={len(neos)}"
        )
        
        return [_convert_neo_to_response(neo) for neo in neos]
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener datos: {str(e)}"
        )


@router.get("/{neo_id}", response_model=NEODetailResponse)
@limiter.limit("60/minute")
async def get_neo_by_id(
    request: Request,
    neo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene información detallada de un NEO específico.
    """
    # Validar neo_id (solo números)
    if not neo_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="ID de NEO inválido"
        )
    
    try:
        neo = await nasa_client.get_neo_by_id(neo_id)
        
        if not neo:
            raise HTTPException(
                status_code=404,
                detail="NEO no encontrado"
            )
        
        await log_audit_event(
            db=db,
            action="neo_lookup",
            status="success",
            request=request,
            user_id=current_user.id,
            resource_type="neo",
            resource_id=neo_id
        )
        
        return _convert_neo_to_response(neo)
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener datos: {str(e)}"
        )


@router.get("/analysis/closest", response_model=List[NEODetailResponse])
@limiter.limit("20/minute")
async def get_closest_neos(
    request: Request,
    days: int = Query(default=7, ge=1, le=7),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los NEOs más cercanos ordenados por distancia.
    
    Útil para análisis de riesgo.
    """
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    try:
        neos = await nasa_client.get_neo_feed(start_date, end_date)
        
        # Ordenar por distancia mínima
        def get_min_distance(neo: NEOWithApproaches) -> float:
            distances = [
                a.miss_distance_km
                for a in neo.close_approaches
                if a.miss_distance_km is not None
            ]
            return min(distances) if distances else float('inf')
        
        sorted_neos = sorted(neos, key=get_min_distance)[:limit]
        
        await log_audit_event(
            db=db,
            action="closest_neo_analysis",
            status="success",
            request=request,
            user_id=current_user.id,
            details=f"days={days}, limit={limit}"
        )
        
        return [_convert_neo_to_response(neo) for neo in sorted_neos]
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener datos: {str(e)}"
        )


@router.get("/analysis/largest", response_model=List[NEODetailResponse])
@limiter.limit("20/minute")
async def get_largest_neos(
    request: Request,
    days: int = Query(default=7, ge=1, le=7),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los NEOs más grandes ordenados por diámetro estimado.
    """
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    try:
        neos = await nasa_client.get_neo_feed(start_date, end_date)
        
        # Ordenar por diámetro máximo
        def get_max_diameter(neo: NEOWithApproaches) -> float:
            return neo.estimated_diameter_max_km or 0
        
        sorted_neos = sorted(neos, key=get_max_diameter, reverse=True)[:limit]
        
        return [_convert_neo_to_response(neo) for neo in sorted_neos]
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener datos: {str(e)}"
        )
