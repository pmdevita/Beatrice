from pathlib import Path
import json
import re
import os

SENTENCE_END = re.compile("(\w[.!?]+(?!\") ?)")

p = Path("substojson")
out_folder = Path("cleaned text")

text_files = []
for root, dirs, files in os.walk(p):
    for file in files:
        if file.endswith(".json"):
            file_path = os.path.join(root, file)

            with open(file_path) as f:
                text = json.load(f)

            final = []

            for line in text:
                indexes = []
                # Don't separate Beatrice's lines
                if line["speaker"] != "Beatrice":
                    for i in SENTENCE_END.finditer(line["dialogue"]):
                        indexes.append(i.end())
                if len(indexes) > 1:
                    sentences = []
                    last_index = 0
                    for i in indexes:
                        sentences.append(line["dialogue"][last_index:i].strip())
                        last_index = i
                    for sentence in sentences:
                        final.append({"dialogue": sentence, "speaker": line["speaker"]})
                else:
                    final.append(line)

            with open(os.path.join(out_folder, file), "w") as f:
                json.dump(final, f, indent=4, sort_keys=True)
