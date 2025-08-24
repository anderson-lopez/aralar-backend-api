from functools import wraps
from bson import ObjectId
from bson.errors import InvalidId
from flask import jsonify


def validate_object_id(*param_names):
    """
    Decorador para validar que los parámetros especificados sean ObjectIds válidos.
    
    Args:
        *param_names: Nombres de los parámetros a validar
    
    Usage:
        @validate_object_id('user_id')
        def get_user(user_id):
            # user_id ya está validado aquí
            pass
            
        @validate_object_id('user_id', 'role_id')
        def update_user_role(user_id, role_id):
            # ambos parámetros están validados
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener los nombres de los parámetros de la función
            import inspect
            sig = inspect.signature(func)
            param_list = list(sig.parameters.keys())
            
            # Crear un diccionario con los valores de los parámetros
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validar cada parámetro especificado
            for param_name in param_names:
                if param_name in bound_args.arguments:
                    param_value = bound_args.arguments[param_name]
                    try:
                        ObjectId(param_value)
                    except InvalidId:
                        return jsonify({"error": f"Invalid {param_name} format"}), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
