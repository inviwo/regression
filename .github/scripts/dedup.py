import pathlib
import sys

lines = open(sys.argv[1]).readlines()

duplicates = {}
for line in lines:
    (_, _, sha, path) = line.split()
    if sha in duplicates:
        duplicates[sha].append(pathlib.Path(path))
    else:
        duplicates[sha] = [pathlib.Path(path)]

for (first, *rest) in duplicates.values():
    for item in rest:
        item.unlink()
        item.symlink_to(first)

    print(f"Created {len(rest)} symlinks to {first}")