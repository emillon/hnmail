#!/usr/bin/env python

import unittest
import hnmail

from mock import ListMDA, Message, TreeAPI

class TestHN(unittest.TestCase):
    def test_get_empty(self):
        mda = ListMDA()
        hnmail.main(network=TreeAPI(), mda=mda)
        self.assertEquals(mda.msgs, [])

    def test_one_message(self):
        t = TreeAPI()
        msg = Message(url='example.com', title='an example')
        t.add_disc(msg)
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        self.assertEquals(len(mda.msgs), 1)

    def test_comment(self):
        t = TreeAPI()
        msg1 = Message(url='example.com', title='an example')
        id1 = t.add_disc(msg1)
        msg2 = Message(text='A comment')
        id2 = t.add_to(id1, msg2)
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        self.assertEquals(len(mda.msgs), 2)

if __name__ == '__main__':
    unittest.main()
