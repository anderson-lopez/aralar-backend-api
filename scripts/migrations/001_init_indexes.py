def up(db):
    # índices base
    db["users"].create_index("email", unique=True)
    db["roles"].create_index("name", unique=True)
    db["permissions"].create_index("name", unique=True)
