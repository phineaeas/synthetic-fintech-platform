-- Mart: mart_daily_transactions. Grain: 1 row = 1 calendar day.
--
-- Design note: total_amount / average_transaction_amount are computed
-- across ALL transactions regardless of status (success/failed/pending),
-- mirroring transaction_count. If you need "successful revenue only",
-- that's a different, deliberately narrower metric - filter by status in
-- the BI layer (Superset) rather than baking one interpretation into this
-- mart's only amount column.

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
