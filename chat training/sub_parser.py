from pathlib import Path
import json

file_path = Path("raw text/ep9.ass")
output_path = Path("cleaned text/ep9.json")

with open(file_path) as f:
    text = f.read()

text = text[text.find("[Events]"):]
text = text.split("\n")
text.pop(0)
text.pop(0)


def parse_line(line):
    if "," not in line:
        return None
    line_args = line.split(",")
    while len(line_args) > 10:
        line_args[len(line_args) - 2] += "," + line_args[len(line_args) - 1]
        line_args.pop(len(line_args) - 1)

    line_args[9] = line_args[9].replace("\\N", "")
    return line_args


def print_dialogue(line):
    print(f"{line[4]}: {line[9]}")


all_dialogue = []
last_speaker = None
dialogue = ""
for line in text:
    parsed_line = parse_line(line)
    if parsed_line:
        if parsed_line[4] == last_speaker or parsed_line[4] == "":
            dialogue += " " + parsed_line[9]
        else:
            if dialogue:
                all_dialogue.append({"speaker": last_speaker, "dialogue": dialogue})
            dialogue = parsed_line[9]
            last_speaker = parsed_line[4]

with open(output_path, "w") as f:
    json.dump(all_dialogue, f, indent=4, sort_keys=True)

