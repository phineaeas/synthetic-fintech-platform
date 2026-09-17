-- Staging: приводим raw.accounts к надёжному виду "1 строка = 1 счёт".
--
-- Тот же паттерн, что stg_customers, плюс один дополнительный фильтр:
-- счета, чей customer_id не совпадает ни с одной строкой в stg_customers,
-- отбрасываются здесь. Именно это держит зелёным relationships-тест на
-- stg_accounts.customer_id ниже по пайплайну - проблема "битый FK"
-- ловится и решается на этом слое, а не остаётся для core.

with source as (

    select * from {{ source('raw', 'accounts') }}

),

cleaned as (

    select
        account_id,
        customer_id,
        account_type,
        upper(currency) as currency,
        cast(opened_at as timestamp) as opened_at,
        cast(closed_at as timestamp) as closed_at,
        lower(status) as status

    from source
    where account_id is not null
      and customer_id is not null

),

valid_customer_fk as (

    select cleaned.*
    from cleaned
    inner join {{ ref('stg_customers') }} as customers
        on cleaned.customer_id = customers.customer_id

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by account_id
            order by opened_at desc
        ) as _row_num

    from valid_customer_fk

)

select
    account_id,
    customer_id,
    account_type,
    currency,
    opened_at,
    closed_at,
    status

from deduplicated
where _row_num = 1
