-- upgrade --
CREATE TABLE IF NOT EXISTS "nickname" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "nickname" VARCHAR(32) NOT NULL,
    "group_id" INT NOT NULL REFERENCES "nicknamegroup" ("id") ON DELETE CASCADE
);;
CREATE TABLE IF NOT EXISTS "nicknamegroup" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "group_name" VARCHAR(20) NOT NULL
);-- downgrade --
DROP TABLE IF EXISTS "nickname";
DROP TABLE IF EXISTS "nicknamegroup";
