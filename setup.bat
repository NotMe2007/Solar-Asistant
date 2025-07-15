@echo off
echo Solar Assistant Bot
echo ==================

echo Setting up the bot...
python setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Setup completed successfully!
    echo.
    echo Do you want to run a test capture now? (y/n)
    set /p choice=
    if /i "%choice%"=="y" (
        echo Running test capture...
        python solar_assistant_bot.py --test
    )
) else (
    echo.
    echo Setup failed. Please check the errors above.
)

pause
