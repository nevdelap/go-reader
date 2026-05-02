// Tests for lookupWord, lookupParticle, and their fallbacks.
// Functions are inlined from index.html — keep in sync if those change.

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { gunzipSync } = require('node:zlib');
const { join } = require('node:path');

// ── Functions under test (inlined from index.html) ───────────────────────────

function toHiragana(str) {
  return (str || '').replace(/[ァ-ヺ]/g, c =>
    String.fromCharCode(c.charCodeAt(0) - 0x60)
  );
}

function stripNonJapanese(text) {
  return text
    .replace(/[^　-〿぀-ゟ゠-ヿ一-鿿㐀-䶿＀-￯「」『』【】・ー―—\n]/g, '').trim();
}

async function textToHash(text) {
  const bytes = new TextEncoder().encode(text);
  const cs = new CompressionStream('deflate-raw');
  const writer = cs.writable.getWriter();
  writer.write(bytes);
  writer.close();
  const buf = await new Response(cs.readable).arrayBuffer();
  const binary = Array.from(new Uint8Array(buf), b => String.fromCharCode(b)).join('');
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

async function hashToText(encoded) {
  const binary = atob(encoded.replace(/-/g, '+').replace(/_/g, '/'));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const ds = new DecompressionStream('deflate-raw');
  const writer = ds.writable.getWriter();
  writer.write(bytes);
  writer.close();
  return new Response(ds.readable).text();
}

const JMDICT_POS_MAP = {
  'n': 'noun', 'n-pref': 'prefix', 'n-suf': 'suffix',
  'adv': 'adverb', 'adv-to': 'adverb',
  'prt': 'particle',
  'conj': 'conjunction',
  'int': 'interjection',
  'pref': 'prefix',
  'suf': 'suffix',
  'aux': 'auxiliary', 'aux-v': 'auxiliary verb', 'aux-adj': 'auxiliary adjective',
  'ctr': 'counter',
  'pn': 'pronoun',
  'num': 'numeral',
  'exp': 'expression',
  'cop': 'copula',
};

function jmdictPOS(tags) {
  if (!tags || !tags.length) return [];
  const seen = new Set();
  const labels = [];
  for (const tag of tags) {
    let label;
    if (tag.startsWith('v')) label = 'verb';
    else if (tag.startsWith('adj')) label = 'adjective';
    else label = JMDICT_POS_MAP[tag] || null;
    if (label && !seen.has(label)) { seen.add(label); labels.push(label); }
  }
  return labels;
}

const IMPERATIVE_E_TO_U = {え:'う',け:'く',げ:'ぐ',せ:'す',て:'つ',ね:'ぬ',べ:'ぶ',め:'む',れ:'る'};

let jmdict = null;

function lookupParticle(token) {
  if (!jmdict) return null;
  // て and で as conjunctive particles: the JMdict "common" entry for て is the quoting
  // particle (って), whose glosses ("you said, he said") win and fill pg — wrong for 接続助詞 use.
  if (token.pos_detail_1 === '接続助詞' &&
      (token.surface_form === 'て' || token.surface_form === 'で')) return null;
  const base = token.basic_form && token.basic_form !== '*' ? token.basic_form : token.surface_form;
  const entry = jmdict[base] || jmdict[token.surface_form];
  if (!entry || !entry.pg) return null;
  return entry.pg.slice(0, 3).join(', ');
}

function lookupWord(surface, basicForm) {
  if (!jmdict) return null;
  const candidates = (basicForm && basicForm !== '*' && basicForm !== surface)
    ? [basicForm, surface]
    : [surface];
  const engParts = [];
  const posLabels = new Set();
  for (const word of candidates) {
    const entry = jmdict[word];
    if (!entry) continue;
    engParts.push(entry.g.map(group => group.join(', ')).join('; '));
    for (const label of jmdictPOS(entry.p)) posLabels.add(label);
  }
  if (!engParts.length) {
    const dictKana = IMPERATIVE_E_TO_U[surface.slice(-1)];
    if (dictKana) {
      const entry = jmdict[surface.slice(0, -1) + dictKana];
      if (entry) {
        engParts.push(entry.g.map(group => group.join(', ')).join('; '));
        for (const label of jmdictPOS(entry.p)) posLabels.add(label);
      }
    }
  }
  if (!engParts.length) return null;
  return { eng: engParts.join('; '), pos: [...posLabels].join('; ') || null };
}

// ── Load dict ────────────────────────────────────────────────────────────────

jmdict = JSON.parse(gunzipSync(readFileSync(join(__dirname, 'jmdict-compact.json.gz'))).toString('utf8'));

// ── Tests ────────────────────────────────────────────────────────────────────

test('returns null when jmdict not loaded', () => {
  const saved = jmdict;
  jmdict = null;
  assert.equal(lookupWord('払う', null), null);
  jmdict = saved;
});

test('direct lookup', () => {
  const r = lookupWord('払う', '払う');
  assert.ok(r);
  assert.ok(r.eng.includes('pay'));
  assert.equal(r.pos, 'verb');
});

test('unknown word returns null', () => {
  assert.equal(lookupWord('zzzzz', null), null);
});

// Kuromoji misanalyses godan imperatives as potential verbs (e.g. 払え → basic_form:
// 払える). The potential forms are not in the compact dict, so lookupWord falls back
// to stripping the imperative ending and looking up the dictionary form.
// Note: ね→ぬ is omitted — 死ぬ is the only common v5n verb and 死ね has its own
// dict entry as an interjection, so the fallback is never reached for that group.
test('godan imperative fallback — eight groups', async (t) => {
  const cases = [
    // [surface, wrongBasicForm, え-col→う-col mapping, expected eng substring]
    ['払え', '払える', 'え→う', 'pay'],
    ['書け', '書ける', 'け→く', 'write'],
    ['泳げ', '泳げる', 'げ→ぐ', 'swim'],
    ['貸せ', '貸せる', 'せ→す', 'lend'],
    ['勝て', '勝てる', 'て→つ', 'win'],
    ['遊べ', '遊べる', 'べ→ぶ', 'play'],
    ['住め', '住める', 'め→む', 'live'],
    ['作れ', '作れる', 'れ→る', 'make'],
  ];
  for (const [surface, badBasicForm, label, expectedEng] of cases) {
    await t.test(label, () => {
      const r = lookupWord(surface, badBasicForm);
      assert.ok(r, `${surface} should find a result via fallback`);
      assert.ok(r.eng.toLowerCase().includes(expectedEng), `eng '${r.eng}' should include '${expectedEng}'`);
      assert.equal(r.pos, 'verb');
    });
  }
});

test('godan imperative fallback when basicForm equals surface', () => {
  const r = lookupWord('払え', '払え');
  assert.ok(r);
  assert.ok(r.eng.includes('pay'));
});

// ── lookupParticle ───────────────────────────────────────────────────────────

test('lookupParticle returns null when jmdict not loaded', () => {
  const saved = jmdict;
  jmdict = null;
  assert.equal(lookupParticle({ surface_form: 'は', basic_form: 'は', pos_detail_1: '係助詞' }), null);
  jmdict = saved;
});

test('lookupParticle — common particles return non-null', async (t) => {
  const cases = [
    ['は', '係助詞'],
    ['が', '格助詞'],
    ['を', '格助詞'],
    ['に', '格助詞'],
    ['へ', '格助詞'],
    ['も', '係助詞'],
    ['ね', '終助詞'],
    ['だけ', '副助詞'],
    ['ので', '接続助詞'],  // not excluded — only て/で are special-cased as 接続助詞
    ['のに', '接続助詞'],
    ['けど', '接続助詞'],
  ];
  for (const [particle, detail] of cases) {
    await t.test(particle, () => {
      const r = lookupParticle({ surface_form: particle, basic_form: particle, pos_detail_1: detail });
      assert.ok(r, `${particle} should return a result`);
    });
  }
});

test('lookupParticle — て as conjunctive (接続助詞) returns null', () => {
  // conjunctive て (食べて): JMdict "common" て entry covers quoting (って) not conjunction
  assert.equal(
    lookupParticle({ surface_form: 'て', basic_form: 'て', pos_detail_1: '接続助詞' }),
    null
  );
});

test('lookupParticle — で as conjunctive (接続助詞) returns null', () => {
  // conjunctive で (読んで): JMdict pg contains locative senses, not conjunctive
  assert.equal(
    lookupParticle({ surface_form: 'で', basic_form: 'で', pos_detail_1: '接続助詞' }),
    null
  );
});

test('lookupParticle — て as non-conjunctive falls through to JMdict', () => {
  const r = lookupParticle({ surface_form: 'て', basic_form: 'て', pos_detail_1: '副助詞' });
  assert.ok(r, 'non-conjunctive て should return a JMdict result');
});

test('lookupParticle — で as case particle (格助詞) falls through to JMdict', () => {
  const r = lookupParticle({ surface_form: 'で', basic_form: 'で', pos_detail_1: '格助詞' });
  assert.ok(r, 'locative で should return a JMdict result');
});

test('lookupParticle — word with no pg entry returns null', () => {
  // ずつ is tagged suf (not prt) in JMdict, so it has no pg field
  assert.equal(
    lookupParticle({ surface_form: 'ずつ', basic_form: 'ずつ', pos_detail_1: '副助詞' }),
    null
  );
});

test('lookupParticle — unknown particle returns null', () => {
  assert.equal(
    lookupParticle({ surface_form: 'zzz', basic_form: 'zzz', pos_detail_1: '格助詞' }),
    null
  );
});

test('lookupParticle — uses basic_form when it differs from surface', () => {
  const r = lookupParticle({ surface_form: 'zzz', basic_form: 'は', pos_detail_1: '係助詞' });
  assert.ok(r, 'should find entry via basic_form');
});

test('lookupParticle — falls back to surface_form when basic_form is *', () => {
  const r = lookupParticle({ surface_form: 'は', basic_form: '*', pos_detail_1: '係助詞' });
  assert.ok(r, 'should find entry via surface_form fallback');
});

test('lookupParticle — result is at most 3 glosses', () => {
  // が has 17 pg entries; only first 3 should be returned
  const r = lookupParticle({ surface_form: 'が', basic_form: 'が', pos_detail_1: '格助詞' });
  assert.ok(r);
  assert.equal(r, jmdict['が'].pg.slice(0, 3).join(', '));
});

// ── toHiragana ───────────────────────────────────────────────────────────────

test('toHiragana', async (t) => {
  await t.test('converts katakana to hiragana', () => {
    assert.equal(toHiragana('アイウエオ'), 'あいうえお');
    assert.equal(toHiragana('カキクケコ'), 'かきくけこ');
    assert.equal(toHiragana('サシスセソ'), 'さしすせそ');
  });
  await t.test('converts small katakana', () => {
    assert.equal(toHiragana('ァィゥェォ'), 'ぁぃぅぇぉ');
  });
  await t.test('leaves hiragana and kanji unchanged', () => {
    assert.equal(toHiragana('あいう漢字'), 'あいう漢字');
  });
  await t.test('handles mixed katakana and other characters', () => {
    assert.equal(toHiragana('アBCあ'), 'あBCあ');
  });
  await t.test('handles empty string', () => {
    assert.equal(toHiragana(''), '');
  });
  await t.test('handles null/undefined', () => {
    assert.equal(toHiragana(null), '');
    assert.equal(toHiragana(undefined), '');
  });
});

// ── stripNonJapanese ─────────────────────────────────────────────────────────

test('stripNonJapanese', async (t) => {
  await t.test('strips ASCII letters and numbers', () => {
    assert.equal(stripNonJapanese('abc 123'), '');
  });
  await t.test('preserves hiragana, katakana, and kanji', () => {
    assert.equal(stripNonJapanese('あいうアイウ漢字'), 'あいうアイウ漢字');
  });
  await t.test('strips English from mixed text, keeping Japanese', () => {
    assert.equal(stripNonJapanese('日本語 Japanese'), '日本語');
  });
  await t.test('preserves Japanese punctuation', () => {
    assert.equal(stripNonJapanese('「こんにちは」'), '「こんにちは」');
    assert.equal(stripNonJapanese('『本』'), '『本』');
    assert.equal(stripNonJapanese('【見出し】'), '【見出し】');
  });
  await t.test('preserves newlines', () => {
    assert.equal(stripNonJapanese('日本語\n英語'), '日本語\n英語');
  });
  await t.test('trims leading and trailing whitespace', () => {
    assert.equal(stripNonJapanese('  日本語  '), '日本語');
  });
  await t.test('returns empty string for pure English', () => {
    assert.equal(stripNonJapanese('Hello, world!'), '');
  });
});

// ── textToHash / hashToText ───────────────────────────────────────────────────

test('textToHash / hashToText round-trip', async (t) => {
  await t.test('round-trips ASCII text', async () => {
    const text = 'hello world';
    assert.equal(await hashToText(await textToHash(text)), text);
  });
  await t.test('round-trips Japanese text', async () => {
    const text = '日本語のテキスト';
    assert.equal(await hashToText(await textToHash(text)), text);
  });
  await t.test('round-trips empty string', async () => {
    assert.equal(await hashToText(await textToHash('')), '');
  });
  await t.test('hash contains no URL-unsafe characters', async () => {
    const hash = await textToHash('テスト test 123');
    assert.doesNotMatch(hash, /[+/=]/);
  });
});
