-- ═══════════════════════════════════════════════════════════════════════
-- GarmentFlow — Access Control Migration
-- Adds: groups, user_groups tables
-- Run manually if not using SQLAlchemy auto-create (create_all on startup)
-- ═══════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS groups (
    id                    SERIAL PRIMARY KEY,
    group_code            VARCHAR(20)  UNIQUE NOT NULL,
    group_name            VARCHAR(100) NOT NULL,
    description           VARCHAR(255),
    can_access_orders     BOOLEAN DEFAULT FALSE,
    can_access_productions BOOLEAN DEFAULT FALSE,
    can_access_shipments  BOOLEAN DEFAULT FALSE,
    is_active             BOOLEAN DEFAULT TRUE,
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_groups (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    group_id   INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_user_group UNIQUE (user_id, group_id)
);

CREATE INDEX IF NOT EXISTS idx_user_groups_user  ON user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group ON user_groups(group_id);
