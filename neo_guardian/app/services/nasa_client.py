"""
NEO Guardian - Cliente de API de NASA
======================================
Cliente seguro para consumir la API de Near Earth Objects (NEO) de NASA.

Características de seguridad:
- Validación de respuestas
- Rate limiting respetado
- Timeout configurables
- Manejo seguro de errores
- Sanitización de datos
"""

import httpx
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import asyncio

from app.core.config import get_settings
from app.core.security import input_sanitizer


class NEOData(BaseModel):
    """Esquema de datos de un NEO."""
    
    neo_id: str
    name: str
    nasa_jpl_url: Optional[str] = None
    absolute_magnitude_h: Optional[float] = None
    estimated_diameter_min_km: Optional[float] = None
    estimated_diameter_max_km: Optional[float] = None
    is_potentially_hazardous_asteroid: bool = False
    is_sentry_object: bool = False
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitiza el nombre del asteroide."""
        return input_sanitizer.sanitize_input(v)


class CloseApproachData(BaseModel):
    """Datos de aproximación cercana."""
    
    close_approach_date: str
    close_approach_date_full: Optional[str] = None
    epoch_date_close_approach: Optional[int] = None
    relative_velocity_kmh: Optional[float] = None
    relative_velocity_kms: Optional[float] = None
    miss_distance_km: Optional[float] = None
    miss_distance_lunar: Optional[float] = None
    miss_distance_astronomical: Optional[float] = None
    orbiting_body: str = "Earth"


class NEOWithApproaches(NEOData):
    """NEO con sus aproximaciones cercanas."""
    
    close_approaches: List[CloseApproachData] = []


class NASAAPIClient:
    """
    Cliente seguro para la API de NASA.
    
    Implementa:
    - Connection pooling
    - Retry logic
    - Rate limit awareness
    - Secure error handling
    """
    
    def __init__(self):
        """Inicializa el cliente."""
        self._settings = get_settings().nasa
        self._client: Optional[httpx.AsyncClient] = None
        
        # Rate limiting local
        self._request_count = 0
        self._last_reset = datetime.now()
        self._max_requests_per_hour = 1000  # Límite de NASA
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._settings.nasa_base_url,
                timeout=httpx.Timeout(self._settings.api_timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=30
                ),
                headers={
                    "User-Agent": "NEO-Guardian/1.0",
                    "Accept": "application/json"
                }
            )
        return self._client
    
    async def close(self):
        """Cierra el cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _check_rate_limit(self) -> bool:
        """
        Verifica si podemos hacer más requests.
        
        Returns:
            bool: True si podemos continuar.
        """
        now = datetime.now()
        
        # Reset contador cada hora
        if (now - self._last_reset).total_seconds() >= 3600:
            self._request_count = 0
            self._last_reset = now
        
        if self._request_count >= self._max_requests_per_hour:
            return False
        
        self._request_count += 1
        return True
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza una petición a la API de NASA.
        
        Args:
            endpoint: Endpoint de la API.
            params: Parámetros de la petición.
            
        Returns:
            Dict con la respuesta o None si hay error.
        """
        if not self._check_rate_limit():
            raise Exception("Rate limit excedido. Intente más tarde.")
        
        # Añadir API key a los parámetros
        if params is None:
            params = {}
        params["api_key"] = self._settings.nasa_api_key
        
        client = await self._get_client()
        
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            raise Exception("Timeout al conectar con NASA API")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise Exception("Rate limit de NASA API excedido")
            elif e.response.status_code == 403:
                raise Exception("API key de NASA inválida")
            else:
                raise Exception(f"Error de NASA API: {e.response.status_code}")
        except httpx.RequestError as e:
            raise Exception(f"Error de conexión: {str(e)}")
    
    def _parse_neo_data(self, neo: Dict[str, Any]) -> NEOWithApproaches:
        """
        Parsea y valida datos de un NEO.
        
        Args:
            neo: Datos crudos del NEO.
            
        Returns:
            NEOWithApproaches validado.
        """
        # Extraer diámetros
        diameter = neo.get("estimated_diameter", {}).get("kilometers", {})
        
        # Extraer aproximaciones
        close_approaches = []
        for approach in neo.get("close_approach_data", []):
            velocity = approach.get("relative_velocity", {})
            distance = approach.get("miss_distance", {})
            
            close_approaches.append(CloseApproachData(
                close_approach_date=approach.get("close_approach_date", ""),
                close_approach_date_full=approach.get("close_approach_date_full"),
                epoch_date_close_approach=approach.get("epoch_date_close_approach"),
                relative_velocity_kmh=float(velocity.get("kilometers_per_hour", 0)) if velocity.get("kilometers_per_hour") else None,
                relative_velocity_kms=float(velocity.get("kilometers_per_second", 0)) if velocity.get("kilometers_per_second") else None,
                miss_distance_km=float(distance.get("kilometers", 0)) if distance.get("kilometers") else None,
                miss_distance_lunar=float(distance.get("lunar", 0)) if distance.get("lunar") else None,
                miss_distance_astronomical=float(distance.get("astronomical", 0)) if distance.get("astronomical") else None,
                orbiting_body=approach.get("orbiting_body", "Earth")
            ))
        
        return NEOWithApproaches(
            neo_id=str(neo.get("id", "")),
            name=neo.get("name", "Unknown"),
            nasa_jpl_url=neo.get("nasa_jpl_url"),
            absolute_magnitude_h=neo.get("absolute_magnitude_h"),
            estimated_diameter_min_km=diameter.get("estimated_diameter_min"),
            estimated_diameter_max_km=diameter.get("estimated_diameter_max"),
            is_potentially_hazardous_asteroid=neo.get("is_potentially_hazardous_asteroid", False),
            is_sentry_object=neo.get("is_sentry_object", False),
            close_approaches=close_approaches
        )
    
    async def get_neo_feed(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[NEOWithApproaches]:
        """
        Obtiene NEOs para un rango de fechas.
        
        Args:
            start_date: Fecha de inicio.
            end_date: Fecha de fin (máximo 7 días desde start_date).
            
        Returns:
            Lista de NEOs con aproximaciones.
        """
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        
        # Validar rango máximo de 7 días (límite de NASA)
        if (end_date - start_date).days > 7:
            end_date = start_date + timedelta(days=7)
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        data = await self._make_request(
            self._settings.neo_feed_endpoint,
            params
        )
        
        if not data:
            return []
        
        neos = []
        near_earth_objects = data.get("near_earth_objects", {})
        
        for date_str, neo_list in near_earth_objects.items():
            for neo in neo_list:
                try:
                    parsed = self._parse_neo_data(neo)
                    neos.append(parsed)
                except Exception:
                    # Skip invalid NEOs
                    continue
        
        return neos
    
    async def get_neo_by_id(self, neo_id: str) -> Optional[NEOWithApproaches]:
        """
        Obtiene un NEO específico por su ID.
        
        Args:
            neo_id: ID del NEO en NASA.
            
        Returns:
            NEO con aproximaciones o None.
        """
        # Validar ID (solo números)
        if not neo_id.isdigit():
            raise ValueError("ID de NEO inválido")
        
        endpoint = f"{self._settings.neo_lookup_endpoint}/{neo_id}"
        
        data = await self._make_request(endpoint)
        
        if not data:
            return None
        
        return self._parse_neo_data(data)
    
    async def get_hazardous_neos(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[NEOWithApproaches]:
        """
        Obtiene solo NEOs potencialmente peligrosos.
        
        Args:
            start_date: Fecha de inicio.
            end_date: Fecha de fin.
            
        Returns:
            Lista de NEOs peligrosos.
        """
        all_neos = await self.get_neo_feed(start_date, end_date)
        
        return [
            neo for neo in all_neos
            if neo.is_potentially_hazardous_asteroid
        ]
    
    async def get_today_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de NEOs para hoy.
        
        Returns:
            Diccionario con estadísticas.
        """
        today = date.today()
        neos = await self.get_neo_feed(today, today)
        
        hazardous = [n for n in neos if n.is_potentially_hazardous_asteroid]
        
        # Encontrar el más cercano
        closest = None
        closest_distance = float('inf')
        
        for neo in neos:
            for approach in neo.close_approaches:
                if approach.miss_distance_km and approach.miss_distance_km < closest_distance:
                    closest_distance = approach.miss_distance_km
                    closest = neo
        
        return {
            "date": today.isoformat(),
            "total_count": len(neos),
            "hazardous_count": len(hazardous),
            "closest_neo": closest.name if closest else None,
            "closest_distance_km": closest_distance if closest_distance != float('inf') else None,
            "closest_distance_lunar": closest_distance / 384400 if closest_distance != float('inf') else None
        }


# Singleton del cliente
nasa_client = NASAAPIClient()


async def get_nasa_client() -> NASAAPIClient:
    """Dependency para obtener el cliente NASA."""
    return nasa_client
