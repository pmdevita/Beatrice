-- upgrade --
CREATE TABLE IF NOT EXISTS `gregchannels` (
    `guild_id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `channel_id` BIGINT NOT NULL
) CHARACTER SET utf8mb4;;
CREATE TABLE IF NOT EXISTS `gregoriginalperms` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `channel_id` BIGINT NOT NULL,
    `role_id` BIGINT NOT NULL
) CHARACTER SET utf8mb4;-- downgrade --
DROP TABLE IF EXISTS `gregchannels`;
DROP TABLE IF EXISTS `gregoriginalperms`;
