@echo off
echo ========================================
echo    Iniciando Aralar API con Docker
echo ========================================

REM Verificar si existe el archivo .env
if not exist .env (
    echo [INFO] Creando archivo .env desde .env.example...
    copy .env.example .env
    echo [IMPORTANTE] Por favor, edita el archivo .env con tus configuraciones antes de continuar.
    echo [IMPORTANTE] Especialmente SECRET_KEY y JWT_SECRET_KEY para produccion.
    pause
)

echo [INFO] Construyendo e iniciando contenedores...
docker-compose up --build -d

echo [INFO] Esperando que los servicios esten listos...
timeout /t 10 /nobreak > nul

echo [INFO] Verificando estado de los contenedores...
docker-compose ps

echo [INFO] Ejecutando migraciones y seed inicial...
docker-compose exec api python scripts/migrate.py
docker-compose exec api python scripts/seed.py

REM Solo sincroniza si la coleccion esta vacia: la primera vez trae las resenas
REM y en los siguientes arranques no vuelve a consultar a Google.
REM Si falla (sin URL configurada, Google caido) NO aborta el arranque.
echo [INFO] Comprobando resenas de Google...
docker-compose exec api python scripts/sync_google_reviews.py --if-empty
if errorlevel 1 (
    echo [AVISO] No se pudieron sincronizar las resenas. La API arranca igualmente.
    echo [AVISO] Revisa GOOGLE_REVIEWS_PROVIDER y GOOGLE_MAPS_PLACE_URL en el .env
)

echo ========================================
echo    Aralar API iniciada correctamente!
echo ========================================
echo.
echo API disponible en: http://localhost:8000
echo Documentacion Swagger: http://localhost:8000/api/docs/swagger-ui
echo MongoDB disponible en: localhost:27017
echo.
echo Para ver logs: docker-compose logs -f
echo Para detener: docker-compose down
echo ========================================

pause
