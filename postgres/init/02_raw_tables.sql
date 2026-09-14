-- RAW layer (spec section 12).
--
-- Design decision: RAW tables carry NO constraints (no PRIMARY KEY, no
-- FOREIGN KEY, no NOT NULL) on purpose. Section 10 requires intentionally
-- injecting NULLs, duplicates, invalid FKs and negative amounts into this
-- layer, so any constraint here would either reject the load or silently
-- "fix" bad data before staging gets a chance to validate/normalize it.
--
-- ALL business columns are `text`, including dates and amounts. This is a
-- deliberate correction from an earlier version of this file that typed
-- dates as `date`/`timestamp` and amount as `numeric`: Postgres performs an
-- implicit cast on INSERT for those types, which would silently "fix" the
-- intentional wrong-type corruption (amount generated as a numeric-looking
-- string, e.g. "164.68" instead of 164.68) before staging ever sees it.
-- Per spec section 13, type casting is staging's job, not RAW's - so RAW
-- must not have any type system that could do casting on its own.

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id     text,
    created_at      text,
    birth_date      text,
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
    opened_at       text,
    closed_at       text,
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
    transaction_ts       text,
    amount               text,
    currency             text,
    transaction_type     text,
    status                text,
    _loaded_at            timestamp NOT NULL DEFAULT now()
);

-- _loaded_at is our own bookkeeping column (not part of source semantics):
-- it records when the loader inserted the row, useful later for debugging
-- full-refresh runs and for a "freshness" check if we add one. It stays
-- as `timestamp` because we control its value ourselves (DEFAULT now()) -
-- it can never contain intentionally-bad source data.
