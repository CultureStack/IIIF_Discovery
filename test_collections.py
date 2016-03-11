'''
Unit tests.

Incomplete and behind the code.
'''import unittest
from iiif_collections import IIIF_Item


class CollectionTester(unittest.TestCase):

    def test_collection_init(self):
        self.assertEqual(IIIF_Item('http://www.test.com/test').uri,
                         'http://www.test.com/test')

    def test_collection_url_valid(self):
        self.assertEqual(IIIF_Item('http://www.test.com/test').uri_valid,
                         True)

    def test_collection_url_invalid(self):
        self.assertRaises(ValidationFailure,
                          Collection('ftpr:/test.com/test').uri_valid)

    def test_collection_url_type(self):
        self.assertEqual(IIIF_Item('http://test.com/test').request_type,
                         'http')

    def test_collection_url_wrong_type(self):
        self.assertEqual(IIIF_Item('ftp://test.com/test').request_type,
                         None)

    def test_collection_url_empty(self):
        self.assertEqual(IIIF_Item(None).uri_valid, False)


if __name__ == '__main__':
    unittest.main()
