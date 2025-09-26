from aralar.catalog.role_catalog import apply_catalog


def up(db):
    """Synchronize roles and permissions with the centralized catalog.
    Safe to run multiple times (idempotent).
    """
    apply_catalog(db)
