@echo off
echo ============================================
echo Online Food Ordering System - Setup Script
echo ============================================
echo.

echo Step 1: Installing dependencies...
pip install -r requirements.txt
echo.

echo Step 2: Creating database migrations...
python manage.py makemigrations
echo.

echo Step 3: Applying migrations...
python manage.py migrate
echo.

echo ============================================
echo Setup complete!
echo ============================================
echo.
echo Next steps:
echo 1. Create admin user: python manage.py createsuperuser
echo 2. Run server: python manage.py runserver
echo 3. Visit: http://127.0.0.1:8000
echo 4. Admin panel: http://127.0.0.1:8000/admin
echo.
pause
