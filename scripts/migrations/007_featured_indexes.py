# scripts/migrations/007_featured_indexes.py
def up(db):
    """
    Migración para agregar índices de menus destacados (featured).
    
    Estos índices optimizan las consultas para:
    - Filtrar menus destacados (featured=True)
    - Ordenar por featured_order
    - Consultas combinadas de featured + availability + publish status
    """
    
    # Índice simple para featured
    db["menus"].create_index([("featured", 1)])
    
    # Índice compuesto para featured_order (optimiza ordenamiento)
    db["menus"].create_index([("featured_order", 1)])
    
    # Índice compuesto para consultas de menus destacados disponibles
    # Este índice optimiza la query principal de list_featured_by_day()
    db["menus"].create_index([
        ("featured", 1),
        ("status", 1),
        ("availability.days_of_week", 1),
        ("featured_order", 1)
    ])
    
    # Índice adicional para consultas con locale específico
    # Útil para consultas que filtran por publish status de un locale
    db["menus"].create_index([
        ("featured", 1),
        ("status", 1),
        ("publish.es-ES.status", 1),  # Locale principal
        ("featured_order", 1)
    ])
    
    print("[migrate] featured menu indexes created successfully")


def down(db):
    """
    Rollback: elimina los índices de featured menus
    """
    try:
        # Eliminar índices en orden inverso
        db["menus"].drop_index([
            ("featured", 1),
            ("status", 1),
            ("publish.es-ES.status", 1),
            ("featured_order", 1)
        ])
        
        db["menus"].drop_index([
            ("featured", 1),
            ("status", 1),
            ("availability.days_of_week", 1),
            ("featured_order", 1)
        ])
        
        db["menus"].drop_index([("featured_order", 1)])
        db["menus"].drop_index([("featured", 1)])
        
        print("[rollback] featured menu indexes dropped successfully")
    except Exception as e:
        print(f"[rollback] Warning: Some indexes may not exist: {e}")
