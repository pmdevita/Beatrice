import ormar
from nextcord_ormar import OrmarApp, AppModel

MetaModel = OrmarApp.create_app("scrum")


class ScrumGuild(AppModel):
    class Meta(MetaModel):
        tablename = "scrum_scrumservers"

    guild = ormar.BigInteger(primary_key=True)
    channel = ormar.BigInteger()


class ScrumDay(AppModel):
    class Meta(MetaModel):
        tablename = "scrum_scrumday"
    id = ormar.Integer(primary_key=True, autoincrement=True)
    day = ormar.Date()
    guild = ormar.ForeignKey(ScrumGuild, related_name="days")
    post_id = ormar.BigInteger(nullable=True)
    ignored = ormar.Boolean(default=False)


class ScrumEntry(AppModel):
    class Meta(MetaModel):
        tablename = "scrum_scrumentry"

    id = ormar.Integer(primary_key=True, autoincrement=True)
    day = ormar.ForeignKey(ScrumDay, related_name="entries")
    user = ormar.BigInteger()
    previous = ormar.Text()
    next = ormar.Text()
    blockers = ormar.Text()
