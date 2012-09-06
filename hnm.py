import email.message
import json
import requests

URL = 'http://api.thriftdb.com/api.hnsearch.com/items/_search'

def hnget(**params):
    r = requests.get(URL, params=params)
    j = json.loads(r.text)
    return j

def msg_id(n):
    return '%d-msg@example.com' % n

def set_reply_to(e, h):
    pid = h['parent_id']
    if pid is not None:
        e['In-Reply-To'] = msg_id(pid)

def payload(h):
    if h['type'] == 'submission':
        return h['url']
    return h['text']

def build_email(h):
    print json.dumps(h, indent=4)
    e = email.message.Message()
    e['Subject'] = "[HN] "
    e['From'] = h['username'] + '-hn@example.com'
    e['Message-ID'] = msg_id(h['id'])
    set_reply_to(e, h)
    e.set_payload(payload(h))
    return e

def main():
    h = hnget(limit=10, sortby='create_ts desc')
    for r in h['results']:
        r = r['item']
        e = build_email(r)
        print e.as_string()

if __name__ == '__main__':
    main()
