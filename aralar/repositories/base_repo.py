from bson import ObjectId


def to_object_id(id_or_str):
    return id_or_str if isinstance(id_or_str, ObjectId) else ObjectId(id_or_str)
