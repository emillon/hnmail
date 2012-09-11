import email.message
import json
import requests
import subprocess

URL = 'http://api.thriftdb.com/api.hnsearch.com/items/_search'

MDA = 'procmail'

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
    if h['type'] == 'submission' and h['url'] is not None:
        return h['url']
    return h['text']

def build_email(h):
    e = email.message.Message()
    e['Subject'] = "[HN] "
    e['From'] = h['username'] + '-hn@example.com'
    e['Message-ID'] = msg_id(h['id'])
    e['User-Agent'] = 'hnmail'
    e['Content-type'] = 'text/plain; charset="utf-8"'
    p = payload(h)
    p = p.encode('utf-8')
    set_reply_to(e, h)
    e.set_payload(p)
    return e

def send_to_mda(e):
    proc = subprocess.Popen(MDA, stdin=subprocess.PIPE)
    proc.communicate(e.as_string())
    proc.stdin.close()

def main():
    n = 100
    h = hnget(limit=n, sortby='create_ts desc')
    i = 1
    for r in h['results']:
        print '%d/%d' % (i, n)
        i += 1
        r = r['item']
        e = build_email(r)
        send_to_mda(e)

if __name__ == '__main__':
    main()
