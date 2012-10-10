#!/usr/bin/env python
"""
hnmail - mail gateway for Hacker News
"""

__author__ = 'Etienne Millon'
__email__ = 'me AT emillon.org'
__license__ = 'BSD-3'
__status__ = 'Prototype'

import datetime
import email.charset
import email.message
import email.utils
import json
import os
import pickle
import requests
import subprocess
import sys
import time

from xdg.BaseDirectory import save_data_path

URL = 'http://api.thriftdb.com/api.hnsearch.com'

MDA = 'procmail'

class HackerNewsApi:
    def search(self, params):
        """
        Get results from the Hacker News ThriftDB API.
        The documentation of this API is available at:
        http://www.hnsearch.com/api
        Keyword arguments are passed as GET parameters and the result is returned as
        a JSON object.
        """
        response = requests.get(URL + '/items/_search', params=params)
        return json.loads(response.text)

    def get_item(self, sig_id):
        response = requests.get(URL + '/items/' + sig_id)
        return json.loads(response.text)

class ProcmailMDA:
    def send_to(self, mail):
        """
        Send an email to a Mail Delivery Agent such as procmail.
        """
        proc = subprocess.Popen(MDA, stdin=subprocess.PIPE)
        proc.communicate(mail.as_string())
        proc.stdin.close()

def msg_id(item_id):
    """
    Build a RFC822 Message-ID from a HN item id.
    """
    return '<%d-msg@example.com>' % item_id

def from_rfc8601(rfc8601_dt):
    """
    Convert a RFC8601 datetime to a datetime object.
    """
    return datetime.datetime.strptime(rfc8601_dt, "%Y-%m-%dT%H:%M:%SZ")

def to_rfc822(dtime):
    """
    Convert a datetime object to a RFC822 string
    """
    timetuple = dtime.timetuple()
    localtime = time.mktime(timetuple)
    return email.utils.formatdate(localtime)

def build_item(data):
    if data['type'] == 'submission':
        if data['url'] is None:
            return TextItem(data)
        else:
            return SubmissionItem(data)
    else:
        return Item(data)

class Item:
    def __init__(self, data):
        self.data = data

    def payload(self):
        """
        Compute the payload of the email corresponding to a given HN item.
        """
        return self.data['text']

    def subject(self):
        """
        Compute the subject of an item.
        If this is not a submission, it will include a "Re: " prefix.
        """
        return "Re: %s" % self.data['discussion']['title']

    def needs_to_be_sent(self, state):
        item_date = from_rfc8601(self.data['create_ts'])
        return ('run_date' not in state or item_date > state['run_date'])

    def creation_date(self):
        return from_rfc8601(self.data['create_ts'])

    def build_email(self):
        mail = email.message.Message()
        mail['Subject'] = self.subject()
        mail['From'] = '{0} <{0}-hn@example.com>'.format(self.data['username'])
        mail['Message-ID'] = msg_id(self.data['id'])
        mail['User-Agent'] = 'hnmail'
        mail['Date'] = to_rfc822(self.creation_date())
        pid = self.data['parent_id']
        if pid is not None:
            mail['In-Reply-To'] = msg_id(pid)
        charset = email.charset.Charset('utf-8')
        mail.set_payload(self.payload(), charset)
        return mail

class SubmissionItem(Item):
    def payload(self):
        return self.data['url']

    def subject(self):
        return self.data['title']

class TextItem(Item):
    def subject(self):
        return self.data['title']

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

def fetch_children(network, sigid, exp_children):
    params = { 'filter[fields][parent_sigid]': sigid
             , 'sortby': 'create_ts desc'
             , 'limit': exp_children
             }
    return network.search(params)

def fetch_thread(network, disc):
    """
    Fetch the whole thread with given signed ID.
    """
    root_comments = network.get_item(disc)['num_comments']
    worklist = [(disc, root_comments)]
    while worklist:
        (sigid, num_comments) = worklist.pop(0)
        response = fetch_children(network, sigid, num_comments)
        results = response['results']
        for result in results:
            item = result['item']
            child_id = item['_id']
            width = item['num_comments']
            if width > 0:
                worklist.append((child_id, width))
            yield item

def run(network=None, mda=None, quiet=False, state=None):
    """
    Get new messages, and send them to a MDA.

    Parameters :
      - network : how to access the API. See HackerNewsApi.
      - mda : how to deliver emails. See ProcmailMDA.
      - quiet : emit messages or not.
      - state : how to handle persistent state. See State.
    """
    def log(msg):
        if quiet:
            return
        print msg
    if network is None:
        network = HackerNewsApi()
    if mda is None:
        mda = ProcmailMDA()
    num_threads = 100
    params = { 'limit': num_threads
             , 'sortby': 'create_ts desc'
             }
    response = network.search(params)
    results = response['results']
    discussions = {}
    submissions = set()
    for result in results:
        item = result['item']
        if item['type'] == 'submission':
            submissions.add(item['id'])
            obj = build_item(item)
            if state is None or obj.needs_to_be_sent(state):
                log ("%d - %s" % (item['id'], item['title']))
                mda.send_to(obj.build_email())
        else:
            disc = item['discussion']
            discussions[disc['id']] = (disc['sigid'], disc['title'])
    for (disc_id, (sigid, title)) in discussions.iteritems():
        log ("%d - %s" % (disc_id, title))
        for item in fetch_thread(network, sigid):
            if item['type'] == 'submission' and item['id'] in submissions:
                continue
            obj = build_item(item)
            if state is None or obj.needs_to_be_sent(state):
                mda.send_to(obj.build_email())
                if not quiet:
                    sys.stdout.write('.')
                    sys.stdout.flush()
        log ("")
    if state:
        state['run_date'] = datetime.datetime.now()

def main():
    """
    Program entry point.
    """
    state_file = os.path.join(save_data_path('hnmail'), 'state.pickle')
    with State(state_file) as state:
        run(state=state)

if __name__ == '__main__':
    main()
