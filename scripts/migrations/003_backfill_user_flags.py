def up(db):
    db["users"].update_many(
        {"permissions_allow": {"$exists": False}}, {"$set": {"permissions_allow": []}}
    )
    db["users"].update_many(
        {"permissions_deny": {"$exists": False}}, {"$set": {"permissions_deny": []}}
    )
    db["users"].update_many({"perm_version": {"$exists": False}}, {"$set": {"perm_version": 1}})
