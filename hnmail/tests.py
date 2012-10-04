#!/usr/bin/env python

import unittest
import hnmail

from mock import ListMDA, Message, TreeAPI

def run(api):
    """
    Build a MDA, run tests with given TreeAPI and return delivered messages.
    """
    mda = ListMDA()
    hnmail.main(network=api, mda=mda, quiet=True)
    return mda.msgs

class TestHN(unittest.TestCase):
    def test_get_empty(self):
        msgs = run(TreeAPI())
        self.assertEquals(msgs, [])

    def test_one_message(self):
        t = TreeAPI()
        msg = Message(url='example.com', title='an example')
        t.add_disc(msg)
        msgs = run(t)
        self.assertEquals(len(msgs), 1)

    def test_comment(self):
        t = TreeAPI()
        msg1 = Message(url='example.com', title='an example')
        id1 = t.add_disc(msg1)
        msg2 = Message(text='A comment')
        id2 = t.add_to(id1, msg2)
        msgs = run(t)
        self.assertEquals(len(msgs), 2)

if __name__ == '__main__':
    unittest.main()
