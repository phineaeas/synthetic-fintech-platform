-- Staging: clean up raw.accounts into a reliable 1-row-per-account shape.
--
-- Same pattern as stg_customers, plus one extra filter: accounts whose
-- customer_id doesn't match any row in stg_customers are dropped here.
-- This is what keeps the `relationships` test on stg_accounts.customer_id
-- passing downstream - the orphan FK problem is caught and resolved at
-- this layer, not left for core to trip over.

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
