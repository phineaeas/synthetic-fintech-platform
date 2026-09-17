"""
Конфигурация Superset, монтируется в официальный образ по пути
/app/pythonpath/superset_config.py (задокументированная точка расширения
Superset - любой .py файл там автоматически импортируется при старте).
 
Как и Airflow, собственные метаданные Superset (дашборды, графики,
сохранённые запросы, пользователи) живут в ОТДЕЛЬНОЙ БАЗЕ данных, не в
схемах raw/staging/core/mart самого склада данных. К складу данных
Superset подключается отдельно, как обычное "подключение к базе данных",
настраиваемое через собственный UI после запуска (Admin -> Database
Connections), а не через этот конфигурационный файл.
"""

import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@postgres:5432/superset"
)
