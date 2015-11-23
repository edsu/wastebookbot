#!/usr/bin/env python

import os
import re
import json
import time
import tweepy
import pymarkovchain

config = json.load(open('config.json'))
db_file = config['db_file']

mc = pymarkovchain.MarkovChain(db_file)

# create the markov db if it's not there

if not os.path.isfile(db_file):
    text = []
    for line in open('wastebook.txt'):
        if re.search('wastebook', line, re.IGNORECASE):
            continue
        line = line.strip()
        line = re.sub(r'\+\w+-', '', line)
        line = re.sub('<http\w+>', '', line)
        line = re.sub('-$', '', line)
        line = re.sub('^\d+ ', '', line)
        text.append(line)
    mc.generateDatabase(' '.join(text))
    mc.dumpdb()

# set up twitter api

auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
auth.set_access_token(config['access_token'], config['access_token_secret'])
tw = tweepy.API(auth)

# look for messages sent to us

tweet_ids = []
for tweet in tw.mentions_timeline(since_id=config['since_id']):
    text = tweet.text.replace('@wastebookbot ', '')
    user = tweet.user.screen_name
    status_id = tweet.id_str

    if len(text) == 0:
        text = mc.generateString()

    tries = 0
    while len(text.split(' ')) < 5 and tries < 10:
        text = mc.generateString(text)
        tries += 1

    text = '.@%s %s' % (user, text)
    text = text[0:140]
    tw.update_status(status=text, in_reply_to_status_id=status_id)

    time.sleep(1)
    tweet_ids.append(tweet.id_str)

if len(tweet_ids) > 0:
    config['since_id'] = max(tweet_ids)

json.dump(config, open('config.json', 'w'), indent=2)
