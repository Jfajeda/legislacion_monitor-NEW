import os
import tempfile
import unittest

from src.database import Database


class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db = Database({'path': self.tmp.name})
    
    def tearDown(self):
        os.unlink(self.tmp.name)
        # WAL files
        for suffix in ('-wal', '-shm'):
            path = self.tmp.name + suffix
            if os.path.exists(path):
                os.unlink(path)
    
    def _sample_pub(self, url='https://example.com/norm1'):
        return {
            'source': 'ue_medio_ambiente',
            'url': url,
            'title': 'Test Norm',
            'category': 'medio_ambiente',
            'date': '2025-01-01',
            'vigente': 'Si',
            'norma': 'Test/2025',
            'summary': 'Test summary',
        }
    
    def test_save_and_exists(self):
        pub = self._sample_pub()
        self.db.save_publication(pub)
        self.assertTrue(self.db.publication_exists(pub['url']))
    
    def test_duplicate_url_ignored(self):
        pub = self._sample_pub()
        self.db.save_publication(pub)
        self.db.save_publication(pub)  # Should not raise
        pubs = self.db.get_all_publications()
        urls = [p['url'] for p in pubs]
        self.assertEqual(urls.count(pub['url']), 1)
    
    def test_get_publications_with_filter(self):
        self.db.save_publication(self._sample_pub('https://a.com'))
        pub2 = self._sample_pub('https://b.com')
        pub2['category'] = 'ciberseguridad'
        self.db.save_publication(pub2)
        
        result = self.db.get_publications_by_category('ciberseguridad')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['category'], 'ciberseguridad')
    
    def test_get_stats(self):
        self.db.save_publication(self._sample_pub())
        stats = self.db.get_stats()
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['vigentes'], 1)
    
    def test_publication_not_exists(self):
        self.assertFalse(self.db.publication_exists('https://no-such-url.com'))


if __name__ == '__main__':
    unittest.main()
