#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
@author: Panagiotis Vasilopoulos (AlwaysLivid)
@description: Bot that posts a tiny flower bed on Twitter every few hours.
@contributors: https://github.com/panos/TinyFlowerBeds/graphs/contributors
'''

import tweepy
import time
import configparser
import logging, os, textwrap
import random
from random import randint
from datetime import datetime, timedelta

print("""
                       TinyFlowerBeds

            Copyright (C) 2018-2020 AlwaysLivid

=============================================================
======================= DISCLAIMER ==========================
=============================================================
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; read the LICENSE file for details.
=============================================================

""")

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler("{0}/{1}.txt".format(os.path.dirname(os.path.realpath(__file__)), "log")),
        logging.StreamHandler()
    ]
)

emojis = ["🌻", "🌱", "🌸", "🌷", "💮", "🌺", "🌹", "🌼", "🌿", "🌿", "🌷"]

config_path = "src/config.txt"
credential_list = ["CONSUMER_KEY", "CONSUMER_SECRET", "ACCESS_KEY", "ACCESS_SECRET"]
use_environment_variables = bool
use_file_variables = bool
amount_of_credentials = len(credential_list)
credential_counter = 0

CONSUMER_KEY = str
CONSUMER_SECRET = str
ACCESS_KEY = str
ACCESS_SECRET = str

for credential in credential_list:
    if credential_list[0] in os.environ:
        credential_counter += 1

if credential_counter == amount_of_credentials:
    logging.info("All environment variables were found!")
    use_environment_variables = True
    use_file_variables = False
else:
    logging.warning("Environment variables were not successfully found!")
    logging.info("Using credentials.py instead.")
    use_environment_variables = False
    use_file_variables = True

if use_environment_variables == True:
    logging.info("Using environment variables.")
    CONSUMER_KEY = os.environ['CONSUMER_KEY']
    CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
    ACCESS_KEY = os.environ['ACCESS_KEY']
    ACCESS_SECRET = os.environ['ACCESS_SECRET']
elif use_file_variables == True:
    logging.info("Using file variables.")
    try:
        config = configparser.ConfigParser()
        config.read(config_path)

        mininterval = int(config['intervals']['mininterval'])
        maxinterval = int(config['intervals']['maxinterval'])

        cooldown = randint(mininterval, maxinterval) * 24 * 60 * 60
        # converts the random value from days to seconds

        limit = int(config['formatting']['lines']) * int(config['formatting']['limit_per_line'])

       	CONSUMER_KEY = config['credentials']['CONSUMER_KEY']
        CONSUMER_SECRET = config['credentials']['CONSUMER_SECRET']
        ACCESS_KEY = config['credentials']['ACCESS_KEY']
        ACCESS_SECRET = config['credentials']['ACCESS_SECRET']
    except ImportError:
        logging.critical("An error occured while importing the credentials from the credentials.py file.")
        logging.critical("The bot will now shut down.")
        logging.info("Please check the README.md file for more information.")
        exit()

class Bot:
    def user_info(self, api, user): 
        ''' 
        Prints user information. 
        
        Also works as a way to check whether the credentials are valid without making a tweet.
        '''
        logging.info("Username: {}".format(api.get_user(user.id).screen_name))
        logging.info("Display Name: {}".format(user.name))
        logging.info("ID: {}".format(user.id))

    def generate_batch(self):
        '''
        Generates a string containing flower emojis, while creating a virtual flower bed in the form of a tweet!
        '''
        batch = ''
        counter = 0
        while counter != limit:
            batch += random.choice(emojis)
            counter += 1
            if counter > 16: break
        tweet = '\n'.join(textwrap.wrap(batch, int(config['formatting']['limit_per_line'])))
        return tweet

    def tweet_loop(self, api):
        '''
        Function that generates and tweets a flower batch at a specified interval.
        '''
        while True:
            try:
                last_tweet_time = api.user_timeline()[0].created_at-timedelta(hours=4)
                if not (os.getenv('CI') == None or os.getenv('CI') == False) or not (os.getenv('CONTINUOUS_INTEGRATION') == None or os.getenv('CONTINUOUS_INTEGRATION') == False):
                    logging.critical("CI detected! Skipping tweet.")
                    logging.critical("Everything seems to be fine. Exiting...")
                    exit()
                elif len(api.user_timeline()) == 0 or last_tweet_time+timedelta(seconds=cooldown) > datetime.now():
                    next_tweet_time = cooldown - (datetime.now()-last_tweet_time).total_seconds()
                    logging.info(f'The next tweet is scheduled to be made at {last_tweet_time+timedelta(seconds=cooldown)}, {int(next_tweet_time/60)} minutes from now')
                    time.sleep(cooldown - (datetime.now()-last_tweet_time).total_seconds())
                else: 
                    api.update_status(self.generate_batch())
                    logging.info("Tweeted out a new flower bed!")
                    logging.info("The next tweet is scheduled to be made in {} minutes".format(cooldown/60))
                    time.sleep(cooldown)
            except tweepy.RateLimitError:
                    logging.critical("Tweeting failed due to ratelimit. Waiting {} more minutes.".format(cooldown/60))
                    time.sleep(cooldown)
            

    def main(self):
        '''
        Main function that takes care of the authentication and the threading.
        '''
        logging.info("Attempting to login!")
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
        api = tweepy.API(auth)
        user = api.me()
        self.user_info(api, user)
        logging.info("Successfully logged in!")
        self.tweet_loop(api)

if __name__ == '__main__':
    try:
        TwitterBot = Bot()
        TwitterBot.main()
    except tweepy.TweepError:
        logging.critical("Authentication error!")
        logging.info("Please validate your credentials.") 
        quit()
