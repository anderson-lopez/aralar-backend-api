# scripts/migrations/004_availability_indexes.py
def up(db):
    # Índices de availability para menus
    db["menus"].create_index([("availability.days_of_week", 1)])
    db["menus"].create_index(
        [
            ("availability.date_ranges.start", 1),
            ("availability.date_ranges.end", 1),
        ]
    )
    # si tu locale principal es es-ES, acelera filtros publicados:
    db["menus"].create_index([("publish.es-ES.status", 1)])
    
    # Índices adicionales para menus
    db["menus"].create_index([("tenant_id", 1)])
    db["menus"].create_index([("template_slug", 1), ("template_version", 1)])
    db["menus"].create_index([("status", 1)])
    
    # Índices para menu_templates
    db["menu_templates"].create_index([("slug", 1), ("version", 1)], unique=True)
    db["menu_templates"].create_index([("status", 1)])
    db["menu_templates"].create_index([("tenant_id", 1)])
    
    print("[migrate] availability and menu indexes OK")
