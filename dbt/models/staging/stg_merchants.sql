-- Staging: приводим raw.merchants к надёжному виду "1 строка = 1 мерчант".

with source as (

    select * from {{ source('raw', 'merchants') }}

),

cleaned as (

    select
        merchant_id,
        merchant_name,
        lower(category) as category,
        initcap(country) as country

    from source
    where merchant_id is not null

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by merchant_id
            order by merchant_name
        ) as _row_num

    from cleaned

)

select
    merchant_id,
    merchant_name,
    category,
    country

from deduplicated
where _row_num = 1
