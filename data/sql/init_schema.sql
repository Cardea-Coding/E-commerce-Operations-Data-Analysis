CREATE DATABASE IF NOT EXISTS ecommerce_analysis DEFAULT CHARACTER SET utf8mb4;
USE ecommerce_analysis;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    age INT NOT NULL DEFAULT 25,
    gender VARCHAR(16) NOT NULL DEFAULT 'unknown',
    region VARCHAR(64) NOT NULL DEFAULT '未知',
    created_at DATETIME NOT NULL,
    last_login_at DATETIME NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    cost DECIMAL(10, 2) NOT NULL DEFAULT 0,
    stock INT NOT NULL DEFAULT 0,
    rating DECIMAL(3, 2) NOT NULL DEFAULT 5,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(128) NOT NULL,
    campaign_type VARCHAR(64) NOT NULL DEFAULT 'promotion',
    cost DECIMAL(12, 2) NOT NULL DEFAULT 0,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    campaign_id INT NULL,
    coupon_type VARCHAR(64) NULL,
    quantity INT NOT NULL DEFAULT 1,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    payment_status VARCHAR(16) NOT NULL DEFAULT 'paid',
    refund_status VARCHAR(16) NOT NULL DEFAULT 'none',
    created_at DATETIME NOT NULL,
    INDEX idx_orders_time(created_at),
    INDEX idx_orders_filter(created_at, payment_status, refund_status),
    INDEX idx_orders_user(user_id),
    INDEX idx_orders_product(product_id),
    INDEX idx_orders_campaign_time(campaign_id, created_at),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT fk_orders_campaign FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id)
);

CREATE TABLE IF NOT EXISTS user_behaviors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    behavior_type VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_behaviors_time(created_at),
    INDEX idx_behaviors_type(behavior_type),
    INDEX idx_behaviors_type_time(behavior_type, created_at),
    CONSTRAINT fk_behaviors_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_behaviors_product FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    score INT NOT NULL DEFAULT 5,
    tags VARCHAR(255) NULL,
    content TEXT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS coupon_usages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    campaign_id INT NULL,
    coupon_type VARCHAR(64) NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    used BOOLEAN NOT NULL DEFAULT 0,
    amount_before DECIMAL(10, 2) NOT NULL DEFAULT 0,
    amount_after DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    INDEX idx_coupon_time(created_at),
    INDEX idx_coupon_campaign_time(campaign_id, created_at),
    CONSTRAINT fk_coupon_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_coupon_campaign FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id)
);

CREATE TABLE IF NOT EXISTS ad_performance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    campaign_id INT NOT NULL,
    stat_date DATE NOT NULL,
    clicks INT NOT NULL DEFAULT 0,
    cost DECIMAL(10, 2) NOT NULL DEFAULT 0,
    conversions INT NOT NULL DEFAULT 0,
    gmv DECIMAL(12, 2) NOT NULL DEFAULT 0,
    INDEX idx_ad_date(stat_date),
    INDEX idx_ad_campaign_date(campaign_id, stat_date),
    CONSTRAINT fk_ad_campaign FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id)
);

CREATE TABLE IF NOT EXISTS data_sync_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    source VARCHAR(64) NOT NULL,
    mode VARCHAR(16) NOT NULL DEFAULT 'manual',
    status VARCHAR(16) NOT NULL DEFAULT 'success',
    inserted_users INT NOT NULL DEFAULT 0,
    inserted_products INT NOT NULL DEFAULT 0,
    inserted_orders INT NOT NULL DEFAULT 0,
    inserted_behaviors INT NOT NULL DEFAULT 0,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    message VARCHAR(255) NULL,
    INDEX idx_sync_source(source),
    INDEX idx_sync_status(status)
);

CREATE TABLE IF NOT EXISTS decision_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_key VARCHAR(64) NOT NULL UNIQUE,
    rule_name VARCHAR(128) NOT NULL,
    rule_type VARCHAR(32) NOT NULL,
    threshold_value DECIMAL(12, 2) NOT NULL DEFAULT 0,
    action_text VARCHAR(255) NOT NULL,
    reason_template VARCHAR(255) NOT NULL,
    priority_weight INT NOT NULL DEFAULT 50,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS metric_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(128) NOT NULL UNIQUE,
    expression VARCHAR(255) NOT NULL,
    variables_schema TEXT NOT NULL,
    description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS report_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(128) NOT NULL UNIQUE,
    query_type VARCHAR(64) NOT NULL,
    filters_json TEXT NOT NULL,
    columns_json TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS export_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_name VARCHAR(128) NOT NULL,
    export_format VARCHAR(16) NOT NULL,
    row_count INT NOT NULL DEFAULT 0,
    file_path VARCHAR(255) NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'success',
    created_at DATETIME NOT NULL
);