CREATE TABLE IF NOT EXISTS push_subscriptions (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER,
    endpoint   TEXT NOT NULL UNIQUE,
    p256dh     TEXT NOT NULL,
    auth       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
