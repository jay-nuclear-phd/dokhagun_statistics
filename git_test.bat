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