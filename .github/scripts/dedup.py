import pathlib
import sys
import os

from bs4 import BeautifulSoup

lines = open(sys.argv[1]).readlines()

print(f"Deduplicating", flush=True)

duplicates = {}
for line in lines:
    (_, _, sha, path) = line.split()
    if sha in duplicates:
        duplicates[sha].append(pathlib.Path(path))
    else:
        duplicates[sha] = [pathlib.Path(path)]

print(f"Found {len(duplicates)} unique files out of {len(lines)} files", flush=True)

orgMap = {}
for (first, *rest) in duplicates.values():
    for item in rest:
        orgMap[item] = first

def replaceSource(items):
    for item in items:
        src = item["src"]
        if reportDir / src in orgMap:
            org = orgMap[reportDir/src]
            item["src"] = f"/regression/{org}"


root = pathlib.Path(sys.argv[2])
reports = list(root.glob("**/report*.html"))

print("::group::Process reports", flush=True)
for report in reports:
    print(f"Processing {report}", flush=True)
    reportDir = report.parent

    with open(report) as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')

    replaceSource(soup.find_all('img'))
    replaceSource(soup.find_all('script'))

    with open(report, 'w') as f:
        f.write(str(soup))
print("::endgroup::", flush=True)

print(f"::group::Removing duplicates", flush=True)
for (first, *rest) in duplicates.values():
    if first.suffix in [".png", ".js"]:
        for item in rest:
            item.unlink()

        if len(rest) > 0:
            print(f"Removed {len(rest)} duplicates of {first}", flush=True)
print("::endgroup::", flush=True)