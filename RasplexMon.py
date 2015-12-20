#!/usr/bin/env python
import datetime
import time
import urllib2
import xml.etree.ElementTree as ET
from os.path import expanduser
import logging
import logging.handlers
import httplib
import urllib
from phue import Bridge
import random
from soco import SoCo
from unidecode import unidecode

### Mini-Config
ignoreAlertList = [] #myPlex usernames with disabled alerting. Will still be logged.

logLocation = '/storage/downloads/plexMon.log' # directory with write-access to store the log
HueBridge = '192.168.1.109' #IP of HueBridge
SonosSpeaker = '192.168.1.105' #IP of Sonos Speaker
neueralarm = 10800 # After this many hours (10800sec = 3h) we will alert again, even if we have seen the session before
PlexPassurl = 'http://192.168.1.119:32400/status/sessions' # The URL to the Plex-Session XML (PlexPass Required)
mainuser = "Peter" #Username of the user who's speakers and ligth schould be automated



# We send iOS-Push-Messages via Pushover

def sendAlert(alertText):

  conn = httplib.HTTPSConnection("api.pushover.net")
  conn.request("POST", "/1/messages.json",
    urllib.urlencode({
      "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # Pushover Application Token
      "user": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # Pushover User ID
      "title": 'Plex',
      "message": alertText,
      "sound": "intermission",
    }), {"Content-type": "application/x-www-form-urlencoded"})
  conn.getresponse()



now = datetime.datetime.now() #What time do we have
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=logLocation, level=logging.INFO)

log = open(logLocation).read() # read log
log_lines = open(logLocation).readlines() # read log file as a list[] of lines

server = urllib2.urlopen(PlexPassurl)
data = server.read()
server.close()

tree = ET.fromstring(data)
for video in tree.iter('Video'):
  show = video.get('grandparentTitle')
  episode = video.get('title')
  if show is None:
    title = episode
    user = video.find('User').get('title').split('@')[0]
  else:
    title = '%s - %s' % (show, episode)
    user = video.find('User').get('title').split('@')[0]
  alert = '%s schaut %s' % (user, unidecode(title))
  print alert #for debug purposes
  if alert in log:
    for line in log_lines:
        if(line.__contains__(alert)):
            partsOfLine = str(line).split()
            dateParts = str(partsOfLine[0]).split("-")
            timeParts = str(partsOfLine[1]).split(":")
            alerttime = datetime.datetime(int(dateParts[0]),int(dateParts[1]),int(dateParts[2]),int(timeParts[0]),int(timeParts[1]),int(timeParts[2]))
            gesehenam = time.mktime(alerttime.timetuple())
            geradejetzt = time.mktime(now.timetuple()) 
            timediff_in_sec = (geradejetzt - gesehenam)
            if(timediff_in_sec >= neueralarm):
                print "more than 3 hours have passed, since last seen"
                alter = True
            else:
                print "less than 3 hours have passed, since last seen"
                alter = False
  if (alert not in log) or (alert in log and alter):
    logging.info(alert)
    if all(i not in alert for i in ignoreAlertList):
      sendAlert(alert)
      if user == mainuser:
          b = Bridge(HueBridge) 
          b.set_light(1, 'bri', 50) #reduce Philips HUE brightness
          my_zone = SoCo(SonosSpeaker)
          my_zone.volume = 0 #Silence Sonos Speaker