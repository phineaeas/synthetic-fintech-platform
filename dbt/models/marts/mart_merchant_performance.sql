-- Mart: mart_merchant_performance. Грануляция: 1 строка = 1 мерчант.
--
-- success_rate - это доля (0..1), не проценты - форматируйте в % на
-- уровне BI при необходимости. NULLIF защищает от деления на ноль для
-- мерчантов без единой транзакции (LEFT JOIN сохраняет их, та же логика,
-- что в mart_customer_activity).

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
