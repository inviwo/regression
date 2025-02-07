import pathlib
import sys
import os

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
        relpath = pathlib.Path(os.path.relpath(first, item.parent))
        item.symlink_to(relpath)

    if len(rest) > 0:
        print(f"Created {len(rest)} symlinks to {first}")