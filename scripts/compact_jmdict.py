#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["zopfli"]
# ///
#
# Converts a jmdict-eng-*.json.zip (from scriptin/jmdict-simplified) into the
# compact jmdict-compact.json.gz used by the app at runtime.
#
# Usage:
#   scripts/compact_jmdict.py
#
# Expects exactly one jmdict-eng-*.json.zip in the repo root (run from there).
# Normally run via scripts/update_jmdict_and_compact_repo.sh, but can be run directly
# after manually downloading the zip from:
#   https://github.com/scriptin/jmdict-simplified/releases
#
# Output format: { "word": {"p": ["pos", ...], "g": [["gloss", ...], ...], "pg": ["gloss", ...]}, ... }
#   p  — POS tags from the first English sense; merged across same-priority entries
#   g  — list of gloss groups, one per JMdict entry; within a group glosses are
#        joined with ", ", between groups with ";"
#   pg — (optional) glosses from particle senses only, for words that double as particles

import json, os, glob, zipfile
import zopfli.gzip  # type: ignore[import-not-found]

matches = sorted(glob.glob('jmdict-eng-*.json.zip'))
if not matches:
    raise FileNotFoundError("No jmdict-eng-*.json.zip found in current directory.")
source = matches[-1]
print(f"Loading {source}...")
with zipfile.ZipFile(source) as zf:
    d = json.load(zf.open(zf.namelist()[0]))

out = {}       # word → {p: pos_tags, g: glosses}
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

    is_common = any(k.get('common', False) for k in entry['kanji'] + entry['kana'])

    # Collect glosses from all particle-tagged senses in this JMdict entry
    particle_glosses = []
    seen_pg = set()
    for sense in entry['sense']:
        if 'prt' in sense.get('partOfSpeech', []):
            for g in sense['gloss']:
                if g['lang'] == 'eng' and g['text'] not in seen_pg:
                    particle_glosses.append(g['text'])
                    seen_pg.add(g['text'])

    for k in entry['kanji'] + entry['kana']:
        word = k['text']
        if word not in out or (is_common and not common.get(word, False)):
            # New entry wins outright (first seen, or common displacing uncommon)
            prev_pg = out.get(word, {}).get('pg')
            out[word] = {'p': list(first_sense.get('partOfSpeech', [])), 'g': [list(glosses)]}
            if particle_glosses:
                out[word]['pg'] = list(particle_glosses)
            elif prev_pg:
                out[word]['pg'] = prev_pg
            common[word] = is_common
        elif is_common == common.get(word, False):
            # Same priority: append glosses as a new group, merge POS tags
            if glosses not in out[word]['g']:
                out[word]['g'].append(list(glosses))
            existing_p = out[word]['p']
            for p in first_sense.get('partOfSpeech', []):
                if p not in existing_p:
                    existing_p.append(p)
            if particle_glosses:
                existing_pg = out[word].get('pg', [])
                seen = set(existing_pg)
                for pg in particle_glosses:
                    if pg not in seen:
                        existing_pg.append(pg)
                        seen.add(pg)
                out[word]['pg'] = existing_pg
        else:
            # Uncommon entry skipped for g/p, but collect its particle glosses in pg2
            # so callers can use them when the primary pg is for a different sense.
            if particle_glosses:
                existing_pg2 = out[word].get('pg2', [])
                seen = set(existing_pg2)
                for pg in particle_glosses:
                    if pg not in seen:
                        existing_pg2.append(pg)
                        seen.add(pg)
                out[word]['pg2'] = existing_pg2

data = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
print(f'Entries: {len(out)}, JSON size: {len(data.encode()) / 1024 / 1024:.1f}MB')

with open('jmdict-compact.json.gz', 'wb') as f:
    f.write(zopfli.gzip.compress(data.encode('utf-8')))

print(f'Gzipped: {os.path.getsize("jmdict-compact.json.gz") / 1024 / 1024:.1f}MB')
print('Done → jmdict-compact.json.gz')
