-- Core: dim_account. Грануляция: 1 строка = 1 счёт.
-- Почему этот слой существует, несмотря на то что это прямой перенос - см. dim_customer.sql.

select
    account_id,
    customer_id,
    account_type,
    currency,
    opened_at,
    closed_at,
    status

from {{ ref('stg_accounts') }}
