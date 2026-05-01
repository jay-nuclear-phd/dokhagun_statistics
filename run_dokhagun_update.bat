@echo off
chcp 65001 > nul

cd /d "C:\Users\staro\OneDrive - The University of Texas at Austin\Github_Projects\dokhagun_statistics"

echo ========================================
echo Dokhagun statistics update started
echo %date% %time%
echo ========================================

conda run -n venv python "C:\Users\staro\OneDrive - The University of Texas at Austin\Github_Projects\dokhagun_statistics\scripts\dokhagun.py"

if errorlevel 1 (
    echo Python script failed.
    pause
    exit /b 1
)

echo Python script completed.

git add .

git diff --cached --quiet
if %errorlevel%==0 (
    echo No changes to commit.
) else (
    git commit -m "data updated"

    if errorlevel 1 (
        echo Git commit failed.
        pause
        exit /b 1
    )

    git push

    if errorlevel 1 (
        echo Git push failed.
        pause
        exit /b 1
    )
)

echo ========================================
echo Dokhagun statistics update finished
echo %date% %time%
echo ========================================

exit /b 0