from alive_progress import alive_bar
import json
from string import ascii_lowercase


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


def words_to_dict(words):
    dictionary = {}
    with alive_bar(len(words), bar="smooth") as bar:
        for i, word in enumerate(words):
            word_int = vect_to_int(word_to_vect(word))
            if word_int in dictionary:
                dictionary[word_int].append(word)
            else:
                dictionary[word_int] = [word]
            bar()
    return dictionary


class Unscrambler:
    def __init__(self, dictionary="words.json"):
        with open(dictionary, 'r') as f:
            self.words = json.load(f)

    def unscramble(self, word, limit=5, add_letters=False):
        options = set()
        checked = set()
        word_int = vect_to_int(word_to_vect(word))
        for i in self.words.get(str(word_int), []):
            options.add(i)
        if len(options) >= limit:
            return options
        with alive_bar() as bar:
            self.unscramble_search(word.lower(), options, limit, checked, bar)
        if len(options) < limit and add_letters:
            left = 1
            while len(options) < limit:
                print(f"Trying {left} extra letter")
                with alive_bar() as bar:
                    self.add_letters(word.lower(), left, options, limit, checked, bar)
                left += 1

        final_options = list(options)
        final_options.sort(key=lambda x: len(x[0]), reverse=True)
        return [(i, len(i[0])) for i in final_options]

    def add_letters(self, word, left, options, limit, checked, bar):
        for letter in ascii_lowercase:
            new_word = word + letter
            if left <= 1:
                self.unscramble_search(new_word, options, limit, checked, bar, extra=new_word)
            else:
                self.add_letters(new_word, left - 1, options, limit, checked, bar)

    def unscramble_search(self, word, options, limit, checked, bar, extra=None):
        if word == "":
            return
        new_words = []
        # print("Trying", word)
        for i in range(len(word)):
            new_word = word[:i] + word[i + 1:]
            if new_word not in checked:
                new_words.append(new_word)
        for new_word in new_words:
            word_int = vect_to_int(word_to_vect(new_word))
            for i in self.words.get(str(word_int), []):
                if extra:
                    options.add((i, extra))
                else:
                    options.add((i,))
            checked.add(new_word)
            bar()
            if len(options) >= limit:
                return
        for new_word in new_words:
            self.unscramble_search(new_word, options, limit, checked, bar, extra)
            if len(options) >= limit:
                return


if __name__ == '__main__':
    # with open("words_alpha.txt", 'r') as f:
    #     words = f.read().split("\n")
    # dictionary = words_to_dict(words)
    # with open("words.json", 'w') as f:
    #     json.dump(dictionary, f)
    # print("Done!")
    u = Unscrambler("mc_blocks.json")
    print(u.unscramble("samformac", add_letters=True, limit=12))
    # print(u.unscramble("morphactin"))
