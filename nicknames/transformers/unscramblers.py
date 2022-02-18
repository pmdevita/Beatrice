from .base import ScramblerNickname


class Pokemon(ScramblerNickname):
    async def get_dictionary(self) -> list[str]:
        pokemon = []
        url = "https://pokeapi.co/api/v2/pokemon-species/?limit=50"
        while True:
            async with self.cog.discord.session.get(url) as response:
                j = await response.json()
            for i in j["results"]:
                pokemon.append(i["name"])
            if j["next"]:
                url = j["next"]
            else:
                break
        return pokemon

    async def transform_names(self, names: list[tuple[str, int]]) -> list[tuple[str, int]]:
        new_names = await super(Pokemon, self).transform_names(names)
        newer_names = []
        for i in new_names:
            async with self.cog.discord.session.get(f"https://pokeapi.co/api/v2/pokemon-species/{i[0]}/") as response:
                j = await response.json()
                for k in j["names"]:
                    if k["language"]["name"] == "en":
                        newer_names.append((k["name"], i[1]))
                        break
        return newer_names


