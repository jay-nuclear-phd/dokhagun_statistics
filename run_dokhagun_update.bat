@echo off
chcp 65001 > nul

set PROJECT_DIR=C:\Users\staro\OneDrive - The University of Texas at Austin\Github_Projects\dokhagun_statistics
set PYTHON_EXE=C:\Users\staro\miniconda3\envs\venv\python.exe
set SCRIPT_PATH=C:\Users\staro\OneDrive - The University of Texas at Austin\Github_Projects\dokhagun_statistics\scripts\dokhagun.py

cd /d "%PROJECT_DIR%"

echo ========================================
echo Dokhagun update started
echo %date% %time%
echo Current directory:
cd
echo ========================================

echo.
echo [1/5] Running Python crawler...
"%PYTHON_EXE%" "%SCRIPT_PATH%"

if errorlevel 1 (
    echo.
    echo Python script failed.
    pause
    exit /b 1
)

echo.
echo [2/5] Python script completed.

echo.
echo [3/5] Git status before add:
git status --short

echo.
echo [4/5] Running git add...
git add .

echo.
echo Git status after add:
git status --short

echo.
echo Checking if there are staged changes...
git diff --cached --quiet

if %errorlevel%==0 (
    echo.
    echo No changes to commit.
) else (
    echo.
    echo [5/5] Running git commit...
    git commit -m "data updated"

    if errorlevel 1 (
        echo.
        echo Git commit failed.
        pause
        exit /b 1
    )

    echo.
    echo Running git push...
    git push

    if errorlevel 1 (
        echo.
        echo Git push failed.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Dokhagun update finished
echo %date% %time%
echo ========================================

pause
exit /b 0