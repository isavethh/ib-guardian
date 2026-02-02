"""
NEO Guardian - Simulador de Impactos
=====================================
Simula impactos de asteroides basado en datos científicos reales.
Incluye impactos históricos documentados.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import math


class ImpactType(str, Enum):
    """Tipos de impacto según energía."""
    AIRBURST = "airburst"           # Explosión en atmósfera
    CRATER_SMALL = "crater_small"    # Cráter pequeño (<1km)
    CRATER_MEDIUM = "crater_medium"  # Cráter mediano (1-10km)
    CRATER_LARGE = "crater_large"    # Cráter grande (10-100km)
    EXTINCTION = "extinction"        # Evento de extinción (>100km)


class ImpactEffect(BaseModel):
    """Efectos de un impacto."""
    crater_diameter_km: float
    fireball_radius_km: float
    thermal_radiation_radius_km: float
    shockwave_radius_km: float
    earthquake_magnitude: float
    tsunami_height_m: Optional[float] = None
    dust_cloud_duration_years: Optional[float] = None
    global_temperature_change_c: Optional[float] = None


class ImpactSimulation(BaseModel):
    """Resultado de una simulación de impacto."""
    asteroid_diameter_m: float
    asteroid_velocity_kms: float
    impact_angle_degrees: float
    asteroid_density_kgm3: float
    impact_energy_megatons: float
    impact_energy_joules: float
    impact_type: ImpactType
    effects: ImpactEffect
    casualties_estimate: Optional[Dict[str, Any]] = None
    comparison: str  # Comparación con eventos conocidos


class HistoricalImpact(BaseModel):
    """Impacto histórico documentado."""
    name: str
    date: str
    location: str
    latitude: float
    longitude: float
    asteroid_diameter_m: float
    crater_diameter_km: Optional[float]
    energy_megatons: float
    description: str
    consequences: List[str]
    fatalities: Optional[int]
    image_url: Optional[str] = None
    discovered_year: Optional[int] = None


# Base de datos de impactos históricos
HISTORICAL_IMPACTS: List[Dict[str, Any]] = [
    {
        "name": "Chicxulub",
        "date": "Hace 66 millones de años",
        "location": "Península de Yucatán, México",
        "latitude": 21.4,
        "longitude": -89.5,
        "asteroid_diameter_m": 10000,  # 10 km
        "crater_diameter_km": 180,
        "energy_megatons": 100000000000,  # 100 billones de megatones
        "description": "El impacto que causó la extinción de los dinosaurios. Creó un invierno nuclear que duró años.",
        "consequences": [
            "Extinción del 75% de todas las especies",
            "Extinción de todos los dinosaurios no aviares",
            "Invierno de impacto de 10+ años",
            "Tsunamis de 100+ metros de altura",
            "Incendios forestales globales",
            "Colapso de la cadena alimenticia"
        ],
        "fatalities": None,
        "discovered_year": 1978,
        "image_url": "/static/images/chicxulub.jpg"
    },
    {
        "name": "Vredefort",
        "date": "Hace 2.023 millones de años",
        "location": "Sudáfrica",
        "latitude": -27.0,
        "longitude": 27.5,
        "asteroid_diameter_m": 15000,  # 15 km
        "crater_diameter_km": 300,
        "energy_megatons": 500000000000,
        "description": "El cráter de impacto verificado más grande en la Tierra. El asteroide era más grande que el que mató a los dinosaurios.",
        "consequences": [
            "El cráter más grande conocido en la Tierra",
            "Posible evento de extinción masiva",
            "Reestructuración geológica de la región",
            "Ondas sísmicas globales"
        ],
        "fatalities": None,
        "discovered_year": 1920
    },
    {
        "name": "Sudbury",
        "date": "Hace 1.849 millones de años",
        "location": "Ontario, Canadá",
        "latitude": 46.6,
        "longitude": -81.2,
        "asteroid_diameter_m": 12000,
        "crater_diameter_km": 130,
        "energy_megatons": 100000000000,
        "description": "Uno de los cráteres más grandes y mejor preservados. Hoy es fuente de níquel, cobre y platino.",
        "consequences": [
            "Rico depósito de minerales",
            "Segundo cráter más grande de la Tierra",
            "Deformación de 200km de la corteza"
        ],
        "fatalities": None,
        "discovered_year": 1891
    },
    {
        "name": "Tunguska",
        "date": "30 de junio de 1908",
        "location": "Siberia, Rusia",
        "latitude": 60.9,
        "longitude": 101.9,
        "asteroid_diameter_m": 50,
        "crater_diameter_km": 0,  # No dejó cráter - explotó en el aire
        "energy_megatons": 15,
        "description": "La mayor explosión de un cuerpo cósmico en la historia registrada. Explotó a 5-10 km de altura.",
        "consequences": [
            "2,150 km² de bosque destruido",
            "80 millones de árboles derribados",
            "Ventanas rotas a 400 km de distancia",
            "Ondas sísmicas detectadas globalmente",
            "Noches brillantes en Europa por semanas"
        ],
        "fatalities": 0,  # Área despoblada
        "discovered_year": 1908,
        "image_url": "/static/images/tunguska.jpg"
    },
    {
        "name": "Chelyabinsk",
        "date": "15 de febrero de 2013",
        "location": "Chelyabinsk, Rusia",
        "latitude": 54.8,
        "longitude": 61.1,
        "asteroid_diameter_m": 20,
        "crater_diameter_km": 0,
        "energy_megatons": 0.5,
        "description": "El evento de impacto más reciente significativo. Explotó a 29.7 km de altura con la fuerza de 30 bombas de Hiroshima.",
        "consequences": [
            "1,500 personas heridas (principalmente por vidrios rotos)",
            "7,200 edificios dañados",
            "Flash más brillante que el Sol",
            "Ondas de choque rompieron ventanas en 6 ciudades"
        ],
        "fatalities": 0,
        "discovered_year": 2013,
        "image_url": "/static/images/chelyabinsk.jpg"
    },
    {
        "name": "Barringer (Meteor Crater)",
        "date": "Hace 50,000 años",
        "location": "Arizona, Estados Unidos",
        "latitude": 35.0,
        "longitude": -111.0,
        "asteroid_diameter_m": 50,
        "crater_diameter_km": 1.2,
        "energy_megatons": 10,
        "description": "El cráter de impacto mejor preservado en la Tierra. Primer cráter reconocido como de origen extraterrestre.",
        "consequences": [
            "Cráter de 170 metros de profundidad",
            "Destrucción en radio de 10 km",
            "Vientos de 1,000 km/h en el área",
            "Sitio turístico y de investigación"
        ],
        "fatalities": None,
        "discovered_year": 1891,
        "image_url": "/static/images/barringer.jpg"
    },
    {
        "name": "Popigai",
        "date": "Hace 35.7 millones de años",
        "location": "Siberia, Rusia",
        "latitude": 71.7,
        "longitude": 111.0,
        "asteroid_diameter_m": 5000,
        "crater_diameter_km": 100,
        "energy_megatons": 10000000000,
        "description": "Cuarto cráter más grande. Contiene el depósito de diamantes de impacto más grande del mundo.",
        "consequences": [
            "Depósito masivo de diamantes de impacto",
            "Posible contribución a extinción Eoceno-Oligoceno",
            "Cráter de 100 km de diámetro"
        ],
        "fatalities": None,
        "discovered_year": 1946
    },
    {
        "name": "Manicouagan",
        "date": "Hace 214 millones de años",
        "location": "Quebec, Canadá",
        "latitude": 51.4,
        "longitude": -68.7,
        "asteroid_diameter_m": 5000,
        "crater_diameter_km": 85,
        "energy_megatons": 5000000000,
        "description": "El 'Ojo de Quebec'. Visible desde el espacio como un anillo de agua perfecto.",
        "consequences": [
            "Lago en forma de anillo de 70 km",
            "Posible vinculación con extinción Triásico-Jurásico",
            "Visible desde el espacio"
        ],
        "fatalities": None,
        "discovered_year": 1966,
        "image_url": "/static/images/manicouagan.jpg"
    }
]


class ImpactSimulator:
    """
    Simulador de impactos de asteroides.
    
    Basado en el modelo de Purdue University "Impact: Earth!"
    y datos del NASA Jet Propulsion Laboratory.
    """
    
    # Constantes físicas
    EARTH_GRAVITY = 9.81  # m/s²
    EARTH_ESCAPE_VELOCITY = 11.2  # km/s
    ATMOSPHERE_SCALE_HEIGHT = 8500  # metros
    TNT_ENERGY_DENSITY = 4.184e9  # J/megaton
    
    # Densidades típicas de asteroides (kg/m³)
    DENSITIES = {
        "ice": 1000,
        "porous_rock": 1500,
        "rock": 2500,
        "dense_rock": 3000,
        "iron": 7800
    }
    
    def __init__(self):
        self.historical_impacts = [
            HistoricalImpact(**impact) for impact in HISTORICAL_IMPACTS
        ]
    
    def calculate_impact_energy(
        self,
        diameter_m: float,
        velocity_kms: float,
        density_kgm3: float
    ) -> tuple[float, float]:
        """
        Calcula la energía de impacto.
        
        Args:
            diameter_m: Diámetro del asteroide en metros
            velocity_kms: Velocidad en km/s
            density_kgm3: Densidad en kg/m³
            
        Returns:
            (energia_joules, energia_megatones)
        """
        # Volumen (esfera)
        radius = diameter_m / 2
        volume = (4/3) * math.pi * (radius ** 3)
        
        # Masa
        mass = volume * density_kgm3
        
        # Velocidad en m/s
        velocity_ms = velocity_kms * 1000
        
        # Energía cinética: E = 0.5 * m * v²
        energy_joules = 0.5 * mass * (velocity_ms ** 2)
        
        # Convertir a megatones de TNT
        energy_megatons = energy_joules / (4.184e15)
        
        return energy_joules, energy_megatons
    
    def determine_impact_type(self, energy_megatons: float, diameter_m: float) -> ImpactType:
        """Determina el tipo de impacto según la energía."""
        if diameter_m < 25:
            return ImpactType.AIRBURST
        elif energy_megatons < 1000:
            return ImpactType.CRATER_SMALL
        elif energy_megatons < 1000000:
            return ImpactType.CRATER_MEDIUM
        elif energy_megatons < 100000000000:
            return ImpactType.CRATER_LARGE
        else:
            return ImpactType.EXTINCTION
    
    def calculate_crater_diameter(
        self,
        energy_joules: float,
        target_density: float = 2500
    ) -> float:
        """
        Calcula el diámetro del cráter usando la relación de Pi-scaling.
        
        Fórmula simplificada basada en Schmidt-Holsapple scaling.
        """
        # Constante empírica
        K = 0.074
        
        # Diámetro en metros
        crater_diameter = K * (energy_joules ** 0.294) * (target_density ** -0.44)
        
        return crater_diameter / 1000  # Convertir a km
    
    def calculate_effects(
        self,
        energy_megatons: float,
        energy_joules: float,
        diameter_m: float,
        is_airburst: bool = False
    ) -> ImpactEffect:
        """Calcula todos los efectos del impacto."""
        
        # Diámetro del cráter
        if is_airburst:
            crater_km = 0
        else:
            crater_km = self.calculate_crater_diameter(energy_joules)
        
        # Radio de la bola de fuego (aproximación)
        fireball_km = 0.002 * (energy_megatons ** 0.4)
        
        # Radio de radiación térmica severa
        thermal_km = 0.02 * (energy_megatons ** 0.41)
        
        # Radio de onda de choque dañina (20 psi)
        shockwave_km = 0.28 * (energy_megatons ** 0.33)
        
        # Magnitud del terremoto (escala Richter)
        if energy_megatons > 0:
            earthquake_mag = 0.67 * math.log10(energy_megatons * 4.184e15) - 5.87
            earthquake_mag = max(0, min(earthquake_mag, 12))
        else:
            earthquake_mag = 0
        
        # Tsunami (solo para impactos oceánicos grandes)
        tsunami_height = None
        if energy_megatons > 100 and crater_km > 0:
            tsunami_height = 10 * (energy_megatons / 1000) ** 0.25
        
        # Efectos globales para impactos masivos
        dust_duration = None
        temp_change = None
        if energy_megatons > 1e10:
            dust_duration = math.log10(energy_megatons) - 8
            temp_change = -5 * (energy_megatons / 1e11) ** 0.3
        
        return ImpactEffect(
            crater_diameter_km=round(crater_km, 2),
            fireball_radius_km=round(fireball_km, 2),
            thermal_radiation_radius_km=round(thermal_km, 2),
            shockwave_radius_km=round(shockwave_km, 2),
            earthquake_magnitude=round(earthquake_mag, 1),
            tsunami_height_m=round(tsunami_height, 1) if tsunami_height else None,
            dust_cloud_duration_years=round(dust_duration, 1) if dust_duration else None,
            global_temperature_change_c=round(temp_change, 1) if temp_change else None
        )
    
    def get_comparison(self, energy_megatons: float) -> str:
        """Compara la energía con eventos conocidos."""
        hiroshima = 0.015  # 15 kilotones
        tsar_bomba = 50  # 50 megatones
        tunguska = 15
        chicxulub = 1e11
        
        if energy_megatons < 0.001:
            return f"Equivalente a {energy_megatons * 1000:.1f} kilotones de TNT"
        elif energy_megatons < 1:
            ratio = energy_megatons / hiroshima
            return f"Equivalente a {ratio:.0f} bombas de Hiroshima"
        elif energy_megatons < 100:
            ratio = energy_megatons / hiroshima
            return f"Equivalente a {ratio:.0f} bombas de Hiroshima o {energy_megatons/tsar_bomba:.1f} Tsar Bombas"
        elif energy_megatons < 1000:
            ratio = energy_megatons / tunguska
            return f"Aproximadamente {ratio:.0f} veces el evento Tunguska"
        elif energy_megatons < 1e9:
            return f"{energy_megatons/1e6:.2f} millones de megatones - Evento de extinción regional"
        else:
            ratio = energy_megatons / chicxulub
            return f"Aproximadamente {ratio:.1%} de la energía del impacto Chicxulub - Evento de extinción global"
    
    def simulate_impact(
        self,
        diameter_m: float,
        velocity_kms: float = 17.0,
        angle_degrees: float = 45.0,
        density_type: str = "rock"
    ) -> ImpactSimulation:
        """
        Simula un impacto de asteroide.
        
        Args:
            diameter_m: Diámetro del asteroide en metros
            velocity_kms: Velocidad de impacto en km/s (default: 17 km/s promedio)
            angle_degrees: Ángulo de impacto en grados (default: 45°)
            density_type: Tipo de asteroide (ice, porous_rock, rock, dense_rock, iron)
            
        Returns:
            ImpactSimulation con todos los datos calculados
        """
        # Obtener densidad
        density = self.DENSITIES.get(density_type, 2500)
        
        # Calcular energía
        energy_joules, energy_megatons = self.calculate_impact_energy(
            diameter_m, velocity_kms, density
        )
        
        # Ajustar por ángulo de impacto
        angle_factor = math.sin(math.radians(angle_degrees))
        energy_megatons *= angle_factor
        energy_joules *= angle_factor
        
        # Determinar tipo de impacto
        impact_type = self.determine_impact_type(energy_megatons, diameter_m)
        
        # Calcular efectos
        is_airburst = impact_type == ImpactType.AIRBURST
        effects = self.calculate_effects(
            energy_megatons, energy_joules, diameter_m, is_airburst
        )
        
        # Comparación
        comparison = self.get_comparison(energy_megatons)
        
        return ImpactSimulation(
            asteroid_diameter_m=diameter_m,
            asteroid_velocity_kms=velocity_kms,
            impact_angle_degrees=angle_degrees,
            asteroid_density_kgm3=density,
            impact_energy_megatons=round(energy_megatons, 4),
            impact_energy_joules=energy_joules,
            impact_type=impact_type,
            effects=effects,
            comparison=comparison
        )
    
    def get_historical_impacts(self) -> List[HistoricalImpact]:
        """Retorna todos los impactos históricos."""
        return self.historical_impacts
    
    def get_historical_impact_by_name(self, name: str) -> Optional[HistoricalImpact]:
        """Busca un impacto histórico por nombre."""
        for impact in self.historical_impacts:
            if impact.name.lower() == name.lower():
                return impact
        return None
    
    def simulate_historical_impact(self, name: str) -> Optional[ImpactSimulation]:
        """Simula un impacto histórico conocido."""
        impact = self.get_historical_impact_by_name(name)
        if not impact:
            return None
        
        # Estimar velocidad basada en tipo
        velocity = 17.0  # Promedio para asteroides
        if impact.asteroid_diameter_m > 5000:
            velocity = 20.0  # Asteroides grandes tienden a ser más rápidos
        
        return self.simulate_impact(
            diameter_m=impact.asteroid_diameter_m,
            velocity_kms=velocity,
            angle_degrees=45.0,
            density_type="rock"
        )


# Singleton
impact_simulator = ImpactSimulator()
