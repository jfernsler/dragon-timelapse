#!/usr/bin/python
# gpio.py
#
# Jeremy Fernsler
#   2 - Nov - 2015
#
# Simple GPIO control for LEDs
#   run with sudo
#
# takes the following arguments:
#   READY
#   CAPTURE
#   COMPRESS
#   CAPTURECOMPLETE
#   COMPRESSCOMPLETE
#   NOTREADY

import sys, time
import RPi.GPIO as GPIO

# set the pin numbering method to the board
#   pincount, not BCM (Broadcom chip)
GPIO.setmode( GPIO.BOARD )

# supress warnings about channel usage
GPIO.setwarnings( False )

# Set up LED output pins
GPIO.setup( 11, GPIO.OUT ) # Ready LED
GPIO.setup( 13, GPIO.OUT ) # Compressing LED
GPIO.setup( 15, GPIO.OUT ) # Capture LED

def main () :
  """ Read the argument, if there's more or less than one
  just ignore everything and quit """

  argc = len( sys.argv )

  if argc == 2 :
    changeMode( str( sys.argv[1] ))

def changeMode( mode ) :
  """ take that argument and parse it for the proper response """

  if mode == 'READY' :
    cyclefun()
    GPIO.output( 11, True )
  elif mode == 'CAPTURE' :
    GPIO.output( 15, True )
  elif mode == 'COMPRESS' :
    GPIO.output( 13, True )
  elif mode == 'CAPTURECOMPLETE' :
    GPIO.output( 15, False )
  elif mode == 'COMPRESSCOMPLETE' :
    GPIO.output( 13, False )
  elif mode == 'NOTREADY' :
    GPIO.output( 11, False )
  elif mode == 'Q' :
    ready = GPIO.input(11)
    capture = GPIO.input(13)
    compress = GPIO.input(15)
    print "Ready: %d  Capture: %d  Compress: %d" % ( ready, capture, compress )
  elif mode == 'HEARTBEAT' :
    ready = GPIO.input(11)
    capture = GPIO.input(13)
    compress = GPIO.input(15)

    cyclefun()

    GPIO.output( 11, ready )
    GPIO.output( 13, capture )
    GPIO.output( 15, compress )

def cyclefun() :
  """ this just does a quick cycle animation on the lights
  nothing special, just a little extra on startup """

  GPIO.output( 11, False )
  GPIO.output( 13, False )
  GPIO.output( 15, False )

  time.sleep(.15)

  for i in range(2) :
    GPIO.output( 15, True )
    time.sleep(.15)
    GPIO.output( 15, False )
    GPIO.output( 13, True )
    time.sleep(.15)
    GPIO.output( 13, False )
    GPIO.output( 11, True )
    time.sleep(.15)
    GPIO.output( 11, False)

if __name__ == "__main__" :
  main()
