from bson import ObjectId
from typing import Optional, Dict, Any, List


def to_object_id(id_or_str):
    return id_or_str if isinstance(id_or_str, ObjectId) else ObjectId(id_or_str)


class BaseRepository:
    """Base repository class for MongoDB operations"""
    
    def __init__(self, collection_name: str):
        # Este metodo sera sobrescrito por las clases hijas
        # que pasaran la instancia de db directamente
        self.collection = None
    
    def find_by_id(self, id_or_str: str) -> Optional[Dict[str, Any]]:
        """Find document by ID"""
        try:
            obj_id = to_object_id(id_or_str)
            return self.collection.find_one({"_id": obj_id})
        except Exception:
            return None
    
    def find_all(self, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find all documents with optional filter"""
        if filter_dict is None:
            filter_dict = {}
        return list(self.collection.find(filter_dict))
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert one document and return its ID as string"""
        result = self.collection.insert_one(document)
        return str(result.inserted_id)
    
    def update_one(self, id_or_str: str, update_dict: Dict[str, Any]) -> bool:
        """Update one document by ID"""
        try:
            obj_id = to_object_id(id_or_str)
            result = self.collection.update_one({"_id": obj_id}, {"$set": update_dict})
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_one(self, id_or_str: str) -> bool:
        """Delete one document by ID"""
        try:
            obj_id = to_object_id(id_or_str)
            result = self.collection.delete_one({"_id": obj_id})
            return result.deleted_count > 0
        except Exception:
            return False
