CREATE TABLE IF NOT EXISTS students (
    id            UUID        PRIMARY KEY,
    name          TEXT        NOT NULL,
    email         TEXT        NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    grade         INTEGER     NOT NULL,
    is_first_login BOOLEAN    NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP   NOT NULL DEFAULT NOW()
);