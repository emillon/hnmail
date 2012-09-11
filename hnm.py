import datetime
import email.charset
import email.message
import email.utils
import json
import requests
import subprocess
import time

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

def convert_time(s):
    "Convert a RFC8601 date to a RFC822 date"
    dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    tt = dt.timetuple()
    ti = time.mktime(tt)
    return email.utils.formatdate(ti)

def subject(h):
    if h['type'] == 'submission':
        return h['title']
    return "Re: %s" % h['discussion']['title']

def build_email(h):
    e = email.message.Message()
    e['Subject'] = subject(h)
    e['From'] = h['username'] + '-hn@example.com'
    e['Message-ID'] = msg_id(h['id'])
    e['User-Agent'] = 'hnmail'
    e['Date'] = convert_time(h['create_ts'])
    p = payload(h)
    set_reply_to(e, h)
    c = email.charset.Charset('utf-8')
    e.set_payload(p, c)
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
