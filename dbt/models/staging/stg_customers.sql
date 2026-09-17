-- Staging: приводим raw.customers к надёжному виду "1 строка = 1 клиент".
--
-- Шаги по порядку:
--   1. каст текстовых колонок из RAW в их настоящие типы
--   2. нормализация регистра (status/segment - нижний регистр,
--      country/city - Заглавные Буквы)
--   3. отбрасываем строки с NULL customer_id - не может быть строки
--      измерения без опознаваемого бизнес-ключа
--   4. дедупликация точных дублей (оставляем одну строку на customer_id)


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
