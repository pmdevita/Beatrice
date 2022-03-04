from pathlib import Path
import json

file_path = Path("raw text/interview.txt")
output_path = Path("qa text/interview.json")

with open(file_path) as f:
    text = f.read().split('\n')

is_beatrice = False
all_dialogue = []
for line in text:
    if line:
        all_dialogue.append({"speaker": "Beatrice" if is_beatrice else "Subaru", "dialogue": line})
        is_beatrice = not is_beatrice

with open(output_path, "w") as f:
    json.dump(all_dialogue, f, indent=4, sort_keys=True)

