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


twitter_api_tokens = [
    ('hash-tag-searcher', {
        'consumer-key': "Nd7J1InJaXN3QRIZLo9Hi3Vcg",
        'consumer-secret': "p5AtH77gdWDRQyfUYUNqhFNPcxaADlzyUjq9b1s0CPooOFT2by",
        'access-token': "1559190498-lfTKYXPu6g83X7aeWp2XkEU0dni3ARuHqZ59ayF",
        'access-token-secret': "3uwnzRv5eHAAhEtDnmvydT13y4BV2gojFnShBJBeGvzj8"
    }),
    ('wordy.news', {
        'consumer-key': "xc5fa8CWl2v9hkYuHOnZNXSxK",
        'consumer-secret': "YqSw2uXCgsOWUoLY8NNPuTeWZ5FVfuenNGBsHEmxX9hMW2Z2gq",
        'access-token': "1559190498-F0hhKbSoia1VJd5QIKq9xoaNor7LpyKe9sBtabW",
        'access-token-secret': "omBBmvulv1YKyMcntgyWP1bsw5FLLi0oqEnqebA42HXjO"
    }),
    ('user-non-bullshit-collector', {
        'consumer-key': "R0VO03XfN2DVr2H7YPCrZsZ4W",
        'consumer-secret': "AEwxPDTtt98mVeSBpNO54EEQtISuoGdb0PwlTeIxwJt2R20upw",
        'access-token': "1559190498-0DdWcfDv13RJ9RhJd8bmNsmBl2xMAuX9SqL4lGb",
        'access-token-secret': "A2BmJNsQl6MSyoQAsH1dPGXXQxx9KIA5SmfEfLoS8Nglt"
    }),
    ('non-bs detector 2', {
        'consumer-key': "NqBkDNnFE843DaKtsFsPJCs2U",
        'consumer-secret': "UbyFnnsJfc3rLkgf7qcoel9QZ8yJtv8FCs1JLySjC9eUIcgMdi",
        'access-token': "1559190498-aSi2gUaawU9KioPU02vyg3ZCBRftxE6oqepyxu7",
        'access-token-secret': "ZDfrZOJ4Sq4ZWqcE3gftpgXqAfh2PWyhLw3rRFUf6nEoH"
    }),
    ('non-bs detector 3', {
        'consumer-key': "3SYAWiIPxfUIi7MBE1jX395J3",
        'consumer-secret': "hfHnHlPT6vky7kTQUuIicFjUjW6jbs4IHRUdrUmtPpJ4xDsYj8",
        'access-token': "1559190498-uaNNsEbTqlXJTEhVLYXYCiNRTo6D2uAmSBtzpSs",
        'access-token-secret': "BZ1Zi2T1HNBwR3Qr8zrQCbvKMaA7TFZW1y5c5cmAdhHyr"
    }),
    ('non-bs detector 4', {
        'consumer-key': "ONFfClIqGKwQATJaX7FzLXQcN",
        'consumer-secret': "5YSrkSsroY8aUucczZbfKbMGlw7KAlQSHvIbqZ6eD4PQlHy369",
        'access-token': "1559190498-sc3IdHJt6adL1HNKhNlAkFG35aYROM7WyCWkpys",
        'access-token-secret': "C9scTPnBgKO2hN5bXoTaLHsZV12XOU00AgJxarrSqs9eg"
    })
]

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