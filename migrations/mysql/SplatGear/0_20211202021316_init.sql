-- upgrade --
CREATE TABLE IF NOT EXISTS `splatgear_requests` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user` BIGINT NOT NULL,
    `gear_type` INT,
    `gear_id` INT,
    `brand_id` INT,
    `skill_id` INT,
    `last_messaged` DATETIME(6) NOT NULL
) CHARACTER SET utf8mb4;
-- downgrade --
DROP TABLE IF EXISTS `splatgear_requests`;
