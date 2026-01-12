@echo off
echo ==========================================
echo RESET DATABASE VA MIGRATIONS
echo ==========================================

:: 1. Xoa database
echo.
echo [1/8] Xoa database...
if exist db.sqlite3 del /f db.sqlite3
if exist db.sqlite3-journal del /f db.sqlite3-journal
echo OK - Da xoa database

:: 2. Xoa cache Python
echo.
echo [2/8] Xoa cache Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /f "%%f"
echo OK - Da xoa cache

:: 3. Xoa tat ca migrations (tru __init__.py)
echo.
echo [3/8] Xoa migrations cu...
cd app_quan_ly\migrations
for %%f in (*.py) do (
    if not "%%f"=="__init__.py" del /f "%%f"
)
cd ..\..
echo OK - Da xoa migrations cu

:: 4. Xoa file 0002 neu da copy nham
echo.
echo [4/8] Kiem tra file 0002...
if exist app_quan_ly\migrations\0002_create_groups_and_permissions.py (
    del /f app_quan_ly\migrations\0002_create_groups_and_permissions.py
    echo OK - Da xoa file 0002 cu
) else (
    echo OK - Khong co file 0002
)

:: 5. Tao migration moi tu models
echo.
echo [5/8] Tao migrations moi...
python manage.py makemigrations app_quan_ly
if errorlevel 1 (
    echo ERROR - Loi khi tao migrations!
    pause
    exit /b 1
)
echo OK - Da tao migrations moi

:: 6. Migrate lan dau (tao tables)
echo.
echo [6/8] Migrate lan dau...
python manage.py migrate
if errorlevel 1 (
    echo ERROR - Loi khi migrate!
    pause
    exit /b 1
)
echo OK - Da tao tables

:: 7. Copy migration phan quyen
echo.
echo [7/8] Copy migration phan quyen...
copy /y 0002_create_groups_and_permissions.py app_quan_ly\migrations\
if errorlevel 1 (
    echo ERROR - Khong tim thay file 0002_create_groups_and_permissions.py
    echo Dam bao file nay nam cung thu muc voi script
    pause
    exit /b 1
)
echo OK - Da copy migration phan quyen

:: 8. Migrate lan 2 (tao groups)
echo.
echo [8/8] Migrate phan quyen...
python manage.py migrate
if errorlevel 1 (
    echo ERROR - Loi khi migrate phan quyen!
    pause
    exit /b 1
)

:: 9. Copy decorators
echo.
echo [Bo sung] Copy decorators...
copy /y decorators.py app_quan_ly\
echo OK - Da copy decorators.py

:: 10. Tao user mau
echo.
echo [Bo sung] Tao user mau...
if not exist app_quan_ly\management mkdir app_quan_ly\management
if not exist app_quan_ly\management\commands mkdir app_quan_ly\management\commands
if not exist app_quan_ly\management\__init__.py type nul > app_quan_ly\management\__init__.py
if not exist app_quan_ly\management\commands\__init__.py type nul > app_quan_ly\management\commands\__init__.py
copy /y create_sample_users.py app_quan_ly\management\commands\
python manage.py create_sample_users

echo.
echo ==========================================
echo SUCCESS - HOAN TAT!
echo ==========================================
echo.
echo Ban co the login voi:
echo   staff1    / staff123    (Nhan vien)
echo   manager1  / manager123  (Quan ly)
echo   admin1    / admin123    (Admin)
echo.
echo ==========================================
pause
