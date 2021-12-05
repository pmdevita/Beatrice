import os
from pathlib import Path
import json

p = Path("cleaned text")
qa = Path("qa text")


dialogue = []

text_files = []
for root, dirs, files in os.walk(p):
    for file in files:
        if file.endswith(".json"):
            with open(os.path.join(root, file)) as f:
                text_files.append(json.load(f))


for text_file in text_files:
    for i, line in enumerate(text_file):
        if line["speaker"] == "Beatrice":
            contexted_line = []
            for j in range(7):
                contexted_line.append(text_file[i-j]["dialogue"] if (i-j) >= 0 else "")
            dialogue.append(contexted_line)

# QA Text
text_files = []
for root, dirs, files in os.walk(qa):
    for file in files:
        if file.endswith(".json"):
            with open(os.path.join(root, file)) as f:
                text_files.append(json.load(f))

for text_file in text_files:
    for i, line in enumerate(text_file):
        if line["speaker"] == "Beatrice":
            contexted_line = []
            for j in range(2):
                contexted_line.append(text_file[i-j]["dialogue"] if (i-j) >= 0 else "")
            dialogue.append(contexted_line)


print("dialogue lines", len(dialogue))

with open("beatrice.json", "w") as f:
    json.dump(dialogue, f, indent=4, sort_keys=True)