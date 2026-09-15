-- Mart: mart_customer_activity. Grain: 1 row = 1 customer.
--
-- Left-joined from dim_customer (not built up from transactions) so that
-- customers with zero transactions still appear as a row with
-- transaction_count = 0, rather than disappearing from the mart entirely -
-- "customers with no activity" is itself a meaningful thing to be able to
-- count in Superset (spec section 24: "active customers").

with customers as (

    select * from {{ ref('dim_customer') }}

),

accounts as (

    select * from {{ ref('dim_account') }}

),

transactions as (

    select * from {{ ref('fct_transaction') }}

),

customer_transactions as (

    select
        accounts.customer_id,
        transactions.transaction_id,
        transactions.amount,
        transactions.transaction_ts

    from transactions
    inner join accounts
        on transactions.account_id = accounts.account_id

),

aggregated as (

    select
        customer_id,
        count(transaction_id) as transaction_count,
        sum(amount) as total_amount,
        avg(amount) as average_transaction,
        min(transaction_ts) as first_transaction_at,
        max(transaction_ts) as last_transaction_at,
        count(distinct cast(transaction_ts as date)) as active_days

    from customer_transactions
    group by 1

)

select
    customers.customer_id,
    coalesce(aggregated.transaction_count, 0) as transaction_count,
    aggregated.total_amount,
    aggregated.average_transaction,
    aggregated.first_transaction_at,
    aggregated.last_transaction_at,
    coalesce(aggregated.active_days, 0) as active_days

from customers
left join aggregated
    on customers.customer_id = aggregated.customer_id
