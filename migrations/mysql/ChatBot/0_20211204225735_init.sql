-- upgrade --
CREATE TABLE IF NOT EXISTS `chat_threads` (
    `thread_id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `history` LONGTEXT NOT NULL
) CHARACTER SET utf8mb4;
-- downgrade --
DROP TABLE IF EXISTS `chat_threads`;
