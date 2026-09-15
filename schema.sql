-- ============================================================
-- COSC 4378 Lab Project - Database Schema
-- Database Administrator deliverable
--
-- Run on the Raspberry Pi 5 (where MariaDB is installed):
--     mariadb -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS webserver_db;
USE webserver_db;

CREATE TABLE IF NOT EXISTS pages (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    path          VARCHAR(255) NOT NULL UNIQUE,
    html_content  MEDIUMTEXT NOT NULL,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE USER IF NOT EXISTS 'webserver'@'%' IDENTIFIED BY 'changeme';
GRANT SELECT, INSERT, UPDATE ON webserver_db.pages TO 'webserver'@'%';
FLUSH PRIVILEGES;

INSERT INTO pages (path, html_content) VALUES
('/index.html',
 '<html><head><title>Home</title></head><body><h1>Welcome!</h1><p>This page was served from MariaDB via the Pico 2 W cache.</p></body></html>'),
('/about.html',
 '<html><head><title>About</title></head><body><h1>About</h1><p>COSC 4378 Networks Lab Project.</p></body></html>')
ON DUPLICATE KEY UPDATE html_content = VALUES(html_content);