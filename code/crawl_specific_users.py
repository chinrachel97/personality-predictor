import atexit
import datetime
import gzip
import json
import os
import time
import logging
import pandas as pandas
import tweepy
from tqdm import tqdm
import sys
import api_keys

twitter_api_tokens = api_keys.twitter_api_tokens

PATH = "../"
DEFAULT_SINCE_ID = 849298404987600896

twitter_api = None


def auth_tweepy():
    global twitter_api_tokens
    global twitter_api

    letter, token = twitter_api_tokens.pop()

    auth = tweepy.OAuthHandler(
        token['consumer-key'], token['consumer-secret'])
    auth.set_access_token(token['access-token'], token['access-token-secret'])
    twitter_api = tweepy.API(auth)

    twitter_api_tokens.insert(0, (letter, token))


def sleep(mins):
    time.sleep(mins * 60)


def write_to_file(gzip_file_name, tweet):
    f = gzip.open(gzip_file_name, 'ab')
    f.write(str(json.dumps(tweet._json)).encode())
    f.write('\n'.encode())


def write_log_file(gzip_file_name, user_json):
    log = open(gzip_file_name + '.json', 'w')
    log.write(json.dumps(user_json, indent=2))


def main():
    # Configure logging
    LOGS_DIR = PATH + 'logs/'
    if not os.path.isdir(LOGS_DIR):
        os.mkdir(LOGS_DIR)
    dt = datetime.datetime.now()
    log_filename = LOGS_DIR + dt.strftime("%m-%d-%y_crawl_specific_users") + ".log"
    logging.basicConfig(filename=log_filename,
                        format='%(levelname)s: %(message)s',
                        level=logging.INFO)
    
    # Log date+time script is run
    logging.info("Date/time: " + dt.strftime("%x") + " " + dt.strftime("%X"))

    # Make sure that directory to put tweets and metadata into exists
    TWEETS_METADATA_DIR = PATH + 'results/users_tweets_metadata/'
    logging.info("Users' tweets and metadata directory: " + TWEETS_METADATA_DIR)
    if not os.path.isdir(TWEETS_METADATA_DIR):
        os.mkdir(TWEETS_METADATA_DIR)

    save_queue = [json.loads(x.strip())
				  for x in gzip.open(PATH + 'data/uids.gz', 'r')]

    progress_bar = tqdm(total=len(save_queue))

    while len(save_queue) > 0:
        user = save_queue.pop()
        gzip_file_name = TWEETS_METADATA_DIR + user + '.json.gz'

        if os.path.exists(gzip_file_name):
            user_json = json.loads(open(gzip_file_name + '.json', 'r').read())
            all_uids = set(user_json['all_uids'])
        else:
            user_json = {
                'user_id': user,
                'front_id': DEFAULT_SINCE_ID,
                'back_id': DEFAULT_SINCE_ID,
                'done': False,
                'all_uids': []
            }

            all_uids = set()

        try:
            set_front = True
            for tweet in tweepy.Cursor(twitter_api.user_timeline, user_id=user,
                                       since_id=user_json['front_id'], count=200).items():
                if tweet.id not in all_uids:
                    if set_front:
                        set_front = False
                        user_json['front_id'] = tweet.id

                    all_uids.add(tweet.id)
                    user_json['back_id'] = tweet.id
                    write_to_file(gzip_file_name, tweet)

            if 'done' not in user_json or not user_json['done']:
                for tweet in tweepy.Cursor(twitter_api.user_timeline, user_id=user,
                                           since_id=DEFAULT_SINCE_ID, max_id=user_json['back_id'], count=200).items():
                    if tweet.id not in all_uids:
                        all_uids.add(tweet.id)
                        user_json['back_id'] = tweet.id
                        write_to_file(gzip_file_name, tweet)

            user_json['done'] = True
            user_json['all_uids'] = list(all_uids)
            write_log_file(gzip_file_name, user_json)
            progress_bar.update(1)

        except tweepy.error.TweepError as e:
            if '404' in str(e):
                user_json['done'] = True
                logging.warning("The URI requested is invalid or the user does not exist: " + user)
                progress_bar.update(1)
            elif '401' not in str(e):
                save_queue.append(user)
            else:
                user_json['done'] = True
                logging.warning("Private account found: " + user)
                progress_bar.update(1)
                
            user_json['all_uids'] = list(all_uids)
            write_log_file(gzip_file_name, user_json)
            auth_tweepy()

        except KeyboardInterrupt:
            print('\n', "Exiting...")

            user_json['all_uids'] = list(all_uids)
            write_log_file(gzip_file_name, user_json)

            exit()

        except:
            print("\nOther error")
            user_json['all_uids'] = list(all_uids)
            write_log_file(gzip_file_name, user_json)

    logging.info("Script has run to completion.\n")


if __name__ == '__main__':
    auth_tweepy()
    main()
