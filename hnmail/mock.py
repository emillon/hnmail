def sign(i):
    return '%d-xxxx' % i

def unsign(s):
    return int(s[:-5])

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

class TreeAPI:
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
            r = { 'sigid': sign(msg.ident)
                , 'title': msg.title
                , 'id': msg.ident
                }
        return r

    def build_item(self, msg):
        item = { 'type': msg.typ
               , 'id': msg.ident
               , '_id': sign(msg.ident)
               , 'url': msg.url
               , 'discussion': self.find_discussion(msg.ident)
               , 'num_comments': len(msg.children)
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
        return item

    def search(self, params):
        msgs = self.all_msgs.values()
        if 'filter[fields][parent_sigid]' in params:
            pid = params['filter[fields][parent_sigid]']
            def is_ok(msg):
                return (msg.parent is not None
                    and pid == sign(msg.parent.ident))
            msgs = filter(is_ok, msgs)
        if 'limit' in params:
            lim = params['limit']
            msgs = msgs[:lim]
        results = [ {'item' : self.build_item(msg)} for msg in msgs ]
        r = { 'results': results }
        return r

    def get_item(self, sig_id):
        ident = unsign(sig_id)
        msg = self.all_msgs[ident]
        return self.build_item(msg)
