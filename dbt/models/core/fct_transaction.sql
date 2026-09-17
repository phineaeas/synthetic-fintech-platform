-- Core: fct_transaction. Грануляция: 1 строка = 1 транзакция.

select
    transaction_id,
    account_id,
    merchant_id,
    transaction_ts,
    amount,
    currency,
    transaction_type,
    status

from {{ ref('stg_transactions') }}
