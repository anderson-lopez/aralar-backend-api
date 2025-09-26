def up(db):
    col = db["translations_cache"]
    col.create_index([("hash", 1)], unique=True, name="uniq_hash")
    col.create_index([("created_at", 1)], name="created_at_idx")
    print("[migrate] translations_cache indexes OK")
