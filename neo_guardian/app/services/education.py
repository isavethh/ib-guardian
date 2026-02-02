"""
NEO Guardian - Módulos Educativos
==================================
Contenido educativo interactivo sobre asteroides y defensa planetaria.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DifficultyLevel(str, Enum):
    """Niveles de dificultad."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuizQuestion(BaseModel):
    """Pregunta de quiz."""
    id: str
    question: str
    options: List[str]
    correct_answer: int  # Índice de la respuesta correcta
    explanation: str
    points: int = 10


class EducationalModule(BaseModel):
    """Módulo educativo."""
    id: str
    title: str
    description: str
    difficulty: DifficultyLevel
    duration_minutes: int
    icon: str
    sections: List[Dict[str, Any]]
    quiz: Optional[List[QuizQuestion]] = None
    achievements: List[str] = []


# Base de datos de módulos educativos
EDUCATIONAL_MODULES: List[Dict[str, Any]] = [
    {
        "id": "intro_asteroids",
        "title": "¿Qué son los Asteroides?",
        "description": "Aprende los fundamentos sobre asteroides, cometas y objetos cercanos a la Tierra.",
        "difficulty": "beginner",
        "duration_minutes": 10,
        "icon": "🪨",
        "sections": [
            {
                "type": "text",
                "title": "Definición",
                "content": """
                    Los **asteroides** son rocas espaciales que orbitan el Sol. Son restos de la 
                    formación del Sistema Solar hace 4.6 mil millones de años. A diferencia de 
                    los planetas, son demasiado pequeños para ser redondos por su propia gravedad.
                    
                    La mayoría se encuentran en el **Cinturón de Asteroides** entre Marte y Júpiter,
                    pero algunos tienen órbitas que los acercan a la Tierra.
                """
            },
            {
                "type": "comparison",
                "title": "Asteroides vs Cometas vs Meteoritos",
                "items": [
                    {
                        "name": "Asteroide",
                        "icon": "🪨",
                        "description": "Roca espacial que orbita el Sol",
                        "composition": "Roca y metal",
                        "size": "1m - 1000km"
                    },
                    {
                        "name": "Cometa",
                        "icon": "☄️",
                        "description": "Hielo y roca que desarrolla cola cerca del Sol",
                        "composition": "Hielo, polvo y roca",
                        "size": "1km - 50km"
                    },
                    {
                        "name": "Meteoroide",
                        "icon": "✨",
                        "description": "Fragmento pequeño en el espacio",
                        "composition": "Roca o metal",
                        "size": "< 1m"
                    },
                    {
                        "name": "Meteoro",
                        "icon": "🌠",
                        "description": "Meteoroide ardiendo en la atmósfera (estrella fugaz)",
                        "composition": "Cualquiera",
                        "size": "Visible"
                    },
                    {
                        "name": "Meteorito",
                        "icon": "🗿",
                        "description": "Fragmento que sobrevive y llega al suelo",
                        "composition": "Roca o metal",
                        "size": "Gramos a toneladas"
                    }
                ]
            },
            {
                "type": "fact_cards",
                "title": "Datos Fascinantes",
                "facts": [
                    {"fact": "Hay más de 1 millón de asteroides conocidos", "icon": "🔢"},
                    {"fact": "El más grande es Ceres con 940km de diámetro", "icon": "👑"},
                    {"fact": "Se descubren ~30 nuevos asteroides cada día", "icon": "🔭"},
                    {"fact": "Algunos asteroides tienen sus propias lunas", "icon": "🌙"},
                    {"fact": "La masa total de asteroides es menor que la Luna", "icon": "⚖️"}
                ]
            },
            {
                "type": "interactive_scale",
                "title": "Escala de Tamaños",
                "items": [
                    {"name": "Chelyabinsk (2013)", "size_m": 20, "comparison": "Como un edificio de 6 pisos"},
                    {"name": "Tunguska (1908)", "size_m": 50, "comparison": "Como un campo de fútbol"},
                    {"name": "Meteor Crater", "size_m": 50, "comparison": "Como un avión comercial"},
                    {"name": "Apophis", "size_m": 370, "comparison": "Como la Torre Eiffel"},
                    {"name": "Bennu", "size_m": 500, "comparison": "Como el Empire State"},
                    {"name": "Chicxulub", "size_m": 10000, "comparison": "Como el Monte Everest"}
                ]
            }
        ],
        "quiz": [
            {
                "id": "q1_intro",
                "question": "¿Cuál es la diferencia principal entre un asteroide y un cometa?",
                "options": [
                    "El tamaño",
                    "La composición (roca vs hielo)",
                    "La velocidad",
                    "El color"
                ],
                "correct_answer": 1,
                "explanation": "Los asteroides son principalmente roca y metal, mientras que los cometas son mayormente hielo y polvo. Por eso los cometas desarrollan 'colas' cuando se acercan al Sol.",
                "points": 10
            },
            {
                "id": "q2_intro",
                "question": "¿Dónde se encuentran la mayoría de los asteroides?",
                "options": [
                    "Entre la Tierra y la Luna",
                    "Detrás del Sol",
                    "Entre Marte y Júpiter",
                    "Más allá de Plutón"
                ],
                "correct_answer": 2,
                "explanation": "El Cinturón de Asteroides está ubicado entre las órbitas de Marte y Júpiter, conteniendo millones de asteroides.",
                "points": 10
            },
            {
                "id": "q3_intro",
                "question": "¿Qué es un meteorito?",
                "options": [
                    "Una estrella fugaz",
                    "Un asteroide grande",
                    "Un fragmento que llega al suelo terrestre",
                    "Un cometa sin cola"
                ],
                "correct_answer": 2,
                "explanation": "Un meteorito es un fragmento de roca espacial que sobrevive el paso por la atmósfera y llega a la superficie de la Tierra.",
                "points": 10
            }
        ],
        "achievements": ["🎓 Estudiante de Asteroides", "🪨 Conocedor Espacial"]
    },
    {
        "id": "neo_explained",
        "title": "Objetos Cercanos a la Tierra (NEOs)",
        "description": "Descubre qué hace que un objeto sea 'cercano' a la Tierra y por qué los monitoreamos.",
        "difficulty": "beginner",
        "duration_minutes": 15,
        "icon": "🌍",
        "sections": [
            {
                "type": "text",
                "title": "¿Qué es un NEO?",
                "content": """
                    Un **NEO (Near-Earth Object)** es cualquier objeto del Sistema Solar cuya 
                    órbita lo acerca a menos de **1.3 Unidades Astronómicas (UA)** del Sol.
                    
                    Una UA es la distancia promedio entre la Tierra y el Sol: **150 millones de km**.
                    
                    Esto significa que un NEO puede acercarse a **menos de 45 millones de km** de la 
                    órbita terrestre.
                """
            },
            {
                "type": "classification",
                "title": "Clasificación de NEOs",
                "categories": [
                    {
                        "name": "Atiras",
                        "description": "Órbitas completamente dentro de la órbita terrestre",
                        "danger_level": "Bajo",
                        "count": "~30 conocidos"
                    },
                    {
                        "name": "Atens",
                        "description": "Órbitas mayormente dentro de la terrestre, pero la cruzan",
                        "danger_level": "Medio",
                        "count": "~2,000 conocidos"
                    },
                    {
                        "name": "Apollos",
                        "description": "Órbitas mayormente fuera de la terrestre, pero la cruzan",
                        "danger_level": "Alto",
                        "count": "~17,000 conocidos"
                    },
                    {
                        "name": "Amors",
                        "description": "Órbitas fuera de la terrestre, se acercan pero no cruzan",
                        "danger_level": "Bajo",
                        "count": "~10,000 conocidos"
                    }
                ]
            },
            {
                "type": "definition",
                "title": "¿Qué es un PHA?",
                "term": "Potentially Hazardous Asteroid (PHA)",
                "definition": "Un asteroide es 'Potencialmente Peligroso' si cumple DOS criterios:",
                "criteria": [
                    "Diámetro mayor a 140 metros",
                    "Puede acercarse a menos de 7.5 millones de km de la Tierra (0.05 UA)"
                ],
                "current_count": "Actualmente hay ~2,300 PHAs conocidos"
            },
            {
                "type": "timeline",
                "title": "Historia de la Detección de NEOs",
                "events": [
                    {"year": 1801, "event": "Se descubre el primer asteroide: Ceres"},
                    {"year": 1898, "event": "Se descubre el primer NEO: 433 Eros"},
                    {"year": 1932, "event": "Se descubre el primer Apollo: 1862 Apollo"},
                    {"year": 1998, "event": "NASA inicia programa Spaceguard"},
                    {"year": 2005, "event": "Congreso ordena detectar 90% de NEOs >140m"},
                    {"year": 2016, "event": "Se crea la Oficina de Defensa Planetaria"},
                    {"year": 2022, "event": "Misión DART desvía exitosamente un asteroide"}
                ]
            }
        ],
        "quiz": [
            {
                "id": "q1_neo",
                "question": "¿A qué distancia máxima del Sol debe estar un objeto para ser considerado NEO?",
                "options": [
                    "0.5 UA",
                    "1.0 UA",
                    "1.3 UA",
                    "2.0 UA"
                ],
                "correct_answer": 2,
                "explanation": "Un NEO debe tener su perihelio (punto más cercano al Sol) a menos de 1.3 UA del Sol.",
                "points": 10
            },
            {
                "id": "q2_neo",
                "question": "¿Qué tipo de NEO tiene las órbitas que cruzan la de la Tierra desde afuera?",
                "options": [
                    "Atiras",
                    "Atens", 
                    "Apollos",
                    "Amors"
                ],
                "correct_answer": 2,
                "explanation": "Los asteroides tipo Apollo tienen órbitas más grandes que la de la Tierra pero la cruzan, haciéndolos potencialmente peligrosos.",
                "points": 10
            }
        ],
        "achievements": ["🛡️ Vigilante Terrestre", "📊 Analista de Órbitas"]
    },
    {
        "id": "planetary_defense",
        "title": "Defensa Planetaria",
        "description": "Conoce las estrategias actuales para proteger la Tierra de impactos de asteroides.",
        "difficulty": "intermediate",
        "duration_minutes": 20,
        "icon": "🛡️",
        "sections": [
            {
                "type": "text",
                "title": "La Amenaza Real",
                "content": """
                    Cada día, aproximadamente **100 toneladas** de material espacial caen sobre 
                    la Tierra. La mayoría son partículas microscópicas que se queman en la atmósfera.
                    
                    Sin embargo, un impacto de un asteroide grande podría tener consecuencias 
                    devastadoras. Por eso, agencias espaciales de todo el mundo trabajan en 
                    **Defensa Planetaria**.
                    
                    La buena noticia: **No hay amenazas conocidas en los próximos 100 años** para 
                    asteroides mayores a 140 metros.
                """
            },
            {
                "type": "strategies",
                "title": "Estrategias de Defensa",
                "methods": [
                    {
                        "name": "Impacto Cinético",
                        "icon": "💥",
                        "description": "Golpear el asteroide con una nave espacial para cambiar su órbita",
                        "status": "Probado - Misión DART (2022)",
                        "effectiveness": "Funciona para asteroides pequeños-medianos con años de anticipación",
                        "example": "DART cambió la órbita de Dimorphos en 32 minutos"
                    },
                    {
                        "name": "Tractor Gravitacional",
                        "icon": "🛸",
                        "description": "Una nave cercana al asteroide usa su gravedad para desviarlo lentamente",
                        "status": "Teórico",
                        "effectiveness": "Requiere décadas de anticipación, muy preciso",
                        "example": "Propuesto para asteroides tipo Apophis"
                    },
                    {
                        "name": "Ablación Láser",
                        "icon": "🔦",
                        "description": "Vaporizar parte del asteroide para crear empuje",
                        "status": "En desarrollo",
                        "effectiveness": "Podría funcionar a distancia con satélites",
                        "example": "Proyecto DE-STAR"
                    },
                    {
                        "name": "Detonación Nuclear",
                        "icon": "☢️",
                        "description": "Explotar una bomba cerca del asteroide para vaporizarlo o desviarlo",
                        "status": "Último recurso",
                        "effectiveness": "Para asteroides grandes o con poco tiempo de aviso",
                        "example": "Solo si hay menos de 10 años de anticipación"
                    },
                    {
                        "name": "Pintura/Reflector",
                        "icon": "🎨",
                        "description": "Cambiar la reflectividad para que la presión solar lo desvíe",
                        "status": "Teórico",
                        "effectiveness": "Requiere muchos años",
                        "example": "Efecto Yarkovsky controlado"
                    }
                ]
            },
            {
                "type": "mission_highlight",
                "title": "Misión DART: Primer Éxito",
                "mission": {
                    "name": "Double Asteroid Redirection Test",
                    "agency": "NASA",
                    "date": "26 de septiembre de 2022",
                    "target": "Dimorphos (luna de Didymos)",
                    "result": "Cambió el período orbital de 11h 55m a 11h 23m (32 minutos)",
                    "significance": "Primera demostración de defensa planetaria",
                    "speed_impact": "22,530 km/h",
                    "facts": [
                        "La nave tenía el tamaño de un refrigerador",
                        "Dimorphos tiene 160 metros de diámetro",
                        "El cambio fue 25 veces mayor de lo esperado mínimo",
                        "Creó una cola de escombros de 10,000 km"
                    ]
                }
            },
            {
                "type": "organizations",
                "title": "Organizaciones de Defensa Planetaria",
                "orgs": [
                    {
                        "name": "NASA Planetary Defense Coordination Office",
                        "role": "Coordina esfuerzos de detección y respuesta en EE.UU.",
                        "founded": 2016
                    },
                    {
                        "name": "ESA Space Safety Programme",
                        "role": "Programa europeo de seguridad espacial",
                        "founded": 2019
                    },
                    {
                        "name": "IAWN (International Asteroid Warning Network)",
                        "role": "Red global de alertas de asteroides",
                        "founded": 2013
                    },
                    {
                        "name": "SMPAG (Space Mission Planning Advisory Group)",
                        "role": "Coordina misiones de defensa entre agencias",
                        "founded": 2014
                    }
                ]
            }
        ],
        "quiz": [
            {
                "id": "q1_defense",
                "question": "¿Qué método de defensa planetaria ya ha sido probado exitosamente?",
                "options": [
                    "Detonación nuclear",
                    "Tractor gravitacional",
                    "Impacto cinético (DART)",
                    "Ablación láser"
                ],
                "correct_answer": 2,
                "explanation": "La misión DART de NASA en 2022 demostró exitosamente que podemos cambiar la órbita de un asteroide golpeándolo con una nave espacial.",
                "points": 15
            },
            {
                "id": "q2_defense",
                "question": "¿Cuánto cambió DART el período orbital de Dimorphos?",
                "options": [
                    "5 minutos",
                    "15 minutos",
                    "32 minutos",
                    "2 horas"
                ],
                "correct_answer": 2,
                "explanation": "DART cambió el período orbital de Dimorphos de 11 horas 55 minutos a 11 horas 23 minutos, una diferencia de 32 minutos.",
                "points": 15
            }
        ],
        "achievements": ["🛡️ Defensor Planetario", "💥 Experto en DART"]
    },
    {
        "id": "impact_science",
        "title": "La Ciencia de los Impactos",
        "description": "Entiende la física detrás de los impactos y sus devastadores efectos.",
        "difficulty": "advanced",
        "duration_minutes": 25,
        "icon": "💥",
        "sections": [
            {
                "type": "physics",
                "title": "Física del Impacto",
                "content": """
                    La energía de un impacto se calcula con la fórmula de energía cinética:
                    
                    **E = ½mv²**
                    
                    Donde:
                    - **E** = Energía (Joules)
                    - **m** = Masa del asteroide (kg)
                    - **v** = Velocidad de impacto (m/s)
                    
                    La velocidad promedio de impacto es **17 km/s** (¡61,200 km/h!).
                    
                    Esto significa que un asteroide de solo 50 metros puede liberar energía 
                    equivalente a **varias bombas nucleares**.
                """,
                "formula": "E = ½ × (4/3 × π × r³ × ρ) × v²",
                "variables": {
                    "r": "Radio del asteroide",
                    "ρ": "Densidad del material",
                    "v": "Velocidad de impacto"
                }
            },
            {
                "type": "effects_cascade",
                "title": "Cascada de Efectos",
                "stages": [
                    {
                        "time": "0 segundos",
                        "name": "Contacto",
                        "description": "El asteroide impacta a velocidades hipersónicas. La presión instantánea es de millones de atmósferas."
                    },
                    {
                        "time": "0.1 segundos",
                        "name": "Vaporización",
                        "description": "El asteroide y la roca debajo se vaporizan instantáneamente por el calor extremo."
                    },
                    {
                        "time": "1 segundo",
                        "name": "Bola de Fuego",
                        "description": "Una bola de plasma más caliente que el Sol se expande destruyendo todo en kilómetros."
                    },
                    {
                        "time": "10 segundos",
                        "name": "Eyección de Material",
                        "description": "Toneladas de roca son lanzadas al aire y al espacio, algunas reentrarán causando más incendios."
                    },
                    {
                        "time": "1 minuto",
                        "name": "Onda de Choque",
                        "description": "Una pared de aire comprimido viaja a velocidades supersónicas devastando todo."
                    },
                    {
                        "time": "10 minutos",
                        "name": "Terremotos",
                        "description": "Ondas sísmicas recorren el planeta. Pueden sentirse a miles de kilómetros."
                    },
                    {
                        "time": "1 hora",
                        "name": "Tsunamis",
                        "description": "Si cayó en el océano, olas de cientos de metros arrasan las costas."
                    },
                    {
                        "time": "Días",
                        "name": "Incendios Globales",
                        "description": "Material caliente reentrado inicia incendios forestales en continentes."
                    },
                    {
                        "time": "Meses",
                        "name": "Invierno de Impacto",
                        "description": "Polvo y hollín bloquean el Sol, temperaturas caen dramáticamente."
                    },
                    {
                        "time": "Años",
                        "name": "Colapso Ecosistémico",
                        "description": "Sin luz solar, plantas mueren, cadena alimenticia colapsa."
                    }
                ]
            },
            {
                "type": "scale_comparison",
                "title": "Escala de Devastación",
                "levels": [
                    {
                        "diameter_m": 10,
                        "energy_mt": 0.01,
                        "effect": "Bola de fuego brillante, posible onda de choque menor",
                        "frequency": "Mensual"
                    },
                    {
                        "diameter_m": 25,
                        "energy_mt": 0.5,
                        "effect": "Daño a edificios, heridos (ej: Chelyabinsk)",
                        "frequency": "Cada 50-100 años"
                    },
                    {
                        "diameter_m": 50,
                        "energy_mt": 10,
                        "effect": "Destrucción de ciudad pequeña (ej: Tunguska)",
                        "frequency": "Cada 500-1000 años"
                    },
                    {
                        "diameter_m": 140,
                        "energy_mt": 100,
                        "effect": "Destrucción regional, millones de víctimas potenciales",
                        "frequency": "Cada 10,000 años"
                    },
                    {
                        "diameter_m": 300,
                        "energy_mt": 1000,
                        "effect": "Destrucción continental, efectos climáticos",
                        "frequency": "Cada 70,000 años"
                    },
                    {
                        "diameter_m": 1000,
                        "energy_mt": 100000,
                        "effect": "Extinción parcial, invierno nuclear",
                        "frequency": "Cada millón de años"
                    },
                    {
                        "diameter_m": 10000,
                        "energy_mt": 100000000000,
                        "effect": "Extinción masiva (ej: Chicxulub)",
                        "frequency": "Cada 100 millones de años"
                    }
                ]
            }
        ],
        "quiz": [
            {
                "id": "q1_science",
                "question": "¿Cuál es la velocidad promedio de impacto de un asteroide?",
                "options": [
                    "5 km/s",
                    "17 km/s",
                    "50 km/s",
                    "100 km/s"
                ],
                "correct_answer": 1,
                "explanation": "La velocidad promedio de impacto es de aproximadamente 17 km/s (61,200 km/h), aunque puede variar de 11 a 72 km/s.",
                "points": 20
            },
            {
                "id": "q2_science",
                "question": "¿Por qué el factor v² en E=½mv² es tan importante?",
                "options": [
                    "Porque la velocidad es constante",
                    "Porque duplicar la velocidad cuadruplica la energía",
                    "Porque la masa es más importante",
                    "Porque v² es siempre menor que m"
                ],
                "correct_answer": 1,
                "explanation": "El factor v² significa que la energía aumenta con el cuadrado de la velocidad. Duplicar la velocidad = 4x energía. Triplicarla = 9x energía.",
                "points": 20
            }
        ],
        "achievements": ["🔬 Científico de Impactos", "💡 Físico Espacial"]
    }
]


class EducationalModulesService:
    """Servicio para gestionar módulos educativos."""
    
    def __init__(self):
        self.modules = [
            EducationalModule(**module) for module in EDUCATIONAL_MODULES
        ]
    
    def get_all_modules(self) -> List[EducationalModule]:
        """Retorna todos los módulos."""
        return self.modules
    
    def get_module_by_id(self, module_id: str) -> Optional[EducationalModule]:
        """Busca un módulo por ID."""
        for module in self.modules:
            if module.id == module_id:
                return module
        return None
    
    def get_modules_by_difficulty(self, difficulty: DifficultyLevel) -> List[EducationalModule]:
        """Filtra módulos por dificultad."""
        return [m for m in self.modules if m.difficulty == difficulty]
    
    def check_quiz_answers(
        self,
        module_id: str,
        answers: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Verifica respuestas de quiz.
        
        Args:
            module_id: ID del módulo
            answers: Dict de {question_id: answer_index}
            
        Returns:
            Resultados del quiz
        """
        module = self.get_module_by_id(module_id)
        if not module or not module.quiz:
            return {"error": "Módulo o quiz no encontrado"}
        
        results = {
            "total_questions": len(module.quiz),
            "correct_answers": 0,
            "total_points": 0,
            "max_points": sum(q.points for q in module.quiz),
            "details": []
        }
        
        for question in module.quiz:
            user_answer = answers.get(question.id)
            is_correct = user_answer == question.correct_answer
            
            if is_correct:
                results["correct_answers"] += 1
                results["total_points"] += question.points
            
            results["details"].append({
                "question_id": question.id,
                "correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "points_earned": question.points if is_correct else 0
            })
        
        # Calcular porcentaje y logros
        percentage = (results["total_points"] / results["max_points"]) * 100
        results["percentage"] = round(percentage, 1)
        
        if percentage >= 80:
            results["achievements_earned"] = module.achievements
        elif percentage >= 50:
            results["achievements_earned"] = [module.achievements[0]] if module.achievements else []
        else:
            results["achievements_earned"] = []
        
        return results


# Singleton
education_service = EducationalModulesService()
