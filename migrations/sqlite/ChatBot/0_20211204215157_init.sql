-- upgrade --
CREATE TABLE IF NOT EXISTS "chat_threads" (
    "thread_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "history" TEXT NOT NULL
);
-- downgrade --
DROP TABLE IF EXISTS "chat_threads";
