-- Staging: clean up raw.customers into a reliable 1-row-per-customer shape.
--
-- Steps, in order:
--   1. cast text columns from RAW to their real types
--   2. normalize casing (status/segment lowercase, country/city Title Case)
--   3. drop rows with a NULL customer_id - can't have a dimension row
--      without an identifiable business key
--   4. deduplicate exact-duplicate rows (keep one per customer_id)
--
-- Deliberately NOT filtered here: future-dated created_at. That's a
-- plausible-but-suspicious value, not a structural problem - it stays
-- visible downstream rather than being silently dropped.

with source as (

    select * from {{ source('raw', 'customers') }}

),

cleaned as (

    select
        customer_id,
        cast(created_at as timestamp) as created_at,
        cast(birth_date as date) as birth_date,
        initcap(country) as country,
        initcap(city) as city,
        lower(segment) as segment,
        lower(status) as status

    from source
    where customer_id is not null

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by customer_id
            order by created_at desc
        ) as _row_num

    from cleaned

)

select
    customer_id,
    created_at,
    birth_date,
    country,
    city,
    segment,
    status

from deduplicated
where _row_num = 1
