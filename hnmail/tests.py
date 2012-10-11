#!/usr/bin/env python

import unittest
import hnmail

from mock import ListMDA, Message, TreeAPI

class TestHN(unittest.TestCase):
    def run_hnmail(self):
        """
        Build a MDA, run tests with given TreeAPI and return delivered messages.
        """
        mda = ListMDA()
        hnmail.run(network=self.api, mda=mda, quiet=True)
        return mda.msgs

    def setUp(self):
        self.api = TreeAPI()

    def test_get_empty(self):
        msgs = self.run_hnmail()
        self.assertEquals(msgs, [])

    def test_one_message(self):
        msg = Message(url='example.com', title='an example')
        self.api.add_disc(msg)
        msgs = self.run_hnmail()
        self.assertEquals(len(msgs), 1)

    def test_comment(self):
        msg1 = Message(url='example.com', title='an example')
        id1 = self.api.add_disc(msg1)
        msg2 = Message(text='A comment')
        id2 = self.api.add_to(id1, msg2)
        msgs = self.run_hnmail()
        self.assertEquals(len(msgs), 2)

    def test_limit(self):
        root = self.api.add_disc(Message(url='example.com', title='an example'))
        n = 20
        for i in xrange(0, n):
            msg = Message(text='A comment')
            self.api.add_to(root, msg)
        msgs = self.api.search({'limit': 10})
        self.assertEquals(len(msgs['results']), 10)

    def test_wide_disc(self):
        root = self.api.add_disc(Message(url='example.com', title='an example'))
        n = 20
        for i in xrange(0, n):
            msg = Message(text='A comment')
            self.api.add_to(root, msg)
        msgs = self.run_hnmail()
        self.assertEquals(len(msgs), 1+n)

if __name__ == '__main__':
    unittest.main()
