import json
import sys

src = sys.argv[1]

with open(src, 'r') as f:
    raw = json.load(f)
    f.close()

with open(src, 'w') as f:
    f.write(json.dumps(raw, indent=2, sort_keys=True))
    f.close()
