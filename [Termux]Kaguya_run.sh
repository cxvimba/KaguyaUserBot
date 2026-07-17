#!/bin/bash

echo "🌸 Kaguya UserBot ➔ Запуск загрузчика..."
echo "--------------------------------------------------"

if ! command -v python &> /dev/null; then
    echo "[Kaguya] Установка Python в Termux..."
    pkg install python -y
fi

if ! command -v git &> /dev/null; then
    echo "[Kaguya] Установка Git в Termux..."
    pkg install git -y
fi

if [ ! -d ".venv" ]; then
    echo "[Kaguya] Создаю виртуальное окружение .venv..."
    python -m venv .venv
fi

echo "[Kaguya] Активация виртуального окружения..."
source .venv/bin/activate

echo "[Kaguya] Установка зависимостей построчно..."
if [ -f "requirements.txt" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue

        clean_line=$(echo "$line" | tr -d '\r' | xargs)

        if [ "$clean_line" = "tgcrypto" ]; then
            echo "[Kaguya] Обрати внимание: Установка tgcrypto может выдать ошибку. Это нормально, запуск продолжится!"
        fi

        echo "[Kaguya] Устанавливаю/Обновляю: $clean_line"
        pip install "$clean_line" --quiet
    done < requirements.txt
else
    echo "❌ Ошибка: Файл requirements.txt не найден в папке проекта!"
    exit 1
fi

if command -v termux-wake-lock &> /dev/null; then
  termux-wake-lock
  echo "[Kaguya] Android Wakelock активирован."
fi

echo "[Kaguya] Запуск Kaguya UserBot..."
echo "--------------------------------------------------"
python main.py

if command -v termux-wake-unlock &> /dev/null; then
  termux-wake-unlock
  echo "[Kaguya] Android Wakelock отключен."
fi
