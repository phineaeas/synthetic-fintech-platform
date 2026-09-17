-- Core: dim_merchant. Грануляция: 1 строка = 1 мерчант.

select
    merchant_id,
    merchant_name,
    category,
    country

from {{ ref('stg_merchants') }}
