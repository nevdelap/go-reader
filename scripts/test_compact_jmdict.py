#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
#
# Validates the content of jmdict-compact.json.gz.
# Run from the repo root: uv run scripts/test_compact_jmdict.py

import gzip, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
with gzip.open(ROOT / 'jmdict-compact.json.gz') as f:
    DICT = json.load(f)


def pg(word):
    return DICT.get(word, {}).get('pg')


class TestParticleGlosses(unittest.TestCase):

    def test_common_particles_have_pg(self):
        expected = ['は', 'が', 'を', 'に', 'へ', 'で', 'と', 'から', 'より',
                    'の', 'まで', 'も', 'ね', 'か', 'ながら', 'ので', 'のに',
                    'けど', 'だけ', 'こそ', 'さえ', 'しか', 'など', 'ばかり']
        missing = [p for p in expected if not pg(p)]
        self.assertFalse(missing, f'particles missing pg: {missing}')

    def test_pg_is_list_of_strings(self):
        for word, entry in DICT.items():
            if 'pg' in entry:
                self.assertIsInstance(entry['pg'], list, f'{word}: pg should be a list')
                for gloss in entry['pg']:
                    self.assertIsInstance(gloss, str, f'{word}: pg item should be str')
                    self.assertTrue(gloss.strip(), f'{word}: pg item should not be blank')

    def test_topic_particle_ha(self):
        self.assertIn('indicates sentence topic', pg('は'))

    def test_subject_particle_ga(self):
        self.assertTrue(any('subject' in g for g in pg('が')),
                        f'が pg should mention subject: {pg("が")}')

    def test_object_particle_wo(self):
        self.assertTrue(any('direct object' in g for g in pg('を')),
                        f'を pg should mention direct object: {pg("を")}')

    def test_topic_particle_ha_first_gloss(self):
        self.assertEqual(pg('は')[0], 'indicates sentence topic')

    def test_te_pg_is_quoting_sense(self):
        # The JMdict "common" て entry is the quoting particle (って).
        # This documents why lookupParticle uses pg2 for 接続助詞 て.
        te_pg = pg('て')
        self.assertIsNotNone(te_pg, 'て should have a pg entry')
        self.assertTrue(
            any('said' in g for g in te_pg),
            f'て pg should contain quoting senses ("said"), got: {te_pg[:4]}'
        )

    def test_te_pg2_is_conjunctive_sense(self):
        # pg2 holds the non-common entry's glosses — the conjunctive て (食べて).
        te_pg2 = DICT.get('て', {}).get('pg2')
        self.assertIsNotNone(te_pg2, 'て should have a pg2 entry')
        self.assertTrue(
            any('and' in g or 'then' in g for g in te_pg2),
            f'て pg2 should contain conjunctive senses, got: {te_pg2[:4]}'
        )

    def test_de_pg_is_locative_sense(self):
        # で pg is the locative sense (common entry).
        de_pg = pg('で')
        self.assertIsNotNone(de_pg, 'で should have a pg entry')
        self.assertTrue(
            any(g in ('at', 'in') for g in de_pg),
            f'で pg should contain locative senses ("at"/"in"), got: {de_pg[:4]}'
        )

    def test_de_pg2_is_conjunctive_sense(self):
        # て and で share the same non-common conjunctive entry.
        de_pg2 = DICT.get('で', {}).get('pg2')
        self.assertIsNotNone(de_pg2, 'で should have a pg2 entry')
        self.assertTrue(
            any('and' in g or 'then' in g for g in de_pg2),
            f'で pg2 should contain conjunctive senses, got: {de_pg2[:4]}'
        )

    def test_zutu_has_no_pg_but_single_g(self):
        # ずつ is tagged suf (not prt) so no pg, but has a single unambiguous g group.
        self.assertIsNone(pg('ずつ'), f'ずつ should have no pg, got: {pg("ずつ")}')
        g0 = DICT.get('ずつ', {}).get('g', [])
        self.assertEqual(len(g0), 1, 'ずつ should have exactly one g group for safe g[0] fallback')

    def test_nitotte_has_pg(self):
        # にとって is tagged exp; exp senses are now collected into pg.
        nitotte_pg = pg('にとって')
        self.assertIsNotNone(nitotte_pg, 'にとって should have pg from exp sense')
        self.assertTrue(any('for' in g or 'standpoint' in g for g in nitotte_pg),
                        f'にとって pg should describe its particle use, got: {nitotte_pg[:3]}')

    def test_niyori_has_pg(self):
        # により had 2 g groups (noun + exp), so g[0] fallback gave "similarity" (wrong).
        # exp senses now go into pg, giving the correct particle meaning.
        niyori_pg = pg('により')
        self.assertIsNotNone(niyori_pg, 'により should have pg from exp sense')
        self.assertTrue(any('according' in g or 'due to' in g for g in niyori_pg),
                        f'により pg should describe its particle use, got: {niyori_pg[:3]}')

    def test_pg_length_reasonable(self):
        # pg entries should not be empty, and capping at a large number catches runaway merges
        for word, entry in DICT.items():
            if 'pg' in entry:
                self.assertGreater(len(entry['pg']), 0, f'{word}: pg should not be empty')
                self.assertLessEqual(len(entry['pg']), 50, f'{word}: pg suspiciously long')


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestParticleGlosses)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
