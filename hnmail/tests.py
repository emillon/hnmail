#!/usr/bin/env python

import unittest
import hnmail

class TreeAPI:
    def get(self, params):
        r = { 'results': '' }
        return r

class TestHN(unittest.TestCase):
    def test_get_empty(self):
        hnmail.main(network=TreeAPI(), mda_enabled=False)

if __name__ == '__main__':
    unittest.main()
