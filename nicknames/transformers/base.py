from string import ascii_lowercase


class BaseNickname:
    def __init__(self, cog):
        self.cog = cog

    async def async_init(self):
        pass

    async def transform_names(self, names: list[tuple[str, int]]) -> list[tuple[str, int]]:
        raise NotImplementedError


def sanitize_word(word: str):
    w = word.lower().replace(" ", "")
    if not w.isalpha():
        indexes = []
        for i, c in enumerate(w):
            if not c.isalpha():
                indexes.append(i)
        indexes.reverse()
        for i in indexes:
            w = w[:i] + w[i + 1:]
    return w


class ScramblerNickname(BaseNickname):
    async def async_init(self):
        self.table = {}
        await self.setup()

    async def get_dictionary(self) -> list[str]:
        raise NotImplementedError

    async def setup(self):
        dictionary = await self.get_dictionary()
        for word in dictionary:
            key = vect_to_int(word_to_vect(sanitize_word(word)))
            if key in self.table:
                self.table[key].append(word)
            else:
                self.table[key] = [word]

    async def transform_names(self, names: list[tuple[str, int]]) -> list[tuple[str, int]]:
        new_names = []
        for name in names:
            name_choices = self.unscramble(name[0], add_letters=True)
            new_names.append((name_choices[0][0][0], name[1]))
        return new_names

    def unscramble(self, word, limit=5, add_letters=False):
        options = set()
        checked = set()
        sanitized_word = sanitize_word(word)
        word_int = vect_to_int(word_to_vect(word))
        # Add the exact matches
        for i in self.table.get(word_int, []):
            options.add(i)
        # If we don't have enough, keep going
        if len(options) < limit:
            # Remove letters and check for matches
            self.unscramble_search(sanitized_word, options, limit, checked)
            # If we don't have enough, keep going
            if len(options) < limit:
                # Add letters until we get enough matches
                if add_letters:
                    left = 1
                    while len(options) < limit:
                        # print(f"Trying {left} extra letter")
                        self.add_letters(word.lower(), left, options, 1000, checked)
                        left += 1

        final_options = list(options)
        final_options.sort(key=lambda x: len(x[0]), reverse=True)
        return [(i, len(i[0])) for i in final_options]

    def add_letters(self, word, left, options, limit, checked):
        for letter in ascii_lowercase:
            new_word = word + letter
            if left <= 1:
                self.unscramble_search(new_word, options, limit, checked, extra=new_word)
            else:
                self.add_letters(new_word, left - 1, options, limit, checked)

    def unscramble_search(self, word, options, limit, checked, extra=None):
        if word == "":
            return
        new_words = []
        # print("Trying", word)
        for i in range(len(word)):
            new_word = word[:i] + word[i + 1:]
            word_int = vect_to_int(word_to_vect(new_word))
            if word_int not in checked:
                new_words.append((word_int, new_word))
        for word_int, new_word in new_words:
            for i in self.table.get(word_int, []):
                if extra:
                    options.add((i, extra))
                else:
                    options.add((i,))
            checked.add(word_int)
            if len(options) >= limit:
                return
        for word_int, new_word in new_words:
            self.unscramble_search(new_word, options, limit, checked, extra)
            if len(options) >= limit:
                return


def word_to_vect(word):
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
               'v', 'w', 'x', 'y', 'z']
    v = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    w = word.lower()
    wl = list(w)
    for i in range(0, len(wl)):
        if wl[i] in letters:
            ind = letters.index(wl[i])
            v[ind] += 1
    return v


def vect_to_int(vector):
    pv = 0
    f = 0
    for scalar in vector:
        f += scalar * (2 ** pv)
        pv += 4
    return f


