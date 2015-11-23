#!/usr/bin/env python

"""
A daemon that listens for tweets to @wastebookbot and replies
with random markov chain text. The first time you run this it
will generate the markov database.
"""

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
        line = re.sub(r'\+\w+- *', '', line)
        line = re.sub('<?http.+>?', '', line)
        line = re.sub('-$', '', line)
        line = re.sub('^\d+ ', '', line)
        line = re.sub('\.\d+ ', '.', line)
        text.append(line)
    mc.generateDatabase(' '.join(text))
    mc.dumpdb()

def generate_text(text):
    tries = 0
    while tries < 100:
        tries += 1
        try:
            if not text:
                text = mc.generateString()
            else:
                new_text = mc.generateStringWithSeed(text)
                if new_text == text:
                    text = ''
                else:
                    text = new_text
        except pymarkovchain.StringContinuationImpossibleError:
            text = mc.generateString()

        if len(text.split(' ')) > 5:
            break

    return text

class ReplyListener(tweepy.StreamListener):
    def on_status(self, tweet):
        if tweet.in_reply_to_screen_name != 'wastebookbot':
            return

        text = tweet.text.replace('@wastebookbot ', '')
        user = tweet.user.screen_name
        status_id = tweet.id_str

        text = generate_text(text)
        text = '.@%s %s' % (user, text)
        text = text[0:140]
        tw.update_status(status=text, in_reply_to_status_id=status_id)
        print text
        time.sleep(1)

        config['since_id'] = tweet.id_str
        json.dump(config, open('config.json', 'w'), indent=2)

auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
auth.set_access_token(config['access_token'], config['access_token_secret'])

stream = tweepy.Stream(auth=auth, listener=ReplyListener())
stream.userstream()
