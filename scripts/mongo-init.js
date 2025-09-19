// Script de inicialización para MongoDB en Docker
// Este script se ejecuta automáticamente cuando se crea el contenedor

// Crear la base de datos aralar si no existe
db = db.getSiblingDB('aralar');

// Crear índices básicos para optimizar consultas
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "tenant_id": 1 });
db.users.createIndex({ "roles": 1 });

// Crear colecciones básicas
db.createCollection("users");
db.createCollection("roles");
db.createCollection("permissions");
db.createCollection("menu_templates");
db.createCollection("menus");

print("MongoDB inicializado correctamente para Aralar API");
