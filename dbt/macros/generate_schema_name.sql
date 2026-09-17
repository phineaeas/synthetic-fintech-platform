{#
  Стандартный макрос generate_schema_name в dbt склеивает схему по
  умолчанию из профиля со схемой модели, например "dev_staging" вместо
  просто "staging". Мы хотим, чтобы модели попадали ровно в те схемы,
  что названы в dbt_project.yml (staging/core/mart), поэтому здесь мы переопределяем поведение: 
  если у модели задана своя схема (+schema), используем её буквально, без склеивания;
  на схему из профиля по умолчанию откатываемся только если у модели
  вообще нет явного +schema.
#}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
