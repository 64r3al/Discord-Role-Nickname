@echo off
chcp 65001 >nul
color 09

echo Starting Discord Bot Setup...

REM Install requirements first
echo Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements!
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment!
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Display custom message with large text
echo.
echo ===================================================
echo.
echo ──────▐▀▄─────────▄▀▌
echo ──────▐▓░▀▄▀▀▀▀▀▄▀░▓▌
echo ──────▐░▓░▄▀░░░▀▄░▓░▌
echo ───────█░░▌█▐░▌█▐░░█
echo ────▄▄▄▐▀░░░▀█▀░░░▀▌▄▄▄
echo ───█▐▐▐▌▀▄░▀▄▀▄▀░▄▀▐▌▌▌█
echo ━━▏┓┏╭╮┳╮┳╮┓┏▕━━
echo ━━▏┣┫┣┫┣╯┣╯╰┫▕━━
echo ━━▏┛┛┛┛┻╱┻╱╰╯▕━━
echo ┈┏┳┳┓┈┈┈┏┓
echo ┈┃┃┃┣━┳━┫┃╭━┓┈┈┈
echo ┈┃┃┃┃┗┃┗┃┗╯╭╋┓┈┈
echo ┈┃┈┈┃╰┫╰┫┏╮╰┫┃┈┈
echo ┈╰━━╋━┻┳┻┻╋━┛┃┈┈
echo ┈┈┈┈┃┗┛┃┏╮┃╭┓┃┈┈
echo ┈┈┈┈┃╰━┫┃┃┃╰┛┃┈┈
echo ┈┈┈┈╰━━┻┛┗┻━━┛┈┈
echo.
echo ===================================================

echo.
echo THIS BOT MADE BY IVX
echo BUY ME COFFEE
echo https://guns.lol/ivx.1x
echo.
echo Powered by ERA
echo.
echo ===================================================
echo.

REM Wait for 10 seconds with countdown
for /L %%i in (10,-1,1) do (
    echo Starting bot in %%i seconds...
    timeout /t 1 /nobreak >nul
)

REM Open the link in default browser
start https://guns.lol/ivx.1x

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file...
    (
        echo # Discord Bot Configuration
        echo DISCORD_TOKEN=your_discord_bot_token_here
        echo LOG_CHANNEL_ID=your_log_channel_id_here
        echo.
        echo # Bot Settings
        echo COMMAND_PREFIX=!
        echo AUTO_RESTORE=true
        echo ADMIN_ROLE_ID=your_admin_role_id_here
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
    ) > .env
    echo Please edit the .env file with your bot token and other settings!
    pause
)

REM Create necessary directories
if not exist "database" mkdir database
if not exist "logs" mkdir logs

REM Start the bot
echo Starting the bot...
python main.py

REM If the bot crashes, pause to see the error
pause