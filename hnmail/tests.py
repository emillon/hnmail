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

class Message:
    def __init__(self, url=None, title=None, text=None):
        self.children = []
        self.url = url
        self.title = title
        self.parent = None
        self.text = text

class MsgMaker:
    def __init__(self):
        self.counter = 1
        self.disc = []
        self.all_msgs = {}

    def find_msg(self, msg_id):
        return self.all_msgs[msg_id]

    def next_id(self):
        r = self.counter
        self.counter += 1
        return r

    def add_disc(self, msg):
        msg.ident = self.next_id()
        msg.typ = 'submission'
        self.disc.append(msg)
        self.all_msgs[msg.ident] = msg
        return msg.ident

    def add_to(self, msgid, msg):
        msg.ident = self.next_id()
        msg.typ = 'comment'
        parent = self.find_msg(msgid)
        parent.children.append(msg)
        msg.parent = parent
        self.all_msgs[msg.ident] = msg
        return msg.ident

    def find_discussion(self, ident):
        msg = self.find_msg(ident)
        is_root = True
        while msg.parent is not None:
            msg = msg.parent
            is_root = False
        if is_root:
            r = None
        else:
            r = { 'sigid': '%d-xxxx' % msg.ident
                , 'title': msg.title
                , 'id': msg.ident
                }
        return r

    def msgs(self):
        r = []
        worklist = self.disc
        while worklist:
            msg = worklist.pop(0)
            item = { 'type': msg.typ
                   , 'id': msg.ident
                   , '_id': '%d-xxxx' % msg.ident
                   , 'url': msg.url
                   , 'discussion': self.find_discussion(msg.ident)
                   , 'num_comments': 0 # TODO len(msg.children)
                   , 'create_ts': '2020-01-01T00:00:00Z'
                   , 'username': 'michel'
                   , 'parent_id': None
                   }
            if msg.title is not None:
                item['title'] = msg.title
            if msg.parent is not None:
                item['parent_id'] = msg.parent.ident
            if msg.text is not None:
                item['text'] = msg.text
            r.append(item)
            for child in msg.children:
                worklist.append(child)
        return r

class TestHN(unittest.TestCase):
    def test_get_empty(self):
        mda = ListMDA()
        hnmail.main(network=TreeAPI(), mda=mda)
        self.assertEquals(mda.msgs, [])

    def test_one_message(self):
        msg = Message(url='example.com', title='an example')
        mk = MsgMaker()
        mk.add_disc(msg)
        t = TreeAPI(mk.msgs())
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        self.assertEquals(len(mda.msgs), 1)

    def test_comment(self):
        mk = MsgMaker()
        msg1 = Message(url='example.com', title='an example')
        id1 = mk.add_disc(msg1)
        msg2 = Message(text='A comment')
        id2 = mk.add_to(id1, msg2)
        t = TreeAPI(mk.msgs())
        mda = ListMDA()
        hnmail.main(network=t, mda=mda)
        self.assertEquals(len(mda.msgs), 2)

if __name__ == '__main__':
    unittest.main()
