-- upgrade --
CREATE TABLE IF NOT EXISTS "splatgear_brands" (
    "id" INTEGER PRIMARY KEY NOT NULL,
    "name" VARCHAR(30) NOT NULL
);;
CREATE TABLE IF NOT EXISTS "splatgear_gear" (
    "_pid" VARCHAR(15) NOT NULL  PRIMARY KEY,
    "id" INT NOT NULL,
    "type" VARCHAR(7) NOT NULL  /* Head: head\nShoes: shoes\nClothes: clothes */,
    "name" VARCHAR(30) NOT NULL
);;
CREATE TABLE IF NOT EXISTS "splatgear_skills" (
    "id" INTEGER PRIMARY KEY NOT NULL,
    "name" VARCHAR(30) NOT NULL
);
CREATE TABLE IF NOT EXISTS "splatgear_requests" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "user" BIGINT NOT NULL,
    "last_messaged" TIMESTAMP NOT NULL,
    "brand_id" INT REFERENCES "splatgear_brands" ("id") ON DELETE CASCADE,
    "gear_id" VARCHAR(15) REFERENCES "splatgear_gear" ("_pid") ON DELETE CASCADE,
    "skill_id" INT REFERENCES "splatgear_skills" ("id") ON DELETE CASCADE
);;
-- downgrade --
DROP TABLE IF EXISTS "splatgear_requests";
DROP TABLE IF EXISTS "splatgear_brands";
DROP TABLE IF EXISTS "splatgear_gear";
DROP TABLE IF EXISTS "splatgear_skills";
