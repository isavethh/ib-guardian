"""
NEO Guardian - API de Simulador e Educación
=============================================
Endpoints para simulación de impactos y módulos educativos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.models import User
from app.services.impact_simulator import (
    impact_simulator,
    ImpactSimulation,
    HistoricalImpact
)
from app.services.education import (
    education_service,
    EducationalModule,
    DifficultyLevel
)
from app.api.dependencies import get_optional_user, get_current_user, log_audit_event
from app.middleware.rate_limit import limiter


router = APIRouter(prefix="/simulator", tags=["Simulador de Impactos"])


class SimulationRequest(BaseModel):
    """Request para simulación de impacto."""
    diameter_m: float = Field(..., ge=1, le=50000, description="Diámetro en metros")
    velocity_kms: float = Field(default=17.0, ge=5, le=72, description="Velocidad en km/s")
    angle_degrees: float = Field(default=45.0, ge=5, le=90, description="Ángulo de impacto")
    density_type: str = Field(default="rock", description="Tipo: ice, porous_rock, rock, dense_rock, iron")


class QuizSubmission(BaseModel):
    """Envío de respuestas de quiz."""
    module_id: str
    answers: Dict[str, int]  # {question_id: answer_index}


# ==================== SIMULADOR ====================

@router.post("/impact", response_model=ImpactSimulation)
@limiter.limit("30/minute")
async def simulate_impact(
    request: Request,
    simulation: SimulationRequest,
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Simula un impacto de asteroide con parámetros personalizados.
    
    Retorna efectos calculados científicamente basados en:
    - Energía cinética
    - Ángulo de impacto
    - Composición del asteroide
    
    No requiere autenticación (educativo).
    """
    try:
        result = impact_simulator.simulate_impact(
            diameter_m=simulation.diameter_m,
            velocity_kms=simulation.velocity_kms,
            angle_degrees=simulation.angle_degrees,
            density_type=simulation.density_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/historical", response_model=List[HistoricalImpact])
@limiter.limit("60/minute")
async def get_historical_impacts(request: Request):
    """
    Obtiene lista de todos los impactos históricos documentados.
    
    Incluye:
    - Chicxulub (extinción de dinosaurios)
    - Tunguska (1908)
    - Chelyabinsk (2013)
    - Y otros cráteres importantes
    """
    return impact_simulator.get_historical_impacts()


@router.get("/historical/{name}", response_model=HistoricalImpact)
@limiter.limit("60/minute")
async def get_historical_impact(request: Request, name: str):
    """
    Obtiene detalles de un impacto histórico específico.
    """
    impact = impact_simulator.get_historical_impact_by_name(name)
    if not impact:
        raise HTTPException(status_code=404, detail="Impacto no encontrado")
    return impact


@router.get("/historical/{name}/simulate", response_model=ImpactSimulation)
@limiter.limit("30/minute")
async def simulate_historical_impact(request: Request, name: str):
    """
    Simula los efectos de un impacto histórico conocido.
    
    Útil para comparar con las consecuencias reales documentadas.
    """
    result = impact_simulator.simulate_historical_impact(name)
    if not result:
        raise HTTPException(status_code=404, detail="Impacto no encontrado")
    return result


@router.get("/compare")
@limiter.limit("30/minute")
async def compare_impacts(
    request: Request,
    diameter1: float = Query(..., ge=1, le=50000),
    diameter2: float = Query(..., ge=1, le=50000)
):
    """
    Compara dos escenarios de impacto diferentes.
    """
    sim1 = impact_simulator.simulate_impact(diameter1)
    sim2 = impact_simulator.simulate_impact(diameter2)
    
    return {
        "asteroid_1": {
            "diameter_m": diameter1,
            "energy_megatons": sim1.impact_energy_megatons,
            "crater_km": sim1.effects.crater_diameter_km,
            "type": sim1.impact_type.value
        },
        "asteroid_2": {
            "diameter_m": diameter2,
            "energy_megatons": sim2.impact_energy_megatons,
            "crater_km": sim2.effects.crater_diameter_km,
            "type": sim2.impact_type.value
        },
        "comparison": {
            "energy_ratio": round(sim2.impact_energy_megatons / sim1.impact_energy_megatons, 2) if sim1.impact_energy_megatons > 0 else 0,
            "crater_ratio": round(sim2.effects.crater_diameter_km / sim1.effects.crater_diameter_km, 2) if sim1.effects.crater_diameter_km > 0 else 0
        }
    }


# ==================== EDUCACIÓN ====================

education_router = APIRouter(prefix="/education", tags=["Módulos Educativos"])


@education_router.get("/modules", response_model=List[EducationalModule])
@limiter.limit("60/minute")
async def get_all_modules(
    request: Request,
    difficulty: Optional[DifficultyLevel] = None
):
    """
    Obtiene todos los módulos educativos disponibles.
    
    Opcional: filtrar por nivel de dificultad.
    """
    if difficulty:
        return education_service.get_modules_by_difficulty(difficulty)
    return education_service.get_all_modules()


@education_router.get("/modules/{module_id}", response_model=EducationalModule)
@limiter.limit("60/minute")
async def get_module(request: Request, module_id: str):
    """
    Obtiene un módulo educativo específico con todo su contenido.
    """
    module = education_service.get_module_by_id(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    return module


@education_router.post("/modules/{module_id}/quiz")
@limiter.limit("20/minute")
async def submit_quiz(
    request: Request,
    module_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Envía respuestas de un quiz y obtiene resultados.
    
    Requiere autenticación para guardar progreso.
    """
    results = education_service.check_quiz_answers(
        module_id=module_id,
        answers=submission.answers
    )
    
    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
    
    # Log del progreso
    await log_audit_event(
        db=db,
        action="quiz_completed",
        status="success",
        request=request,
        user_id=current_user.id,
        resource_type="education_module",
        resource_id=module_id,
        details=f"score={results['percentage']}%, points={results['total_points']}"
    )
    
    return results


@education_router.get("/achievements")
async def get_all_achievements():
    """
    Lista todos los logros posibles en el sistema educativo.
    """
    all_achievements = []
    for module in education_service.get_all_modules():
        for achievement in module.achievements:
            if achievement not in all_achievements:
                all_achievements.append({
                    "achievement": achievement,
                    "module_id": module.id,
                    "module_title": module.title
                })
    return all_achievements
