@echo off
if "%~1"=="-utf8" goto :RUN

chcp 65001 > nul && cmd /c "%~f0" -utf8
exit /b

:RUN
title Kaguya UserBot Launcher

echo 🌸 Kaguya UserBot ➔ Запуск загрузчика...
echo --------------------------------------------------

python --version >nul 2>&1
if %errorlevel% neq 0 goto :NO_PYTHON

if not exist .venv (
    echo [Kaguya] Создаю виртуальное окружение .venv...
    python -m venv .venv
)

echo [Kaguya] Активация виртуального окружения...
call .venv\Scripts\activate

echo [Kaguya] Установка и обновление библиотек...
for /f "usebackq delims=" %%a in ("requirements.txt") do (
    if "%%a"=="tgcrypto" echo [Kaguya] Обрати внимание: Установка tgcrypto может выдать ошибку. Это нормально, бот продолжит запуск!
    echo [Kaguya] Устанавливаю/Обновляю: %%a
    pip install %%a --quiet
)

echo [Kaguya] Запуск Kaguya UserBot...
echo --------------------------------------------------
python main.py
pause
exit

:NO_PYTHON
echo [Kaguya] Ошибка: Python не установлен или не добавлен в переменную PATH!
echo Пожалуйста, установи Python версии 3.11+ и обязательно отметь галочку "Add Python to PATH" при установке.
echo Ссылка для скачивания: https://www.python.org/downloads/
pause
exit