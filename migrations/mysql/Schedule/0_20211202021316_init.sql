-- upgrade --
CREATE TABLE IF NOT EXISTS `schedule_alarms` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `channel` BIGINT NOT NULL,
    `time` DATETIME(6) NOT NULL,
    `message` LONGTEXT NOT NULL
) CHARACTER SET utf8mb4;
-- downgrade --
DROP TABLE IF EXISTS `schedule_alarms`;
