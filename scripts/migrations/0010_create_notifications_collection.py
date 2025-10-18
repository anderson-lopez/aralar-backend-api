# aralar/scripts/migrations/007_create_notifications_collection.py

from datetime import datetime, timedelta

def up(db):
    """Crear colección de notificaciones con índices"""
    
    # Crear la colección
    notifications_collection = db["notifications"]
    
    # Crear índices para optimizar consultas
    notifications_collection.create_index("is_active")
    notifications_collection.create_index("scheduling.start_date")
    notifications_collection.create_index("scheduling.end_date")
    notifications_collection.create_index("scheduling.days_of_week")
    notifications_collection.create_index("display.location")
    notifications_collection.create_index("priority")
    notifications_collection.create_index("name", unique=True)  # Nombre único
    notifications_collection.create_index([("is_active", 1), ("scheduling.start_date", 1), ("scheduling.end_date", 1)])
    notifications_collection.create_index([("display.location", 1), ("priority", -1)])  # Para consultas por ubicación ordenadas por prioridad
    
    # Insertar datos de ejemplo (opcional)
    sample_notifications = [
        {
            "name": "Promoción San Valentín",
            "content": "<strong>¡Oferta especial!</strong> Cena romántica para dos por solo €45",
            "is_active": True,
            "priority": 10,
            "scheduling": {
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=30),
                "days_of_week": ["FRI", "SAT", "SUN"],
                "time_start": "18:00",
                "time_end": "23:30"
            },
            "display": {
                "location": "hero-section",
                "type": "banner",
                "style": {
                    "background_color": "#FF69B4",
                    "text_color": "#FFFFFF",
                    "custom_css_class": "valentine-promo"
                }
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Aviso de Mantenimiento",
            "content": "⚠️ Servicio limitado mañana por mantenimiento de cocina. Solo disponible menú frío.",
            "is_active": True,
            "priority": 5,
            "scheduling": {
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=1),
                "days_of_week": [],
                "time_start": None,
                "time_end": None
            },
            "display": {
                "location": "top-bar",
                "type": "banner",
                "style": {
                    "background_color": "#FFA500",
                    "text_color": "#000000",
                    "custom_css_class": None
                }
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Solo insertar si no existen notificaciones
    existing_count = notifications_collection.count_documents({})
    if existing_count == 0:
        notifications_collection.insert_many(sample_notifications)
        print("OK: Coleccion de notificaciones creada con exito")
    else:
        print("OK: Coleccion de notificaciones ya existe con", existing_count, "documentos")

def down(db):
    """Eliminar colección de notificaciones"""
    db.drop_collection("notifications")
    print("OK: Coleccion de notificaciones eliminada")