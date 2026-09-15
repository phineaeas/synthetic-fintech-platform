-- Staging: clean up raw.transactions into a reliable 1-row-per-transaction
-- shape. Largest and most connected staging model - two FKs to validate
-- (account_id, merchant_id) and the first real numeric cast in this project.
--
-- Deliberately NOT filtered here: negative amounts. A negative amount is a
-- plausible business state (e.g. could represent a refund even though we
-- also have a separate transaction_type = 'refund'), not a structural
-- problem like a missing id or an orphan FK - so it's left visible
-- downstream rather than silently dropped. There is no dbt test enforcing
-- amount >= 0 in this project (out of scope: the built-in generic tests
-- section 17 asks for - unique/not_null/accepted_values/relationships -
-- don't include numeric-range checks without an extra package).
--
-- The RAW `amount` column is text (see postgres/init/02_raw_tables.sql for
-- why), and our "wrong type" corruption always produces a valid numeric
-- string (e.g. "164.68"), so a plain CAST is safe here - it never
-- encounters a genuinely non-numeric value.

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
