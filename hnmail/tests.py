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

class MsgMaker:
    def __init__(self):
        self.counter = 1

    def make_message(self, **params):
        ident = self.counter
        self.counter += 1
        msg = { 'type': params.get('type', 'submission')
              , 'url': 'example.com'
              , 'create_ts': '2020-01-01T00:00:00Z'
              , 'id': ident
              , '_id': '%d-xxxx' % ident
              , 'title': 'an example'
              , 'username': 'michel'
              , 'parent_id': params.get('parent_id', None)
              , 'num_comments': 0
              }
        if msg['type'] == 'comment':
            dident = params.get('disc', msg['parent_id'] or 0)
            disc =  { 'sigid': '%d-xxxx' % dident
                    , 'title': 'Title'
                    , 'id': dident
                    }
            msg['discussion'] = disc
            msg['text'] = 'no text'
        return msg

class TestHN(unittest.TestCase):
    def test_get_empty(self):
        mda = ListMDA()
        hnmail.main(network=TreeAPI(), mda=mda)
        self.assertEquals(mda.msgs, [])

    def test_one_message(self):
        msg = MsgMaker().make_message()
        t = TreeAPI([msg])
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        self.assertEquals(len(mda.msgs), 1)

    def test_comment(self):
        mk = MsgMaker()
        msg1 = mk.make_message()
        msg2 = mk.make_message(type='comment', parent_id=msg1['id'])
        t = TreeAPI([msg1, msg2])
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        self.assertEquals(len(mda.msgs), 2)

if __name__ == '__main__':
    unittest.main()
