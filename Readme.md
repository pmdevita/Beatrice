# Beatrice

This is Beatrice, a custom Discord bot written for my Discord server. She's named after the character Beatrice from 
Re:Zero and some of her responses are written in-character. Just as Re:Zero Beatrice guards the forbidden library, this 
Beatrice guards my server (or something lol).

Beatrice has a number of notable technologies that were developed along with her, including:

- [nextcord-tortoise](https://github.com/pmdevita/nextcord-tortoise), Easy and quick Django-like database integration 
for Nextcord. Most apps under Beatrice had their database code written in minutes or less with this tool.

- ![Efficient async timers](util/timer.py) for apps to schedule events with optional repeats, using native DateTime and 
TimeDelta objects.

- Beatrice Chat, a neural network fine-tuned from Microsoft's DialoGPT to talk like Beatrice.

The full set of apps running under Beatrice include:

- Beatrice Chat
- SplatGear, a service to alert you when gear you want is available on Splatoon 2's SplatNet app
- Schedule, a service to schedule Beatrice to alert you at a specific time
- Nicknames, a service to save and load a server's nicknames and apply mass changes to them, such as randomly 
shuffling everyone's usernames or changing them to the closest anagram of Pokémon species or Minecraft block.
- A terminal console for editing or viewing info for apps or doing some difficult on-the-fly debugging
- A hi command, ping command, and some server specific clean up tasks.

