-- Run this once against the existing MySQL database before starting the HW7 API.
-- Existing users keep their password hashes. Their email address becomes their
-- username and their initial role is reader.

ALTER TABLE users
    ADD COLUMN username VARCHAR(255) NULL AFTER id;

UPDATE users
SET username = email
WHERE username IS NULL;

ALTER TABLE users
    MODIFY COLUMN username VARCHAR(255) NOT NULL,
    ADD UNIQUE INDEX uq_users_username (username),
    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'reader' AFTER password_hash;
