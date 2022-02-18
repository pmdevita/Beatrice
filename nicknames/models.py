from tortoise import fields, models


class NicknameGroup(models.Model):
    id = fields.IntField(pk=True)
    group_name = fields.CharField(max_length=20)


class Nickname(models.Model):
    id = fields.IntField(pk=True)
    group = fields.ForeignKeyField("Nicknames.NicknameGroup", on_delete=fields.CASCADE)
    user_id = fields.BigIntField()
    nickname = fields.CharField(max_length=32)

