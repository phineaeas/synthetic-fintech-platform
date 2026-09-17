# Официальный образ apache/superset не включает драйвер Postgres, а его
# venv в рантайме намеренно закрыт на запись для непривилегированного
# пользователя, от имени которого работает контейнер - поэтому psycopg2
# нельзя доустановить "на лету" при старте контейнера (как мы сделали для
# Airflow через _PIP_ADDITIONAL_REQUIREMENTS). Установка здесь, на этапе
# СБОРКИ образа (пока процесс ещё root, до того как базовый образ сам
# переключится на непривилегированного пользователя) - задокументированный
# способ добавить драйвер БД в этот образ.
FROM apache/superset:latest
 
USER root
RUN /app/.venv/bin/python -m ensurepip --upgrade \
    && /app/.venv/bin/python -m pip install --no-cache-dir psycopg2-binary
 

