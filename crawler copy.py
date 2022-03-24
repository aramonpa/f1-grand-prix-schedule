from itertools import count
import json
import logging.config
import os
import pickle
import string
import sys
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from html2image import Html2Image
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
        try:
            # Get the user metadata.
            user = self.getUserInfo(self.username)

            # TO DO -- Create test mode
            # Test mode will load json into a file for be more readable
            f = open('test', 'w')
            f.write(json.dumps(user))

            if not user:
                self.logger.error('Error getting user details for {0}. Please verify that user.'.format(self.username))

        except ValueError:
            self.logger.error("Unable to scrape user - %s" % self.username)
        finally:
            self.quit = True

        return user

    def getUserInfo(self, username=''):
        # Fetches user metadata
        resp = self.getJson(BASE_URL)
        return resp

    def getJson(self, url):
            # Retrieve text from URL. JSON as string
            resp = self.getResponse(url)

            if resp is not None:
                return self.convertToJson(resp.text)['MRData']['RaceTable']
    
    def convertToJson(self, text):
        # Convert text into JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            self.logger.error('Text is not json: ' + text)
            raise

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

    def formatSchedule(self, data):
        circuit = data['Races'][0]['Circuit']['circuitName']
        freePracticeOneDate = ((datetime.strptime(data['Races'][0]['FirstPractice']['date'].replace('Z', ''), '%Y-%m-%d')))
        freePracticeOneTime = ((datetime.strptime(data['Races'][0]['FirstPractice']['time'].replace('Z', ''), '%H:%M:%S')) + timedelta(hours=1))
        freePracticeTwoDate = ((datetime.strptime(data['Races'][0]['SecondPractice']['date'].replace('Z', ''), '%Y-%m-%d')))
        freePracticeTwoTime = ((datetime.strptime(data['Races'][0]['SecondPractice']['time'].replace('Z', ''), '%H:%M:%S')) + timedelta(hours=1))
        freePracticeThreeDate = ((datetime.strptime(data['Races'][0]['ThirdPractice']['date'].replace('Z', ''), '%Y-%m-%d')))
        freePracticeThreeTime = ((datetime.strptime(data['Races'][0]['ThirdPractice']['time'].replace('Z', ''), '%H:%M:%S')) + timedelta(hours=1))
        qualyDate = ((datetime.strptime(data['Races'][0]['Qualifying']['date'].replace('Z', ''), '%Y-%m-%d')))
        qualyTime = ((datetime.strptime(data['Races'][0]['Qualifying']['time'].replace('Z', ''), '%H:%M:%S')) + timedelta(hours=1))
        raceDate = ((datetime.strptime(data['Races'][0]['date'].replace('Z', ''), '%Y-%m-%d')))
        raceTime = ((datetime.strptime(data['Races'][0]['time'].replace('Z', ''), '%H:%M:%S')) + timedelta(hours=1))

        return {'circuit': circuit,
                'freePracticeOneDate': freePracticeOneDate,
                'freePracticeOneTime': freePracticeOneTime,
                'freePracticeTwoDate': freePracticeTwoDate,
                'freePracticeTwoTime': freePracticeTwoTime,
                'freePracticeThreeDate': freePracticeThreeDate,
                'freePracticeThreeTime': freePracticeThreeTime,
                'qualyDate': qualyDate,
                'qualyTime': qualyTime,
                'raceDate': raceDate,
                'raceTime': raceTime}

    def getSchedule(self):
        data = self.scrape()
        return self.formatSchedule(data)

scrape = ScheduleCrawler(username = 'gran-premio-bahrein')
schedule = scrape.getSchedule()

background = Image.open('assetts\images\F1-2022-1.jpg')
circuitFnt = ImageFont.truetype('C:\\Windows\\Fonts\\ariblk.ttf', 70)
fnt = ImageFont.truetype('C:\\Windows\\Fonts\\arial.ttf', 45)
img = ImageDraw.Draw(background)

circuitWidth, circuitHeigh = circuitFnt.getsize(schedule['circuit'])
""""
img.text(((1920 - circuitWidth) / 2, 240), schedule['circuit'], font=circuitFnt, fill=(255, 255, 255))
img.text((130, 520), schedule['freePracticeOneTime'] + 'h  Libres 1', font=fnt, fill=(255, 255, 255))
img.text((130, 570), schedule['freePracticeTwoTime'] + 'h  Libres 2', font=fnt, fill=(255, 255, 255))
img.text((739, 520), schedule['freePracticeThreeTime'] + 'h  Libres 3', font=fnt, fill=(255, 255, 255))
img.text((739, 570), schedule['qualyTime'] + 'h  Clasificación', font=fnt, fill=(255, 255, 255))
img.text((1360, 520), schedule['qualyTime'] + 'h  Carrera', font=fnt, fill=(255, 255, 255))
"""

#print(background.show())
with open("assetts\\components\\schedule.html") as f:
    htmlString = f.read()

htmlString = htmlString.format(
    circuit = schedule['circuit'],
    pDayOne = schedule['freePracticeOneDate'].strftime('%d'),
    pMonthOne = schedule['freePracticeOneDate'].strftime('%b'),
    pHourOne = schedule['freePracticeOneTime'].strftime('%H:%M'),
    pDayTwo = schedule['freePracticeTwoDate'].strftime('%d'),
    pMonthTwo = schedule['freePracticeTwoDate'].strftime('%b'),
    pHourTwo = schedule['freePracticeTwoTime'].strftime('%H:%M'),
    pDayThree = schedule['freePracticeThreeDate'].strftime('%d'),
    pMonthThree = schedule['freePracticeThreeDate'].strftime('%b'),
    pHourThree = schedule['freePracticeThreeTime'].strftime('%H:%M'),
    qDay = schedule['qualyDate'].strftime('%d'),
    qMonth = schedule['qualyDate'].strftime('%b'),
    qHour = schedule['qualyTime'].strftime('%H:%M'),
    rDay = schedule['raceDate'].strftime('%d'),
    rMonth = schedule['raceDate'].strftime('%b'),
    rHour = schedule['raceTime'].strftime('%H:%M'))

hti = Html2Image()
hti.screenshot(html_str=htmlString, css_file='assetts\components\schedule.css', save_as='out.png', size=(1920, 1080)) #550 x 590

png = Image.open('out.png')

#wide one is 565
#vertical one is 400x650
area = (0, 0, 565, 565)
croppedPng = png.crop(area)
croppedPng.show()
croppedPng.save('easy.png')


#hti.screenshot(html_file='assetts\components\schedule.html', css_file='assetts\components\schedule.css', save_as='out.png', size=(350, 440))
