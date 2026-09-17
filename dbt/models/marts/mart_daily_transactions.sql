-- Mart: mart_daily_transactions. Грануляция: 1 строка = 1 календарный день.
--
-- Design-заметка: total_amount / average_transaction_amount считаются по
-- ВСЕМ транзакциям, независимо от статуса (success/failed/pending),
-- зеркально transaction_count. Если нужна метрика "только успешная
-- выручка" - это другая, намеренно более узкая метрика: фильтруйте по
-- статусу на уровне BI (Superset), а не зашивайте одну интерпретацию в
-- единственную колонку суммы этого mart'а.

with transactions as (

    select * from {{ ref('fct_transaction') }}

),

daily as (

    select
        cast(transaction_ts as date) as date,
        count(*) as transaction_count,
        count(*) filter (where status = 'success') as successful_transaction_count,
        count(*) filter (where status = 'failed') as failed_transaction_count,
        sum(amount) as total_amount,
        avg(amount) as average_transaction_amount

    from transactions
    group by 1

)

select * from daily
