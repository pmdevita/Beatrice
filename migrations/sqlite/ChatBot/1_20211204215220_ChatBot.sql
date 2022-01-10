-- upgrade --
ALTER TABLE "chat_threads" ADD "another_field" BIGINT;
-- downgrade --
ALTER TABLE "chat_threads" DROP COLUMN "another_field";
