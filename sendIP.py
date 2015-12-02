#!/usr/bin/python
# uploadCleanup.py
#
# Jeremy Fernsler
#   2-Dec-2015
#
# sends current IP address to email
#
# requires server.config file

import os
import sys
import time
import string
import smtplib

# create dictionary to hold all server, user and pass data
serverConfig = {}

def main( args ) :
  """ just keeping the peace """
  getConfig()
  sendIP()


def getIP() :
  #f = os.popen('ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1')
  f = os.popen('ifconfig eth0')
  return f.read()

def getConfig() :
    """ get the servers, user, and pass info from
      and external config file"""

    global serverConfig

    f = open("/home/pi/dragon-timelapse/server.config", "r")
    l = f.readline()

    while l :
      l = l.strip( " \t\n" )
      data = l.split( ":", 1)
      serverConfig[ data[0] ] = data[1]
      l = f.readline()
    f.close

def sendIP() :
  """ send an email with the appropriate info. 
  Email addresses, servers and passwords come from external config file.
  Same file as sftp information. """

  # Repeating some vars for clarity.
  # To is comma seperated, so we need to bracket it later
  emailto = serverConfig['EMAILTO']
  emailfrom = serverConfig['EMAILUSER']
  emailpass = serverConfig['EMAILPASS']
  #dicePath = filepath.split("/")
  subj = "Dragon Timelapse IP Update!"
  msg = "A new IP has been aquired!\n\n"
  msg = msg + "IP: " + getIP()
  msg = msg + "\nEnjoy!\n\n"
  msg = msg + "Your Friend,\nDragon Timelapse\n"

  body = string.join((
    "From: %s" % emailfrom, 
    "To: %s" % emailto, 
    "Subject: %s" % subj, 
    "", msg), "\r\n")
  
  server = smtplib.SMTP( serverConfig['EMAILSMTP'], 587 )
  server.starttls()
  server.login( emailfrom, emailpass )
  server.sendmail( emailfrom, [emailto], body )
  server.quit()

if __name__ == "__main__" :
    main( sys.argv )
