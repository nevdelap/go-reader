#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# ///

import json, gzip, os, glob

matches = sorted(glob.glob('jmdict-eng-*.json'))
if not matches:
    raise FileNotFoundError("No jmdict-eng-*.json file found in current directory.")
source = matches[-1]
print(f"Loading {source}...")

with open(source) as f:
    d = json.load(f)

out = {}       # word → glosses
common = {}    # word → bool (is this entry marked common?)

for entry in d['words']:
    first_sense = next(
        (s for s in entry['sense'] if any(g['lang'] == 'eng' for g in s['gloss'])),
        None
    )
    if not first_sense:
        continue

    glosses = [g['text'] for g in first_sense['gloss'] if g['lang'] == 'eng']
    if not glosses:
        continue

    val = glosses[:2]
    is_common = any(k.get('common', False) for k in entry['kanji'] + entry['kana'])

    for k in entry['kanji'] + entry['kana']:
        word = k['text']
        # Only overwrite if this entry is common and the existing one isn't
        if word not in out or (is_common and not common.get(word, False)):
            out[word] = val
            common[word] = is_common

data = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
print(f'Entries: {len(out)}, JSON size: {len(data.encode()) / 1024 / 1024:.1f}MB')

with gzip.open('jmdict-compact.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
    f.write(data)

print(f'Gzipped: {os.path.getsize("jmdict-compact.json.gz") / 1024 / 1024:.1f}MB')
print('Done → jmdict-compact.json.gz')
