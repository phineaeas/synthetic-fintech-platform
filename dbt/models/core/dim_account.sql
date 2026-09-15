-- Core: dim_account. Grain: 1 row = 1 account.
-- See dim_customer.sql for why this layer exists despite being a pass-through.

select
    account_id,
    customer_id,
    account_type,
    currency,
    opened_at,
    closed_at,
    status

from {{ ref('stg_accounts') }}
