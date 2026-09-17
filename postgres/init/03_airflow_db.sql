-- Создаем отдельную бд внутри этого экземплюра pg 
-- для метаданных Aiflow (запуски DAG'ов, task instances, connections
-- и т.д.)

CREATE DATABASE airflow;
