#!/usr/bin/python
# timelapse.py
#
# Jeremy Fernsler
#   1 - Nov - 2015
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
# requires picamera to be installed
# requires external cam.config file

import os, sys, time
from subprocess import call
import datetime as dt
import threading
import urllib2
import picamera

# setup URL vars, update state and interval in seconds
CMDURL = "http://www.jfernsler.com/timelapse/tlstatus.txt"
STATUS = "STOP"
CHECKINTERVAL = 10
BASEINTERVAL = CHECKINTERVAL

# set up a time interval for a basic heartbeat check
#   if the LEDs don't cycle after this period, something is wrong
HEARTINTERVAL = 120

# set up file naming conventions
CWD = os.getcwd() # change this to static location
MOVNAME = ""
IMGDIR = ""
IMGNAME = "imgseq_"
FORMAT = "jpg"

# set up any other constants
# MAXSEQCOUNT of 1200 ensures a timelapse no longer than
#   40 seconds at 30fps. 
MAXSEQCOUNT = 1200
DELAY = 0.5 


# initialize Raspi Camera
camera = picamera.PiCamera()

def main() :
  """ Main parses the optional argv and starts the process. 
  any errors will gracefully exit out"""

  global MAXSEQCOUNT 

  argc = len( sys.argv )

  if argc is 1 :
    os.popen( "sudo python ./gpio.py READY" )
    waitToBegin()
  elif argc is 2 :
    MAXSEQCOUNT = sys.argv[1]
    if MAXSEQCOUNT.isdigit() :
      MAXSEQCOUNT = int( MAXSEQCOUNT )
      os.popen( "sudo python ./gpio.py READY" )
      waitToBegin()
    else :
      print "Usage: " + argv[0] + " [<max frame count>]"
  else :
    print "Usage: " + argv[0] + " [<max frame count>]"
  


def checkStatus() :
  """ checkStatus will tap on a file via http and check for a 
  change in status. Reading 1 will set STATUS to START
  0 will set it to STOP
  Called from waitToBegin and runTimelapse"""

  global STATUS
  global CHECKINTERVAL 

  headers = { 'User-Agent' : 'Mozilla/5.0' }
  request = urllib2.Request( CMDURL, None, headers )
  # try to connect, if the connection is refused, try catching
  # the error
  try :
    r = urllib2.urlopen( request ).read(1)
    CHECKINTERVAL = BASEINTERVAL
    if r == "1" :
      STATUS = "START"
    else :
      STATUS = "STOP"
  except : 
    CHECKINTERVAL = CHECKINTERVAL * 5
    print "long delay: reset"

  print STATUS


def waitToBegin() :
  """ waitToBegin will sit in a loop, periodically asking
  check status to see if anything has changed. If it has, 
  it sets everything in in motion
  Called from main and runTimelapse"""

  lastTime = int( time.time() )
  hbTime = lastTime

  while STATUS is not "START" :
    # launch thread to check status if it's been long enough
    if int( time.time() ) - lastTime > CHECKINTERVAL :
      t = threading.Thread( target = checkStatus )
      t.daemon = True
      t.start()
      lastTime = int( time.time() )
    if int( tim.time() ) - hbTime > HEARTINTERVAL : 
      os.popen( "sudo python ./gpio.py HEARTBEAT" )
      hbTime = int( time.time() )
    time.sleep( 10 )

  if STATUS is "START" :
    runTimelapse()

def setNames( ) :
  """ a function to set the names of the movie and the capture directory.
  Sets the name to epoch time. Perhaps in the future this name will be 
  captured from the STATUS file which is read remotely """

  global MOVNAME
  global IMGDIR

  MOVNAME = str( int( time.time() ))
  IMGDIR = CWD + "/" + MOVNAME 

def runTimelapse() :
  """ The actual capturing meat and potatoes. Once initiated,
  runTimelapse will generate a directory and capture stills into there.
  Once status has been changed to stop, it initiates the rest of the actions. """

  global STATUS

  captureDelay = DELAY
  
  setNames()

  if not os.path.exists( IMGDIR ):
    os.makedirs( IMGDIR )

  shutSpeed = initCamera()

  os.popen( "sudo python ./gpio.py CAPTURE" )

  # initialize looping var, initialize the url check interval
  # grab the start time for the timelapse log
  i = 0
  lastTime = int( time.time() )
  tlstart = time.strftime('%Y-%m-%d %H:%M')
  print "Capture beginning at: %s" % tlstart

  # capture until MAXCOUNT and then delete half and continue
  while STATUS is "START" :
    if i <= MAXSEQCOUNT :
      time.sleep( captureDelay )
      takePhoto( i, captureDelay )
      i = i + 1
    else :
      i = removeEvenPics()
      #shutSpeed = shutSpeed / 2
      captureDelay = captureDelay * 2

    # launch thread to check status if it's been long enough
    if int( time.time() ) - lastTime > CHECKINTERVAL :
      t = threading.Thread( target = checkStatus )
      t.daemon = True
      t.start()
      lastTime = int( time.time() )
      
  os.popen( "sudo python ./gpio.py CAPTURECOMPLETE" )

  # get the end time for the timelapse
  tlend = time.strftime('%Y-%m-%d %H:%M')
  print "Capture complete at: " + tlend
  # finish up.
  compressFiles( tlstart, tlend )
  waitToBegin()


def initCamera() :
  """ initCamera reads an external config file for the camera and loads it
  into a dictionary that is used to set the static camera settings. 
  Camera opens it's shutter and settles into a few gain settings,
  those are read and the process is locked to avoid flicker """

  # initialize a dictonary for camera configuration vars
  configSet = {}

  f = open("cam.config", "r")
  l = f.readline()
  while l:
    l = l.strip( " \t\n" )
    data = l.split( ":", 1)

    configSet[ data[0] ] = data[1]
    l = f.readline()
  f.close

  # set some of the things we can definately lock down.
  camera.iso = int( configSet['iso'] )
  camera.resolution = ( int( configSet['resX']), int( configSet['resY']) )
  camera.vflip = configSet['vflip']
  camera.hflip = configSet['hflip']
  camera.sharpness = int( configSet['sharpness'] )
  camera.drc_strength = configSet['drc_strength']
  camera.crop = (0.0, 0.0, 1.0, 1.0)

  # open up the camera shutter and let the more dynamic settings
  #  settle into place for the current conditions before locking them.
  camera.start_preview()
  time.sleep(2)
  camera.shutter_speed = camera.exposure_speed
  camera.exposure_mode = 'off'
  g = camera.awb_gains
  camera.awb_mode = 'off'
  camera.awb_gains = g
  camera.stop_preview()

  return camera.shutter_speed


def takePhoto( num, delay ) :
  """ Take a photo and add overlay information"""

  camera.annotate_background = picamera.Color('black')
  camera.annotate_text_size = 16
  annText = MOVNAME + " : " + dt.datetime.now().strftime('%m-%d-%Y %H:%M:%S') + " -- Delay: %.2f" % delay
  camera.annotate_text = annText
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
  
def compressFiles( tlstart, tlend ) :
  """ compressFiles calls an external shell script to lanch
  an ffmpeg compression scheme on the img sequence. """

  # print "./ffmpegCmd %s %s \"%s\" \"%s\" &" % (IMGDIR, MOVNAME, tlstart, tlend)
  os.system( "./ffmpegCmd %s %s \"%s\" \"%s\" &" % (IMGDIR, MOVNAME, tlstart, tlend) )

if __name__ == "__main__" :
  main()


