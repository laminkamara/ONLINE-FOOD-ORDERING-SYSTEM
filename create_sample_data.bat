@echo off
echo ============================================
echo yoni Fast Food Restaurant - Sample Data Setup
echo ============================================
echo.

echo Creating sample data...
python manage.py shell < create_sample_data.py

echo.
echo ============================================
echo Sample data created successfully!
echo ============================================
echo.
pause
