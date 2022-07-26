from nextcord_ormar import AppModel, OrmarApp
import ormar

MetaModel = OrmarApp.create_app("nicknames")


class NicknameGroup(AppModel):
    class Meta(MetaModel):
        tablename = "nickname"

    id = ormar.Integer(primary_key=True)
    group_name = ormar.String(max_length=20)


class Nickname(AppModel):
    class Meta(MetaModel):
        tablename = "nicknamegroup"

    id = ormar.Integer(primary_key=True)
    # TODO: Add Delete cascade
    group = ormar.ForeignKey(NicknameGroup)
    user_id = ormar.BigInteger()
    nickname = ormar.String(max_length=32)

