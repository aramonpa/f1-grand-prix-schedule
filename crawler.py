from itertools import count
import json
import logging.config
import os
import pickle
import sys
import time
import requests
import html_to_json
from constants import * 

class ScheduleCrawler(object):
    def __init__(self, **kwargs):
        defaultAttr = dict(username = '', logDestination = '', logger = None, verbose = 0)

        allowedAttr = list(defaultAttr.keys())
        defaultAttr.update(kwargs)

        for key in defaultAttr:
            if key in allowedAttr:
                self.__dict__[key] = defaultAttr.get(key)

        # Set up a logger
        if self.logger is None:
            self.logger = ScheduleCrawler.getLogger(level=logging.DEBUG, dest=defaultAttr.get('logDestination'), verbose=defaultAttr.get('verbose'))

        self.session = requests.Session()
        self.session.headers = {'user-agent': CHROME_WIN_UA}
        
        self.cookies = None
        self.quit = False        

    def getLogger(level=logging.DEBUG, dest='', verbose=0):
        # Creates a logger
        logger = logging.getLogger(__name__)

        dest +=  '/' if (dest !=  '') and dest[-1] != '/' else ''
        fh = logging.FileHandler(dest + 'f1-schedule.log', 'a')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        fh.setLevel(level)
        logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        sh_lvls = [logging.ERROR, logging.WARNING, logging.INFO]
        sh.setLevel(sh_lvls[verbose])
        
        logger.addHandler(sh)
        logger.setLevel(level)

        return logger

    def scrape(self):
            # Get users information
            #self.session.headers.update({'user-agent': STORIES_UA})

            user = ''
            try:
                # Get the user metadata.
                user = self.getUserInfo(self.username)
                outputJson = html_to_json.convert(user.text)
                # TO DO -- Create test mode
                # Test mode will load json into a file for be more readable
                f = open('test', 'w')
                f.write(json.dumps(outputJson))

                print('eee')

                if not user:
                    self.logger.error('Error getting user details for {0}. Please verify that user.'.format(self.username))

            except ValueError:
                self.logger.error("Unable to scrape user - %s" % self.username)
            finally:
                self.quit = True

            return user

    def getUserInfo(self, username=''):
            # Fetches user metadata
            resp = self.getJson(BASE_URL + username)
            return resp

    def getJson(self, url):
            # Retrieve text from URL. JSON as string
            resp = self.getResponse(url)

            if resp is not None:
                #data = resp.text.split("window._sharedData = ")[1].split(";</script>")[0]
                return resp

    def getResponse(self, url):
            # Gets response from Instagram
            retry = 0
            retryDelay = RETRY_DELAY
            while True:
                if self.quit:
                    return
                try:
                    response = self.session.get(timeout = CONNECT_TIMEOUT, cookies = self.cookies, url = url)
                    if response.status_code == 404:
                        return
                    response.raise_for_status()
                    content_length = response.headers.get('Content-Length')
                    if content_length is not None and len(response.content) != int(content_length):
                        #raise PartialContentException('Partial response')
                        raise
                    return response
                except (KeyboardInterrupt):
                    raise
                #except (requests.exceptions.RequestException, PartialContentException) as e:
                except (requests.exceptions.RequestException) as e:
                    if retry < MAX_RETRIES:
                        self.logger.warning('Retry after exception {0} on {1}'.format(repr(e), url))
                        time.sleep(retryDelay)
                        retryDelay = min(2 * retryDelay, MAX_RETRY_DELAY)
                        retry = retry + 1
                        continue
                    
                    raise

scrape = ScheduleCrawler(username = 'gran-premio-bahrein')
gp = scrape.scrape()