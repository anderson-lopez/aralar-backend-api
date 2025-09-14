# scripts/migrations/004_availability_indexes.py
def up(db):
    db["menus"].create_index([("availability.days_of_week", 1)])
    db["menus"].create_index(
        [
            ("availability.date_ranges.start", 1),
            ("availability.date_ranges.end", 1),
        ]
    )
    # si tu locale principal es es-ES, acelera filtros publicados:
    db["menus"].create_index([("publish.es-ES.status", 1)])
    db["menu_templates"].create_index([("slug", 1), ("version", 1)], unique=True)
    db["menu_templates"].create_index([("status", 1)])
    db["menu_templates"].create_index([("tenant_id", 1)])
