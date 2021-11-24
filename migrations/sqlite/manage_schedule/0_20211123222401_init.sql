-- upgrade --
CREATE TABLE IF NOT EXISTS "schedule_alarms" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "channel" BIGINT NOT NULL,
    "time" TIMESTAMP NOT NULL,
    "message" TEXT NOT NULL
);
-- downgrade --
DROP TABLE IF EXISTS "schedule_alarms";
