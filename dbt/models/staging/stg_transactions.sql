-- Staging: приводим raw.transactions к надёжному виду "1 строка = 1
-- транзакция". Самая крупная и самая связанная staging-модель - два FK
-- на проверку (account_id, merchant_id) и первый настоящий числовой каст
-- в этом проекте.
--
-- Намеренно НЕ фильтруется здесь: отрицательные суммы. Отрицательная
-- сумма - правдоподобное бизнес-состояние (например, может означать
-- возврат, хотя у нас есть и отдельный transaction_type = 'refund'), а не
-- структурная проблема вроде отсутствующего id или битого FK - поэтому
-- она остаётся видимой дальше по пайплайну, а не тихо выбрасывается. В
-- этом проекте нет dbt-теста, требующего amount >= 0 (вне скоупа:
-- встроенные generic-тесты из раздела 17 спецификации -
-- unique/not_null/accepted_values/relationships - не включают проверку
-- числового диапазона без дополнительного пакета).
--
-- Колонка amount в RAW текстовая (почему - см.
-- postgres/init/02_raw_tables.sql), а наше искажение "неверный тип"
-- всегда даёт валидную числовую строку (например "164.68"), так что
-- обычный CAST здесь безопасен - он никогда не встретит по-настоящему
-- нечисловое значение.

with source as (

    select * from {{ source('raw', 'transactions') }}

),

cleaned as (

    select
        transaction_id,
        account_id,
        merchant_id,
        cast(transaction_ts as timestamp) as transaction_ts,
        cast(amount as numeric) as amount,
        upper(currency) as currency,
        lower(transaction_type) as transaction_type,
        lower(status) as status

    from source
    where transaction_id is not null
      and account_id is not null
      and merchant_id is not null

),

valid_fks as (

    select cleaned.*
    from cleaned
    inner join {{ ref('stg_accounts') }} as accounts
        on cleaned.account_id = accounts.account_id
    inner join {{ ref('stg_merchants') }} as merchants
        on cleaned.merchant_id = merchants.merchant_id

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by transaction_id
            order by transaction_ts desc
        ) as _row_num

    from valid_fks

)

select
    transaction_id,
    account_id,
    merchant_id,
    transaction_ts,
    amount,
    currency,
    transaction_type,
    status

from deduplicated
where _row_num = 1
