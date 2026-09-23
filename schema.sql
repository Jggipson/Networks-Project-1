/*This is the SQL script that sets up the database and table for the web server project. 
It creates a database called "webserver_db", a table called "pages" to store HTML content, 
and a user with some privileges to be able to access the database.*/

--This creates the database if it doesn't already exist and switches to it.
CREATE DATABASE IF NOT EXISTS webserver_db;
USE webserver_db;

--This creates the "pages" table with columns for id, path, html_content, and last_modified timestamp.
CREATE TABLE IF NOT EXISTS pages (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    path          VARCHAR(255) NOT NULL UNIQUE,
    html_content  MEDIUMTEXT NOT NULL,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- This creates a user named "webserver" with the password "changeme" and grants it some privileges to select, 
-- insert, and update records in the "pages" table.
CREATE USER IF NOT EXISTS 'webserver'@'%' IDENTIFIED BY 'changeme';
GRANT SELECT, INSERT, UPDATE ON webserver_db.pages TO 'webserver'@'%';
FLUSH PRIVILEGES;

-- This inserts a default page into the "pages" table. If a page with the same path already exists,
-- it updates the HTML content instead of inserting a new record.
INSERT INTO pages (path, html_content) VALUES
('/index.html',
 '<html><head><title>Home</title></head><body><h1>Welcome!</h1><p>This page was served from MariaDB via the Pico 2 W cache.</p></body></html>')
ON DUPLICATE KEY UPDATE html_content = VALUES(html_content);


