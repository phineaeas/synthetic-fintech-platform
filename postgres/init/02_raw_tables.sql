-- RAW-слой 
-- Осознанное решение: в этих таблицах НЕТ никаких ограничений (ни PRIMARY
-- KEY, ни FOREIGN KEY, ни NOT NULL). Тут мы намеренно
-- подмешиваем в этот слой NULL-ы, дубликаты, битые внешние ключи и
-- отрицательные суммы, а любое ограничение либо отклонило бы такую
-- вставку, либо тихо "починило" бы плохие данные ещё до того, как их
-- должен поймать и обработать staging.
--
-- ВСЕ бизнес-колонки `text`, включая даты и суммы. Это осознанная
-- правка более ранней версии файла, где даты были `date`/`timestamp`,
-- а сумма `numeric`: при такой типизации Postgres сам молча приводит
-- тип при вставке, и намеренно "битый тип" (сумма, сгенерированная как
-- строка вида "164.68" вместо числа 164.68) тихо чинится ещё до того,
-- как до неё доберётся staging. 

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

-- _loaded_at это служебная колонка (не часть исходных
-- данных источника): фиксирует момент, когда загрузчик реально вставил
-- строку. Остаётся типом `timestamp`, потому
-- что значение всегда задаём мы сами через `DEFAULT now()`- сюда
-- никогда не попадут намеренно испорченные данные источника.
