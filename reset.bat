@echo off
echo ==========================================
echo RESET DATABASE VA MIGRATIONS (POSTGRESQL)
echo ==========================================

:: 0. Kich hoat moi truong ao (QUAN TRONG NHAT)
if exist venv\Scripts\activate (
    echo [0/8] Dang kich hoat moi truong ao venv...
    call venv\Scripts\activate
) else (
    echo ERROR - Khong tim thay thu muc venv tai D:\invoice_application\venv
    pause
    exit /b 1
)

:: 1. Xoa cache Python
echo.
echo [1/8] Xoa cache Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /f "%%f"
echo OK - Da xoa cache

:: 2. Xoa tat ca migrations (tru __init__.py)
echo.
echo [2/8] Xoa migrations cu...
if exist app_quan_ly\migrations (
    cd app_quan_ly\migrations
    for %%f in (*.py) do (
        if not "%%f"=="__init__.py" del /f "%%f"
    )
    cd ..\..
    echo OK - Da xoa migrations cu
)

:: 3. Xoa file 0002 neu da copy nham
echo.
echo [3/8] Kiem tra file 0002...
if exist app_quan_ly\migrations\0002_create_groups_and_permissions.py (
    del /f app_quan_ly\migrations\0002_create_groups_and_permissions.py
    echo OK - Da xoa file 0002 cu
)

:: 4. Tao migration moi tu models
echo.
echo [4/8] Tao migrations moi...
python manage.py makemigrations app_quan_ly
if errorlevel 1 (
    echo ERROR - Loi khi tao migrations!
    pause
    exit /b 1
)
echo OK - Da tao migrations moi

:: 5. Migrate lan dau (PostgreSQL phai dang chay)
echo.
echo [5/8] Migrate lan dau...
python manage.py migrate
if errorlevel 1 (
    echo ERROR - Loi khi migrate! Hay kiem tra Postgres Service da START chua.
    pause
    exit /b 1
)
echo OK - Da tao tables

:: 6. Copy migration phan quyen
echo.
echo [6/8] Copy migration phan quyen...
if exist 0002_create_groups_and_permissions.py (
    copy /y 0002_create_groups_and_permissions.py app_quan_ly\migrations\
    echo OK - Da copy migration phan quyen
) else (
    echo WARNING - Khong tim thay file 0002 de copy.
)

:: 7. Migrate lan 2 (tao groups)
echo.
echo [7/8] Migrate phan quyen...
python manage.py migrate
if errorlevel 1 (
    echo ERROR - Loi khi migrate phan quyen!
    pause
    exit /b 1
)

:: 8. Tao user mau
echo.
echo [Bo sung] Tao user mau...
if exist create_sample_users.py (
    if not exist app_quan_ly\management\commands mkdir app_quan_ly\management\commands
    type nul > app_quan_ly\management\__init__.py
    type nul > app_quan_ly\management\commands\__init__.py
    copy /y create_sample_users.py app_quan_ly\management\commands\
    python manage.py create_sample_users
)

echo.
echo ==========================================
echo SUCCESS - HOAN TAT!
echo ==========================================
pause