-- RAW layer (spec section 12).
--
-- Design decision: RAW tables carry NO constraints (no PRIMARY KEY, no
-- FOREIGN KEY, no NOT NULL) on purpose. Section 10 requires intentionally
-- injecting NULLs, duplicates, invalid FKs and negative amounts into this
-- layer, so any constraint here would either reject the load or silently
-- "fix" bad data before staging gets a chance to validate/normalize it.
-- RAW is a landing zone: it should accept exactly what the source produced.
--
-- All columns are typed loosely (text/timestamp without strict checks)
-- for the same reason: e.g. currency/status stay as free text so values
-- like "rub" vs "RUB" or "SUCCESS" vs "success" can pass through untouched.

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id     text,
    created_at      timestamp,
    birth_date      date,
    country         text,
    city            text,
    segment         text,
    status          text,
    _loaded_at      timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.accounts (
    account_id      text,
    customer_id     text,
    account_type    text,
    currency        text,
    opened_at       timestamp,
    closed_at       timestamp,
    status          text,
    _loaded_at      timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.merchants (
    merchant_id     text,
    merchant_name   text,
    category        text,
    country         text,
    _loaded_at      timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.transactions (
    transaction_id      text,
    account_id          text,
    merchant_id          text,
    transaction_ts       timestamp,
    amount               numeric,
    currency             text,
    transaction_type     text,
    status                text,
    _loaded_at            timestamp NOT NULL DEFAULT now()
);

-- _loaded_at is our own bookkeeping column (not part of source semantics):
-- it records when the loader inserted the row, useful later for debugging
-- full-refresh runs and for a "freshness" check if we add one.
