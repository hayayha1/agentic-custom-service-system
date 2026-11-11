@echo off
chcp 65001 >nul
setlocal
title 知枢 SaaS - 智能客服与知识治理
cd /d "%~dp0"
set "PYTHONPATH=."
set "PY_CMD="

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
    goto :RUN
)
if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0venv\Scripts\python.exe"
    goto :RUN
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :RUN
)
if exist "D:\python解释器\python.exe" (
    set "PY_CMD=D:\python解释器\python.exe"
    goto :RUN
)
echo [错误] 未找到 Python。请安装 Python 3.11 或更高版本，并按 README 安装依赖。
pause
exit /b 1

:RUN
echo ========================================================================
echo   知枢 SaaS - 智能客服与知识治理
echo   运行环境: %PY_CMD%
echo   实际访问端口请以稍后的启动输出为准。
echo ========================================================================
"%PY_CMD%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo [错误] 当前运行环境需要 Python 3.11 或更高版本。
    pause
    exit /b 1
)
"%PY_CMD%" run.py
set "APP_EXIT=%errorlevel%"
if not "%APP_EXIT%"=="0" (
    echo.
    echo [提示] 服务启动失败或异常退出，请检查上方错误、依赖及 .env 配置。
    pause
)
exit /b %APP_EXIT%
