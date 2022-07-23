-- upgrade --
CREATE TABLE IF NOT EXISTS `splatgear_brands` (
    `id` INT NOT NULL PRIMARY KEY,
    `name` VARCHAR(30) NOT NULL
) CHARACTER SET utf8mb4;;
CREATE TABLE IF NOT EXISTS `splatgear_gear` (
    `_pid` VARCHAR(15) NOT NULL  PRIMARY KEY,
    `id` INT NOT NULL,
    `type` VARCHAR(7) NOT NULL  COMMENT 'Head: head\nShoes: shoes\nClothes: clothes',
    `name` VARCHAR(30) NOT NULL
) CHARACTER SET utf8mb4;;
CREATE TABLE IF NOT EXISTS `splatgear_skills` (
    `id` INT NOT NULL PRIMARY KEY,
    `name` VARCHAR(30) NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `splatgear_requests` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user` BIGINT NOT NULL,
    `last_messaged` DATETIME(6) NOT NULL,
    `brand_id` INT,
    `gear_id` VARCHAR(15),
    `skill_id` INT,
    CONSTRAINT `fk_splatgea_splatgea_71b11f45` FOREIGN KEY (`brand_id`) REFERENCES `splatgear_brands` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_splatgea_splatgea_2b7bda9a` FOREIGN KEY (`gear_id`) REFERENCES `splatgear_gear` (`_pid`) ON DELETE CASCADE,
    CONSTRAINT `fk_splatgea_splatgea_b10a3428` FOREIGN KEY (`skill_id`) REFERENCES `splatgear_skills` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;;
-- downgrade --
DROP TABLE IF EXISTS `splatgear_requests`;
DROP TABLE IF EXISTS `splatgear_brands`;
DROP TABLE IF EXISTS `splatgear_gear`;
DROP TABLE IF EXISTS `splatgear_skills`;
