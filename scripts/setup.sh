#!/usr/bin/env bash
# Разовая настройка окружения. Безопасно перезапускать, каждый шаг идемпотентен
#
# Что делает скрипт:
#   1. Проверяет, что Docker и Docker Compose установлены и доступны в PATH
#   2. Создаёт .env из .env.example, если .env ещё не существует
#   3. Открывает права на запись в data/ и dbt/, чтобы Airflow-контейнер
#      (работающий от другого пользователя, не от вашего) мог писать
#      сгенерированные файлы и собственные target/logs dbt в эти
#      смонтированные папки
#
# Нужен Unix-подобный shell: на Linux и macOS работает как есть. На Windows
# запускайте из терминала WSL2 (не из PowerShell) — см. README, раздел
# про требования.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Checking for Docker..."
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: команда 'docker' не найдена. Установите  Install Docker Desktop (Windows/macOS)"
    echo "       или Docker Engine (Linux) чтобы продолжить"
    exit 1
fi

echo "==> Checking for Docker Compose..."
if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: команда 'docker compose' не найдена"
    echo "       Docker Compose v2 идёт в комплекте с последними версиями Docker Desktop"
    echo "       на Linux может потребоваться установить плагин compose отдельно"
    exit 1
fi

echo "==> Setting up .env..."
if [ -f .env ]; then
    echo "    .env already exists, leaving it untouched."
else
    cp .env.example .env
    echo "    Created .env from .env.example (safe defaults, no changes needed)."
fi

echo "==> Fixing permissions on data/ and dbt/..."
echo "    (Airflow's container user can't write into these bind-mounted"
echo "    directories otherwise - see README for why.)"
CHMOD_LOG="$(mktemp)"
chmod -R 777 data/ dbt/ 2>"$CHMOD_LOG" || true
if [ -s "$CHMOD_LOG" ]; then
    echo "    Примечание: у некоторых файлов не удалось изменить права - это"
    echo "    случается, если Airflow (работающий под другим пользователем внутри"
    echo "    своего контейнера) уже создал их, например dbt/target/*.json из"
    echo "    предыдущего запуска 'dbt run', вызванного через DAG. Если задачи Airflow"
    echo "    позже завершатся с ошибкой PermissionError, повторите этот шаг с sudo:"
    echo "        sudo chmod -R 777 data/ dbt/"
fi
rm -f "$CHMOD_LOG"

echo "    Примечание: у некоторых файлов не удалось изменить права - это"
echo "    случается, если Airflow (работающий под другим пользователем внутри"
echo "    своего контейнера) уже создал их, например dbt/target/*.json из"
echo "    предыдущего запуска 'dbt run', вызванного через DAG. Если задачи Airflow"
echo "    позже завершатся с ошибкой PermissionError, повторите этот шаг с sudo:"
echo "        sudo chmod -R 777 data/ dbt/"
