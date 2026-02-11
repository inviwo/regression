import pathlib
import sys
import os

from bs4 import BeautifulSoup


def findDuplicates(lines):
    duplicates = {}
    for line in lines:
        try:
            (_, _, sha, path) = line.strip().split(maxsplit=3)
            if sha in duplicates:
                duplicates[sha].append(pathlib.Path(path))
            else:
                duplicates[sha] = [pathlib.Path(path)]
        except Exception as e:
            print(f"Error processing line: {line}", flush=True)
            print(e, flush=True)
    return duplicates


def fileToOrg(duplicates):
    orgMap = {}
    for (first, *rest) in duplicates.values():
        for item in rest:
            orgMap[item] = first
    return orgMap


def replaceSource(items, orgMap, reportDir):
    for item in items:
        src = item["src"]
        if reportDir / src in orgMap:
            org = orgMap[reportDir/src]
            item["src"] = f"/regression/{org}"


def processReport(report:pathlib.Path, orgMap):
    reportDir = report.parent

    with open(report) as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    replaceSource(soup.find_all('img'), orgMap, reportDir)
    replaceSource(soup.find_all('script'), orgMap, reportDir)

    with open(report, 'w') as f:
        f.write(str(soup))


def deleteDuplicates(duplicates):
    for (first, *rest) in duplicates.values():
        if first.suffix in [".png", ".js"]:
            for item in rest:
                item.unlink()

            if len(rest) > 0:
                print(f"Removed {len(rest)} duplicates of {first}", flush=True)


if __name__ == "__main__":
    print(f"Deduplicating", flush=True)

    root = pathlib.Path(sys.argv[2])
    lines = open(sys.argv[1]).readlines()

    print(f"Found: {len(lines)} files", flush=True)

    duplicates = findDuplicates(lines)

    print(f"Found {len(duplicates)} unique files", flush=True)

    orgMap = fileToOrg(duplicates)

    reports = list(root.glob("**/report*.html"))

    print("::group::Process reports", flush=True)
    for (i, report) in enumerate(reports):
        print(f"({i}/{len(reports)}) Processing {report}", flush=True)
        processReport(report, orgMap)
    print("::endgroup::", flush=True)

    print(f"::group::Removing duplicates", flush=True)
    deleteDuplicates(duplicates)
    print("::endgroup::", flush=True)