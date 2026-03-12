@echo off
echo ========================================
echo   BOOKSTORE MICROSERVICES
echo ========================================
echo.
echo Starting all services...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak

echo.
echo Running migrations...
docker exec bookstoremicro-api-gateway-1 python manage.py migrate
docker exec bookstoremicro-customer-service-1 python manage.py migrate
docker exec bookstoremicro-book-service-1 python manage.py migrate
docker exec bookstoremicro-cart-service-1 python manage.py migrate
docker exec bookstoremicro-order-service-1 python manage.py migrate
docker exec bookstoremicro-payment-service-1 python manage.py migrate
docker exec bookstoremicro-shipping-service-1 python manage.py migrate
docker exec bookstoremicro-comment-rate-service-1 python manage.py migrate

echo.
echo ========================================
echo   ALL SERVICES STARTED!
echo ========================================
echo.
echo Access the application at: http://localhost:8000
echo.
echo Press any key to open browser...
pause
start http://localhost:8000
