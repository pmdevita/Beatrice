import datetime

import nextcord
from .models import *


class ScrumDayView(nextcord.ui.View):
    def __init__(self, channel: nextcord.TextChannel, day: ScrumDay):
        self.day = day
        self.channel = channel
        super().__init__(timeout=None)

        self.entry_button = nextcord.ui.Button(label="Daily Report", style=nextcord.ButtonStyle.green)
        self.entry_button.callback = self.report_button
        self.add_item(self.entry_button)

        self.ignore_button = nextcord.ui.Button(label="Ignore Today", style=nextcord.ButtonStyle.grey)
        self.ignore_button.callback = self.ignore_confirmation
        self.add_item(self.ignore_button)

    @classmethod
    async def send(cls, channel: nextcord.TextChannel, day: ScrumDay):
        data = await cls.format_text(channel.guild, day)
        view = cls(channel, day)
        return await channel.send(view=view, **data), view

    @staticmethod
    async def format_text(guild: nextcord.Guild, day: ScrumDay):
        # await day.load()
        await day.load_all()
        # await day.entries.load()
        # print(day)
        text = ""
        embed = nextcord.Embed()
        if len(day.entries):
            for entry in day.entries:
                # await entry.load()
                user = guild.get_member(entry.user)
                embed.add_field(name=user.display_name, value=f"Previous: {entry.previous}\nNext: {entry.next}\n"
                                                              f"Blockers: {entry.blockers}\n")
        else:
            text += "No entries yet. Hit the Daily Report button below!"
            embed = None
        text = f"Scrum Report: {day.day.strftime('%A, %b %-d')}\n" + text
        return {"content": text, "embed": embed}

    async def report_button(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(ScrumReportModal(self))

    async def ignore_confirmation(self, interaction: nextcord.Interaction):
        self.remove_item(self.ignore_button)
        self.ignore_button = nextcord.ui.Button(label="Are you sure? (Yes)", style=nextcord.ButtonStyle.grey)
        self.ignore_button.callback = self.ignore_today
        self.add_item(self.ignore_button)

        self.cancel_button = nextcord.ui.Button(label="(No)", style=nextcord.ButtonStyle.grey)
        self.cancel_button.callback = self.cancel_ignore
        self.add_item(self.cancel_button)

        await interaction.edit(view=self)

    async def ignore_today(self, interaction: nextcord.Interaction):
        await self.day.update(ignored=True)
        await self.day.load()
        message = await self.channel.fetch_message(self.day.post_id)
        await message.delete()

    async def cancel_ignore(self, interaction: nextcord.Interaction):
        self.remove_item(self.ignore_button)
        self.remove_item(self.cancel_button)
        self.ignore_button = nextcord.ui.Button(label="Ignore Today", style=nextcord.ButtonStyle.grey)
        self.ignore_button.callback = self.ignore_confirmation
        self.add_item(self.ignore_button)
        await interaction.edit(view=self)


class ScrumReportModal(nextcord.ui.Modal):
    def __init__(self, parent: ScrumDayView):
        self.parent = parent
        super().__init__("Scrum Daily Report")

        self.previous_text = nextcord.ui.TextInput(
            label="Previous",
            min_length=2,
            max_length=150
        )
        self.add_item(self.previous_text)

        self.next_text = nextcord.ui.TextInput(
            label="Next",
            min_length=2,
            max_length=150
        )
        self.add_item(self.next_text)

        self.blockers_text = nextcord.ui.TextInput(
            label="Blockers",
            min_length=2,
            max_length=150
        )
        self.add_item(self.blockers_text)

    async def callback(self, interaction: nextcord.Interaction):
        entry = await ScrumEntry.objects.get_or_none(day=self.parent.day, user=interaction.user.id)
        if entry is None:
            await ScrumEntry.objects.create(day=self.parent.day, user=interaction.user.id,
                                            previous=self.previous_text.value, next=self.next_text.value,
                                            blockers=self.blockers_text.value)
        else:
            await entry.update(previous=self.previous_text.value, next=self.next_text.value,
                               blockers=self.blockers_text.value)
        data = await self.parent.format_text(self.parent.channel.guild, self.parent.day)
        await interaction.edit(**data)



