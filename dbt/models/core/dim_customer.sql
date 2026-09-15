-- Core: dim_customer. Grain: 1 row = 1 customer.
--
-- A straight pass-through of stg_customers - all cleanup already happened
-- in staging. This model exists as a separate layer (materialized as a
-- TABLE, not a view) so downstream marts get a stable, fast-to-query
-- dimension rather than recomputing the staging CTE chain on every read.
-- It's also the natural place to add business logic later (e.g. SCD2
-- history, derived attributes) without touching staging's cleanup logic.

select
    customer_id,
    created_at,
    birth_date,
    country,
    city,
    segment,
    status

from {{ ref('stg_customers') }}
