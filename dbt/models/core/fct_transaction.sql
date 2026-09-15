-- Core: fct_transaction. Grain: 1 row = 1 transaction.
-- See dim_customer.sql for why this layer exists despite being a pass-through.

select
    transaction_id,
    account_id,
    merchant_id,
    transaction_ts,
    amount,
    currency,
    transaction_type,
    status

from {{ ref('stg_transactions') }}
