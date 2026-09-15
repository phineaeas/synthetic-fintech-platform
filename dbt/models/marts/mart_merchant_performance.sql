-- Mart: mart_merchant_performance. Grain: 1 row = 1 merchant.
--
-- success_rate is a fraction (0..1), not a percentage - format as % in the
-- BI layer if needed. NULLIF guards against divide-by-zero for merchants
-- with zero transactions (left join preserves them, same reasoning as
-- mart_customer_activity).

with merchants as (

    select * from {{ ref('dim_merchant') }}

),

transactions as (

    select * from {{ ref('fct_transaction') }}

),

aggregated as (

    select
        merchant_id,
        count(*) as transaction_count,
        sum(amount) as total_amount,
        avg(amount) as average_transaction,
        count(*) filter (where status = 'success')::numeric
            / nullif(count(*), 0) as success_rate

    from transactions
    group by 1

)

select
    merchants.merchant_id,
    merchants.merchant_name,
    merchants.category,
    coalesce(aggregated.transaction_count, 0) as transaction_count,
    aggregated.total_amount,
    aggregated.average_transaction,
    aggregated.success_rate

from merchants
left join aggregated
    on merchants.merchant_id = aggregated.merchant_id
