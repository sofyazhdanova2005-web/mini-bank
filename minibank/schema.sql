-- Схема базы данных «Мини-банк» (SQLite)
-- Построена по ER-диаграмме db/er-diagram.drawio
-- Денежные суммы хранятся в копейках (INTEGER), чтобы не было ошибок округления.

PRAGMA foreign_keys = ON;

-- Клиенты банка
CREATE TABLE IF NOT EXISTS clients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT    NOT NULL,
    passport    TEXT    NOT NULL UNIQUE,
    phone       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Справочник видов счетов
CREATE TABLE IF NOT EXISTS account_types (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    rate        REAL    NOT NULL DEFAULT 0      -- годовая ставка, %
);

-- Счета клиентов
CREATE TABLE IF NOT EXISTS accounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    number      TEXT    NOT NULL UNIQUE,         -- 20-значный номер счёта
    client_id   INTEGER NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    type_id     INTEGER NOT NULL REFERENCES account_types(id),
    balance     INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    opened_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Операции по счетам: пополнение, снятие, перевод
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kind            TEXT    NOT NULL CHECK (kind IN ('DEPOSIT', 'WITHDRAW', 'TRANSFER')),
    from_account_id INTEGER REFERENCES accounts(id),
    to_account_id   INTEGER REFERENCES accounts(id),
    amount          INTEGER NOT NULL CHECK (amount > 0),
    comment         TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_accounts_client ON accounts(client_id);
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_account_id);

-- Начальные данные справочника
INSERT OR IGNORE INTO account_types (name, rate) VALUES
    ('Текущий', 0),
    ('Сберегательный', 8.5),
    ('Кредитный', 0);
