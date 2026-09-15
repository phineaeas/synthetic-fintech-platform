-- Core: dim_merchant. Grain: 1 row = 1 merchant.
-- See dim_customer.sql for why this layer exists despite being a pass-through.

select
    merchant_id,
    merchant_name,
    category,
    country

from {{ ref('stg_merchants') }}
