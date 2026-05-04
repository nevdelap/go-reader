#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["zopfli"]
# ///
#
# Converts a jmdict-eng-*.json.zip (from scriptin/jmdict-simplified) into the
# compact dict/jmdict-compact.json.gz used by the app at runtime.
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
#   pg — (optional) glosses from particle (prt), expression (exp), and auxiliary (aux/aux-v/aux-adj) senses

import json, os, glob, zipfile
from pathlib import Path
import zopfli.gzip  # type: ignore[import-not-found]

# JMdict POS tags that signal a grammar/particle sense suitable for pg/pg2.
# exp covers compound particles like により, として that JMdict tags as expressions.
# aux/aux-v/aux-adj covers auxiliary verbs like ない, た, だ, られる.
GRAMMAR_POS = {'prt', 'exp', 'aux', 'aux-v', 'aux-adj'}

def _merge(entry, key, items):
    existing = entry.get(key, [])
    seen = set(existing)
    for item in items:
        if item not in seen:
            existing.append(item)
            seen.add(item)
    entry[key] = existing

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

    # Collect glosses from grammar senses (pg is for disambiguation — words where g[0]
    # would be wrong in particle/auxiliary context; others fall back to g[0] at runtime).
    particle_glosses = list(dict.fromkeys(
        g['text']
        for sense in entry['sense']
        if GRAMMAR_POS.intersection(sense.get('partOfSpeech', []))
        for g in sense['gloss']
        if g['lang'] == 'eng'
    ))

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
            _merge(out[word], 'p', first_sense.get('partOfSpeech', []))
            if particle_glosses:
                _merge(out[word], 'pg', particle_glosses)
        else:
            # Uncommon entry skipped for g/p, but collect its grammar glosses.
            # If the common entry already has pg (competing senses, e.g. て/で), store
            # in pg2 so callers can distinguish. Otherwise merge into pg — no conflict.
            if particle_glosses:
                _merge(out[word], 'pg2' if 'pg' in out[word] else 'pg', particle_glosses)

data = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
print(f'Entries: {len(out)}, JSON size: {len(data.encode()) / 1024 / 1024:.1f}MB')

output = Path('dict') / 'jmdict-compact.json.gz'
output.parent.mkdir(exist_ok=True)

with output.open('wb') as f:
    f.write(zopfli.gzip.compress(data.encode('utf-8')))

print(f'Gzipped: {os.path.getsize(output) / 1024 / 1024:.1f}MB')
print(f'Done → {output}')
