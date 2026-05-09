-- ═══════════════════════════════════════════════════════════════════════
-- GarmentFlow Production Management System — Initial Schema
-- PostgreSQL
-- Run manually OR let SQLAlchemy auto-create tables on first startup.
-- ═══════════════════════════════════════════════════════════════════════

-- CREATE DATABASE order_mgmt;
-- \c order_mgmt;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    username         VARCHAR(50)  UNIQUE NOT NULL,
    email            VARCHAR(100) UNIQUE NOT NULL,
    hashed_password  VARCHAR(255) NOT NULL,
    full_name        VARCHAR(100),
    is_active        BOOLEAN DEFAULT TRUE,
    is_admin         BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- Masters
CREATE TABLE IF NOT EXISTS customers (
    id               SERIAL PRIMARY KEY,
    customer_code    VARCHAR(20)  UNIQUE NOT NULL,
    company_name     VARCHAR(150) NOT NULL,
    contact_person   VARCHAR(100),
    email            VARCHAR(100),
    phone            VARCHAR(30),
    country          VARCHAR(80),
    city             VARCHAR(80),
    address          TEXT,
    payment_terms    VARCHAR(50),
    status           VARCHAR(20)  DEFAULT 'active',
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brands (
    id           SERIAL PRIMARY KEY,
    brand_code   VARCHAR(20)  UNIQUE NOT NULL,
    brand_name   VARCHAR(150) NOT NULL,
    description  TEXT,
    website      VARCHAR(200),
    status       VARCHAR(20)  DEFAULT 'active',
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_brands (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    brand_id    INTEGER NOT NULL REFERENCES brands(id)   ON DELETE CASCADE,
    CONSTRAINT uq_customer_brand UNIQUE (customer_id, brand_id)
);

CREATE INDEX IF NOT EXISTS idx_customer_brands_customer ON customer_brands(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_brands_brand    ON customer_brands(brand_id);

CREATE TABLE IF NOT EXISTS garment_styles (
    id                   SERIAL PRIMARY KEY,
    style_no             VARCHAR(50)  UNIQUE NOT NULL,
    style_name           VARCHAR(150) NOT NULL,
    description          TEXT,
    category             VARCHAR(80),
    fabric_type          VARCHAR(100),
    fabric_composition   VARCHAR(200),
    season               VARCHAR(50),
    gender               VARCHAR(20),
    brand_id             INTEGER REFERENCES brands(id)   ON DELETE SET NULL,
    customer_id          INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    buyer_style_ref      VARCHAR(100),
    unit_of_measure      VARCHAR(20) DEFAULT 'PCS',
    standard_cost        NUMERIC(12,2),
    standard_minutes     NUMERIC(8,2),
    status               VARCHAR(20) DEFAULT 'active',
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS production_lines (
    id                SERIAL PRIMARY KEY,
    line_code         VARCHAR(20)  UNIQUE NOT NULL,
    line_name         VARCHAR(100) NOT NULL,
    floor             VARCHAR(50),
    capacity_per_day  INTEGER,
    operator_count    INTEGER,
    supervisor        VARCHAR(100),
    line_type         VARCHAR(50),
    description       TEXT,
    status            VARCHAR(20) DEFAULT 'active',
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- Transactions
CREATE TABLE IF NOT EXISTS orders (
    id             SERIAL PRIMARY KEY,
    order_no       VARCHAR(30)   UNIQUE NOT NULL,
    po_number      VARCHAR(100),
    customer_id    INTEGER NOT NULL REFERENCES customers(id)      ON DELETE RESTRICT,
    style_id       INTEGER NOT NULL REFERENCES garment_styles(id) ON DELETE RESTRICT,
    order_qty      INTEGER       NOT NULL,
    unit_price     NUMERIC(12,4) NOT NULL,
    currency       VARCHAR(10)   DEFAULT 'USD',
    order_date     DATE          DEFAULT CURRENT_DATE,
    delivery_date  DATE,
    remarks        TEXT,
    status         VARCHAR(30)   DEFAULT 'confirmed',
    created_at     TIMESTAMP DEFAULT NOW(),
    updated_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS productions (
    id              SERIAL PRIMARY KEY,
    production_no   VARCHAR(30)  UNIQUE NOT NULL,
    order_id        INTEGER NOT NULL REFERENCES orders(id)            ON DELETE RESTRICT,
    line_id         INTEGER NOT NULL REFERENCES production_lines(id)  ON DELETE RESTRICT,
    planned_start   DATE,
    planned_end     DATE,
    actual_start    DATE,
    actual_end      DATE,
    planned_qty     INTEGER NOT NULL,
    output_qty      INTEGER DEFAULT 0,
    rejected_qty    INTEGER DEFAULT 0,
    remarks         TEXT,
    status          VARCHAR(30) DEFAULT 'scheduled',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shipments (
    id                  SERIAL PRIMARY KEY,
    invoice_no          VARCHAR(30)  UNIQUE NOT NULL,
    order_id            INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    shipment_date       DATE DEFAULT CURRENT_DATE,
    shipped_qty         INTEGER NOT NULL,
    carton_count        INTEGER,
    net_weight_kg       NUMERIC(10,2),
    gross_weight_kg     NUMERIC(10,2),
    unit_price          NUMERIC(12,4),
    currency            VARCHAR(10)  DEFAULT 'USD',
    port_of_loading     VARCHAR(100),
    port_of_discharge   VARCHAR(100),
    vessel_name         VARCHAR(150),
    bl_number           VARCHAR(100),
    etd                 DATE,
    eta                 DATE,
    remarks             TEXT,
    status              VARCHAR(30) DEFAULT 'draft',
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_style       ON orders(style_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
CREATE INDEX IF NOT EXISTS idx_productions_order  ON productions(order_id);
CREATE INDEX IF NOT EXISTS idx_productions_line   ON productions(line_id);
CREATE INDEX IF NOT EXISTS idx_productions_status ON productions(status);
CREATE INDEX IF NOT EXISTS idx_shipments_order    ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_status   ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_styles_brand       ON garment_styles(brand_id);
CREATE INDEX IF NOT EXISTS idx_styles_customer    ON garment_styles(customer_id);
