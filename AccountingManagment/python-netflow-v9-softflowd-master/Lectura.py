import gzip
import json

with gzip.open("flows.gz", "rt") as gzipped:
    # "for line in" lazy-loads all lines in the file
    i = "Linea: "
    for line in gzipped:
        entry = json.loads(line)
        print(entry)