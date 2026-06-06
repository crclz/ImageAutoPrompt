import random
import re
import sys

rate = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5

# Dynamically read artists from library/artists.md
artists = []
with open("./library/artists.md", encoding="utf-8") as fp:
    for line in fp:
        if line.startswith("## artist:"):
            name = line.removeprefix("## artist:").rstrip("\n\r")
            name = re.sub(r"\s*//.*", "", name).strip()
            if name:
                artists.append(name)

random.seed()
random.shuffle(artists)

remaining = [a for a in artists if random.random() >= rate]
dropped = [a for a in artists if a not in remaining]

print(f"Total artists: {len(artists)}")
print(f"Remaining: {len(remaining)}")
print(f"Dropped: {len(dropped)}")
print()
print("=== REMAINING ARTISTS ===")
for i, a in enumerate(remaining):
    print(f"{i+1}. artist:{a}")
print()
print("=== DROPPED ARTISTS ===")
for i, a in enumerate(dropped):
    print(f"{i+1}. artist:{a}")
