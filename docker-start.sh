#!/bin/bash

echo "========================================"
echo "   Iniciando Aralar API con Docker"
echo "========================================"

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "[INFO] Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo "[IMPORTANTE] Por favor, edita el archivo .env con tus configuraciones antes de continuar."
    echo "[IMPORTANTE] Especialmente SECRET_KEY y JWT_SECRET_KEY para producción."
    read -p "Presiona Enter para continuar..."
fi

echo "[INFO] Construyendo e iniciando contenedores..."
docker-compose up --build -d

echo "[INFO] Esperando que los servicios estén listos..."
sleep 15

echo "[INFO] Verificando estado de los contenedores..."
docker-compose ps

echo "[INFO] Ejecutando migraciones y seed inicial..."
docker-compose exec api python scripts/migrate.py
docker-compose exec api python scripts/seed.py

# Solo sincroniza si la colección está vacía: la primera vez trae las reseñas y en
# los siguientes arranques no vuelve a consultar a Google.
# Si falla (sin URL configurada, Google caído) NO aborta el arranque.
echo "[INFO] Comprobando reseñas de Google..."
if ! docker-compose exec api python scripts/sync_google_reviews.py --if-empty; then
    echo "[AVISO] No se pudieron sincronizar las reseñas. La API arranca igualmente."
    echo "[AVISO] Revisa GOOGLE_REVIEWS_PROVIDER y GOOGLE_MAPS_PLACE_URL en el .env"
fi

echo "========================================"
echo "   Aralar API iniciada correctamente!"
echo "========================================"
echo ""
echo "API disponible en: http://localhost:8000"
echo "Documentación Swagger: http://localhost:8000/api/docs/swagger-ui"
echo "MongoDB disponible en: localhost:27017"
echo ""
echo "Para ver logs: docker-compose logs -f"
echo "Para detener: docker-compose down"
echo "========================================"
