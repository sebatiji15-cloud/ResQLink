-- ═══════════════════════════════════════════════════════════
--  ResQLink  –  Database Setup
--  Run this ONCE in phpMyAdmin → SQL tab before starting app
-- ═══════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS resqlink_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE resqlink_db;

-- ── Drop old tables if exist (fresh setup) ───────────────────
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS volunteer_applications;
DROP TABLE IF EXISTS volunteers;
DROP TABLE IF EXISTS users;

-- ── Users table (ordinary users only) ────────────────────────
CREATE TABLE users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    phone      VARCHAR(20)  NOT NULL,
    address    VARCHAR(255) DEFAULT '',
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Volunteer Applications (before approval) ──────────────────
-- plain_password stores the original password so it can be emailed on approval
CREATE TABLE volunteer_applications (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(120) NOT NULL,
    email            VARCHAR(150) NOT NULL UNIQUE,
    phone            VARCHAR(20)  NOT NULL,
    address          VARCHAR(255) DEFAULT '',
    password         VARCHAR(255) NOT NULL,       -- hashed password (for login)
    plain_password   VARCHAR(255) NOT NULL,       -- plain text (for emailing once on approval)
    certificate_file VARCHAR(255) DEFAULT NULL,
    degree_file      VARCHAR(255) DEFAULT NULL,
    volunteer_id     VARCHAR(20)  DEFAULT NULL,   -- Assigned when approved
    status           ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    admin_notes      TEXT DEFAULT NULL,
    applied_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at      DATETIME DEFAULT NULL
);

-- ── Verified Volunteers (only approved volunteers) ────────────
CREATE TABLE volunteers (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id      VARCHAR(20)  NOT NULL UNIQUE,
    name              VARCHAR(120) NOT NULL,
    email             VARCHAR(150) NOT NULL UNIQUE,
    phone             VARCHAR(20)  NOT NULL,
    address           VARCHAR(255) DEFAULT '',
    password          VARCHAR(255) NOT NULL,
    certificate_file  VARCHAR(255) DEFAULT NULL,
    degree_file       VARCHAR(255) DEFAULT NULL,
    verified_by_admin VARCHAR(120) DEFAULT NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Emergency Requests ────────────────────────────────────────
CREATE TABLE requests (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT          NOT NULL,
    volunteer_id INT          DEFAULT NULL,
    etype        VARCHAR(100) NOT NULL,
    description  TEXT         NOT NULL,
    location     VARCHAR(255) NOT NULL,
    latitude     VARCHAR(30)  DEFAULT '',
    longitude    VARCHAR(30)  DEFAULT '',
    status       ENUM('pending','active','resolved') NOT NULL DEFAULT 'pending',
    created_at   TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME   DEFAULT NULL,
    resolved_at  DATETIME   DEFAULT NULL,
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (volunteer_id) REFERENCES volunteers(id) ON DELETE SET NULL
);

CREATE INDEX idx_status ON requests(status);
CREATE INDEX idx_user   ON requests(user_id);
CREATE INDEX idx_vol    ON requests(volunteer_id);

-- ── Demo accounts ─────────────────────────────────────────────
-- Password for all demo accounts = "Test123"
INSERT INTO users (name, email, phone, address, password) VALUES
('Seba Thomas', 'user@resqlink.com', '9876543210', 'Ernakulam, Kerala', SHA2('Test123', 256));

INSERT INTO volunteers (volunteer_id, name, email, phone, address, password, verified_by_admin, created_at) VALUES
('VID-000001', 'Rahul Volunteer', 'volunteer@resqlink.com', '9876543211', 'Kochi, Kerala', SHA2('Test123', 256), 'Admin', NOW());

-- ── Admin Account ─────────────────────────────────────────────
INSERT INTO users (name, email, phone, address, password) VALUES
('Admin User', 'admin@resqlink.com', '9876543212', 'Admin Office', SHA2('Admin123', 256));
