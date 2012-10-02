#!/usr/bin/env python

import unittest
import hnmail

class TreeAPI:
    def __init__(self, msgs=[]):
        self.msgs = msgs

    def get(self, params):
        results = [ {'item' : msg} for msg in self.msgs ]
        r = { 'results': results }
        return r

class ListMDA:
    def __init__(self):
        self.msgs = []

    def send_to(self, mail):
        self.msgs.append(mail)

class TestHN(unittest.TestCase):
    def test_get_empty(self):
        mda = ListMDA()
        hnmail.main(network=TreeAPI(), mda=mda)
        self.assertEquals(mda.msgs, [])

    def test_one_message(self):
        msg = { 'type': 'submission'
              , 'url': 'example.com'
              , 'create_ts': '2020-01-01T00:00:00Z'
              , 'id': 1
              , 'title': 'an example'
              , 'username': 'michel'
              , 'parent_id': None
              }
        t = TreeAPI([msg])
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        #self.assertEquals(len(mda.msgs), 1)

if __name__ == '__main__':
    unittest.main()
