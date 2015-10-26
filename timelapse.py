#!/usr/bin/python
# timelapse.py
#
# Jeremy Fernsler
#   25 - Oct - 2015
#
# Dynamic timelapse capture program
# begins with .5 second captures and after 1200 captures
# deletes every other photo and continues with dealy*2
#
# upon completion, image sequence is assembled into a movie
# using ffmpeg (external shell command)
# 
# movie is uploaded via sftp, directories are cleaned up
# and an email notification is sent out (external python program)
#
# requires external cam.config file for now

import os
import sys
import time
import datetime as dt
import threading
import urllib2
import picamera

# set up email, ftp, and server vars
CMDURL = "http://www.jfernsler.com/timelapse/tlstatus.txt"
STATUS = "IDLE"
CHECKINTERVAL = 10

#set up file naming conventions
CWD = os.getcwd() # change this to static location
DATENAME = str( int( time.time() ))
IMGDIR = CWD + "/" + DATENAME 
IMGNAME = "imgseq_"
FORMAT = "jpg"

#set up any other constants
MAXSEQCOUNT = 1200
DELAY = 0.5 

# initialize a dictonary for camera configuration vars
configSet = {}

# initialize Raspi Camera
camera = picamera.PiCamera()


def main() :
  """ Main parses the optional argv and starts the process. 
  any errors will gracefully exit out"""

  global MAXSEQCOUNT 

  argc = len( sys.argv )

  if argc is 1 :
    waitToBegin()
  elif argc is 2 :
    MAXSEQCOUNT = int( sys.argv[1] )
    waitToBegin()
  else :
    print "Usage: " + argv[0] + " [<max frame count>]"
  


def checkStatus() :
  """ checkStatus will tap on a file via http and check for a 
  change in status. Reading 1 will set STATUS to START
  0 will set it to STOP
  Called from waitToBegin and runTimelapse"""

  global STATUS

  r = urllib2.urlopen( CMDURL ).read(1)

  if r == "1" :
    STATUS = "START"
  else :
    STATUS = "STOP"


def waitToBegin() :
  """ waitToBegin will sit in a loop, periodically asking
  check status to see if anything has changed. If it has, 
  it sets everything in in motion
  Called from main and runTimelapse"""

  while STATUS is not "START" :
    time.sleep(5)
    checkStatus()
    print "Status result is: ", STATUS
  
  if STATUS is "START" :
    runTimelapse()

def runTimelapse() :
  """ The actual capturing meat and potatoes. Once initiated,
  runTimelapse will generate a directory and capture stills into there.
  Once status has been changed to stop, it initiates the rest of the actions. """

  global STATUS
  global DELAY
  
  if not os.path.exists( IMGDIR ):
    print "making dir!"
    os.makedirs( IMGDIR )
    initCamera()

  # capture until MAXCOUNT and then delete half and continue
  i = 0
  lastTime = int( time.time() )
  while STATUS is "START" :
    if i <= MAXSEQCOUNT :
      time.sleep(DELAY)
      takePhoto( i )
      i = i + 1
    else :
      i = removeEvenPics()
      DELAY = DELAY * 2

    # launch thread to check status if it's been long enough
    if int( time.time() ) - lastTime > CHECKINTERVAL :
      t = threading.Thread( target = checkStatus )
      t.daemon = True
      t.start()
      lastTime = int( time.time() )
      
  #camera.close()
  # finish up.
  compressFiles( )
  waitToBegin()


def initCamera() :
  """ initCamera reads an external config file for the camera and loads it
  into a dictionary that is used to set the static camera settings """

  global configSet

  f = open("cam.config", "r")

  l = f.readline()

  while l:
    l = l.strip( " \t\n" )
    data = l.split( ":", 1)

    configSet[ data[0] ] = data[1]
    l = f.readline()
  f.close

  camera.sharpness = int( configSet['sharpness'] )
  camera.contrast = int( configSet['contrast'] )
  camera.brightness = int( configSet['brightness'] )
  camera.saturation = int( configSet['saturation'] )
  camera.iso = int( configSet['iso'] )
  camera.video_stabilization = configSet['video_stabilization']
  camera.exposure_compensation = int(configSet['exposure_compensation'])
  camera.exposure_mode = configSet['exposure_mode']
  camera.meter_mode = configSet['meter_mode']
  camera.awb_mode = configSet['awb_mode']
  camera.image_effect = configSet['image_effect']
  camera.rotation = int( configSet['rotation'] )
  camera.drc_strength = configSet['drc_strength']
  camera.shutterspeed = int( configSet['shutterspeed'] )
  camera.resolution = ( int( configSet['resX']), int( configSet['resY']) )
  camera.crop = (0.0, 0.0, 1.0, 1.0)


def takePhoto( num ) :
  """ Take a photo and add overlay information"""

  camera.annotate_background = picamera.Color('black')
  camera.annotate_text_size = 32
  camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  camera.capture( IMGDIR + "/" + IMGNAME + "%04d." % num + FORMAT )

def removeEvenPics() :
  """ remove every other image from a directory """

  fname = []
  
  for (dirpath, dirnames, filenames) in os.walk( IMGDIR ):
    fname.extend( filenames )
    break

  fname.sort()

  for i in range( len( fname )):
    if i % 2 == 0:
      os.remove( IMGDIR + "/" + fname[ i ])

  return renumberPics()


def renumberPics() :
  """ Grab all the images in a directory, sort them and
      renumber them to keep them sequential"""

  fname = []

  for (dirpath, dirnames, filenames) in os.walk(IMGDIR):
    fname.extend(filenames)
    break

  fname.sort()

  for i in range( len( fname )):
    oldFile = IMGDIR + "/" + fname[ i ]
    newFile = IMGDIR + "/" + IMGNAME + "%04d." % i + FORMAT
    os.rename ( oldFile, newFile )

  # send back the number to continue on
  return len( fname )
  
def compressFiles( ) :
  """ compressFiles calls an external shell script to lanch
  an ffmpeg compression scheme on the img sequence. """

  os.system( "./ffmpegCmd " + IMGDIR + " " + DATENAME + " &")

if __name__ == "__main__" :
  main()


