-- Create Database if not exists
CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

-- 1. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    category_id INT,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    min_threshold INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- 3. Sales Table
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    customer_name VARCHAR(120) DEFAULT 'Walk-in Customer',
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- 4. Inventory Logs (Tracks Stock In & Stock Out)
CREATE TABLE IF NOT EXISTS inventory_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    change_type ENUM('IN', 'OUT') NOT NULL,
    quantity INT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Seed Initial Categories
INSERT INTO categories (name, description) VALUES
('Laptops & Computers', 'High performance laptops, desktops, and workstations'),
('Accessories', 'Keyboards, mice, webcams, and docking stations'),
('Audio', 'Noise cancelling headphones, earbuds, and microphones'),
('Storage & Networking', 'External SSDs, routers, and flash drives')
ON DUPLICATE KEY UPDATE name=name;

-- Seed Initial Products
INSERT INTO products (name, sku, category_id, price, quantity, min_threshold) VALUES
('Logitech MX Master 3S Mouse', 'LOG-MX-3S', 2, 99.99, 28, 5),
('Dell UltraSharp 27" 4K Monitor', 'DEL-U27-4K', 1, 489.50, 12, 4),
('Apple MacBook Air M3 (16GB/512GB)', 'APP-MBA-M3', 1, 1299.00, 7, 3),
('Sony WH-1000XM5 Headphones', 'SNY-XM5-BLK', 3, 349.99, 15, 5),
('Samsung T7 Shield 2TB Portable SSD', 'SAM-T7-2TB', 4, 189.95, 4, 6),
('Keychron Q1 Pro Mechanical Keyboard', 'KEY-Q1-PRO', 2, 199.00, 3, 5),
('Anker 737 GaN Prime Charger 140W', 'ANK-737-140', 2, 89.99, 35, 10)
ON DUPLICATE KEY UPDATE name=name;

-- Seed Initial Sales
INSERT INTO sales (product_id, quantity, unit_price, total_price, customer_name, sale_date) VALUES
(1, 2, 99.99, 199.98, 'Sarah Jenkins', DATE_SUB(NOW(), INTERVAL 4 DAY)),
(4, 1, 349.99, 349.99, 'Michael Scott', DATE_SUB(NOW(), INTERVAL 3 DAY)),
(3, 1, 1299.00, 1299.00, 'David Wallace', DATE_SUB(NOW(), INTERVAL 2 DAY)),
(7, 3, 89.99, 269.97, 'Jim Halpert', DATE_SUB(NOW(), INTERVAL 1 DAY)),
(2, 1, 489.50, 489.50, 'Pam Beesly', NOW());

-- Seed Initial Inventory Logs
INSERT INTO inventory_logs (product_id, change_type, quantity, reason, created_at) VALUES
(1, 'IN', 30, 'Initial supplier restock', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(1, 'OUT', 2, 'Sale Order #1001', DATE_SUB(NOW(), INTERVAL 4 DAY)),
(2, 'IN', 13, 'Bulk warehouse arrival', DATE_SUB(NOW(), INTERVAL 8 DAY)),
(2, 'OUT', 1, 'Sale Order #1005', NOW()),
(3, 'IN', 8, 'Apple direct delivery', DATE_SUB(NOW(), INTERVAL 6 DAY)),
(3, 'OUT', 1, 'Sale Order #1003', DATE_SUB(NOW(), INTERVAL 2 DAY)),
(5, 'IN', 4, 'Stock adjustment', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(6, 'IN', 3, 'Specialty import', DATE_SUB(NOW(), INTERVAL 3 DAY));
