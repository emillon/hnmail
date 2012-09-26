"""
hnmail - mail gateway for Hacker News
"""

import datetime
import email.charset
import email.message
import email.utils
import json
import os
import pickle
import requests
import subprocess
import time

from xdg.BaseDirectory import save_data_path

URL = 'http://api.thriftdb.com/api.hnsearch.com/items/_search'

MDA = 'procmail'

def hnget(**params):
    """
    Get results from the Hacker News ThriftDB API.
    The documentation of this API is available at:
    http://www.hnsearch.com/api
    Keyword arguments are passed as GET parameters and the result is returned as
    a JSON object.
    """
    response = requests.get(URL, params=params)
    return json.loads(response.text)

def msg_id(item_id):
    """
    Build a RFC822 Message-ID from a HN item id.
    """
    return '<%d-msg@example.com>' % item_id

def set_reply_to(mail, item):
    """
    Set the In-Reply-To field of an email.
    """
    pid = item['parent_id']
    if pid is not None:
        mail['In-Reply-To'] = msg_id(pid)

def payload(item):
    """
    Compute the payload of the email corresponding to a given HN item.
    Depending on the type of item (submission, discussion, etc), it will either
    include a link or the text of the submission.
    """
    if item['type'] == 'submission' and item['url'] is not None:
        return item['url']
    return item['text']

def from_rfc8601(rfc8601_dt):
    """
    Convert a RFC8601 datetime to a datetime object.
    """
    return datetime.datetime.strptime(rfc8601_dt, "%Y-%m-%dT%H:%M:%SZ")

def convert_time(rfc8601_dt):
    """
    Convert a RFC8601 date to a RFC822 date
    """
    dtime = from_rfc8601(rfc8601_dt)
    timetuple = dtime.timetuple()
    localtime = time.mktime(timetuple)
    return email.utils.formatdate(localtime)

def subject(item):
    """
    Compute the subject of an item.
    If this is not a submission, it will include a "Re: " prefix.
    """
    if item['type'] == 'submission':
        return item['title']
    return "Re: %s" % item['discussion']['title']

def build_email(item):
    """
    Build an email from a HN item.
    """
    mail = email.message.Message()
    mail['Subject'] = subject(item)
    mail['From'] = '{0} <{0}-hn@example.com>'.format(item['username'])
    mail['Message-ID'] = msg_id(item['id'])
    mail['User-Agent'] = 'hnmail'
    mail['Date'] = convert_time(item['create_ts'])
    set_reply_to(mail, item)
    charset = email.charset.Charset('utf-8')
    mail.set_payload(payload(item), charset)
    return mail

def send_to_mda(mail):
    """
    Send an email to a Mail Delivery Agent such as procmail.
    """
    proc = subprocess.Popen(MDA, stdin=subprocess.PIPE)
    proc.communicate(mail.as_string())
    proc.stdin.close()

class State:
    """
    A context manager for the application state.
    It exposes a dict-like interface that will persist across runs.
    """

    def __init__(self, file_name):
        self.file_name = file_name
        try:
            with open(self.file_name) as state_file:
                self.data = pickle.load(state_file)
        except IOError:
            self.data = {}

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        with open(self.file_name, 'w') as state_file:
            pickle.dump(self.data, state_file)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

def fetch_thread(disc_sigid):
    """
    Fetch the whole thread with given signed ID.
    """
    worklist = [disc_sigid]
    results = []
    while worklist:
        sigid = worklist.pop(0)
        params = { 'filter[fields][parent_sigid]': sigid
                 , 'sortby': 'create_ts desc'
                 }
        response = hnget(**params)
        for result in response['results']:
            item = result['item']
            child_id = item['_id']
            worklist.append(child_id)
            results.append(item)
    return results

def handle_item(state, item):
    """
    Build and send an email for a given item.
    """
    item_date = from_rfc8601(item['create_ts'])
    if 'run_date' in state and item_date < state['run_date']:
        return
    mail = build_email(item)
    send_to_mda(mail)

def main():
    """
    Program entry point.
    """
    state_file = os.path.join(save_data_path('hnmail'), 'state.pickle')
    with State(state_file) as state:
        num_threads = 100
        response = hnget(limit=num_threads, sortby='create_ts desc')
        results = response['results']
        discussions = {}
        for result in results:
            item = result['item']
            if item['type'] == 'submission':
                print "%d - %s" % (item['id'], item['title'])
                handle_item(state, item)
            else:
                disc = item['discussion']
                discussions[disc['id']] = (disc['sigid'], disc['title'])
        for (disc_id, (sigid, title)) in discussions.iteritems():
            print "%d - %s" % (disc_id, title)
            for item in fetch_thread(sigid):
                handle_item(state, item)
        newest = results[0]['item']
        state['run_date'] = from_rfc8601(newest['create_ts'])

if __name__ == '__main__':
    main()
