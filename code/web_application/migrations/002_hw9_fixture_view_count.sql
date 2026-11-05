-- Run this once against the existing MySQL database before starting the HW9 API.
ALTER TABLE fixtures
    ADD COLUMN view_count INT NOT NULL DEFAULT 0 AFTER available_slots;
