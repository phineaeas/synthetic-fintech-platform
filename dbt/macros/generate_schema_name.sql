{#
  dbt's default generate_schema_name macro concatenates the profile's
  default schema with a model's custom +schema config, e.g. "dev_staging"
  instead of just "staging". We want our models to land in exactly the
  schema named in dbt_project.yml (staging/core/mart), matching spec
  section 11 - so this override uses the custom schema name literally
  whenever one is set, falling back to the profile's default schema only
  when a model has no explicit +schema config at all.
#}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
