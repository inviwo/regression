import pathlib
import sys
import os
import json

from bs4 import BeautifulSoup


def findDuplicates(lines):
    duplicates = {}
    for line in lines:
        try:
            (_, _, sha, path) = line.strip().split(maxsplit=3)
            if sha in duplicates:
                duplicates[sha].append(path)
            else:
                duplicates[sha] = [path]
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
        key = f"{reportDir}/{src}"
        if key in orgMap:
            item["src"] = f"/regression/{orgMap[key]}"


def processReport(reportFile:pathlib.Path, orgMap):
    reportDir = reportFile.parent

    with open(reportFile) as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    replaceSource(soup.find_all('img'), orgMap, reportDir)
    replaceSource(soup.find_all('script'), orgMap, reportDir)

    with open(reportFile, 'w') as f:
        f.write(str(soup))


def processJsons(reportFile:pathlib.Path, orgMap):
    reportDir = reportFile.parent

    # read json from report
    with open(reportFile) as f:
        report = json.load(f)

    for name, result in report.items():
        [_, testDir] = result['outputdir'].split(f"/{name}/")
       
        updated = {}
        for refImg in result['images']['refs']:
            key = f"{reportDir.as_posix()}/{name}/{testDir}/imgref/{refImg}"
            if key in orgMap:
                updated[refImg] = f"https://inviwo.org/regression/{orgMap[key]}"
            else:
                updated[refImg] = f"https://inviwo.org/regression/{key}"
        result['images']['refs-map'] = updated
                      
        updated = {}
        for testImg in result['images']['imgs']:
            key = f"{reportDir.as_posix()}/{name}/{testDir}/imgtest/{testImg}"
            if key in orgMap:
                updated[testImg] = f"https://inviwo.org/regression/{orgMap[key]}"
            else:
                updated[testImg] = f"https://inviwo.org/regression/{key}"
        result['images']['imgs-map'] = updated

    with open(reportFile, 'w') as f:
        json.dump(report, f, indent=4)


def deleteDuplicates(duplicates : dict[str, list[str]]):
    for (first, *rest) in duplicates.values():
        if first.endswith((".png", ".js")):
            for item in rest:
                pathlib.Path(item).unlink()

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

    jsonReports = list(root.glob("**/report.json"))
    print("::group::Process json reports", flush=True)
    for (i, jsonReport) in enumerate(jsonReports):
        print(f"({i}/{len(jsonReports)}) Processing {jsonReport}", flush=True)
        processJsons(jsonReport, orgMap)
    print("::endgroup::", flush=True)

    htmlReports = list(root.glob("**/report*.html"))

    print("::group::Process html reports", flush=True)
    for (i, htmlReport) in enumerate(htmlReports):
        print(f"({i}/{len(htmlReports)}) Processing {htmlReport}", flush=True)
        processReport(htmlReport, orgMap)
    print("::endgroup::", flush=True)


    print(f"::group::Removing duplicates", flush=True)
    deleteDuplicates(duplicates)
    print("::endgroup::", flush=True)