-- upgrade --
CREATE TABLE IF NOT EXISTS `nicknamegroup` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `group_name` VARCHAR(20) NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `nickname` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `nickname` VARCHAR(32) NOT NULL,
    `group_id` INT NOT NULL,
    CONSTRAINT `fk_nickname_nickname_8081c88f` FOREIGN KEY (`group_id`) REFERENCES `nicknamegroup` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;;
-- downgrade --
DROP TABLE IF EXISTS `nickname`;
DROP TABLE IF EXISTS `nicknamegroup`;
