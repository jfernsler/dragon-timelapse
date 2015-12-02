#!/usr/bin/python
# uploadCleanup.py
#
# Jeremy Fernsler
#   25-Oct-2015
#
# upload the movie via sftp
# notify others with log of stats
# clean up after
#
# takes 2 arguments
# 1. the file path
# 2. the dir it resides in
# 3. the log file for the movie
#
# requires server.config file

import os
import sys
import time
import string
import smtplib
import pysftp
import shutil

# create dictionary to hold all server, user and pass data
serverConfig = {}

mvdir = "/home/pi/Movies/"

def main( args ) :
  """ just keeping the peace """

  getConfig()
  doUpload( args[1], args[3] )
  #mvMovie( args[1], args[3] )
  sendEmail( args[1] )
  cleanUp( args[2] )


def getConfig() :
  """ get the servers, user, and pass info from
  and external config file"""

  global serverConfig

  f = open("server.config", "r")
  l = f.readline()

  while l :
    l = l.strip( " \t\n" )
    data = l.split( ":", 1)
    serverConfig[ data[0] ] = data[1]
    l = f.readline()
  f.close


def mvMovie( mvfile, mvlog ) :
 shutil.move( mvfile, mvdir )
 shutil.move( mvlog, mvdir )



def doUpload( putfile, putlog ) :
  """ use SFTP to upload the movie file 
  perhaps a log file in the future as well

  Should put a post-upload check in before
  cleaning house"""

  sftp = pysftp.Connection( serverConfig['FTPSERVER'], username=serverConfig['USER'], password=serverConfig['PASS'] ) 
  sftp.cwd( serverConfig['FTPDIR'] )
  sftp.put( putfile )
  sftp.put( putlog )
  
  # append logfile here just for records
  with open( "SFTP_log", "a" ) as logfile:
    logfile.write( "Upload completed on: %s\n" % time.strftime( '%Y-%m-%d %H:%M' ))
    logfile.write( "Upload dir list: \n" )
    for item in sftp.listdir() :
      logfile.write( item + "\n" )
    logfile.write( "Closing connection\n\n" )
  sftp.close()

def sendEmail( filepath ) :
  """ send an email with the appropriate info. 
  Email addresses, servers and passwords come from external config file.
  Same file as sftp information. """

  # Repeating some vars for clarity.
  # To is comma seperated, so we need to bracket it later
  emailto = serverConfig['EMAILTO']
  emailfrom = serverConfig['EMAILUSER']
  emailpass = serverConfig['EMAILPASS']
  #dicePath = filepath.split("/")
  subj = "Dragon Timelapse Upload Update!"
  msg = "A new Movie has been uploaded!\n\n"
  msg = msg + "Movie Name: " + filepath.split("/")[-1] + "\n"
  msg = msg + "uploaded on " + time.strftime('%Y-%m-%d %H:%M')
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

def cleanUp( path ) :
  """ Remove all files, then delete the dir """

  for root, dirs, files in os.walk( path, topdown=False ):
    for name in files :
      os.remove( os.path.join( root, name ))
    for name in dirs :
      os.rmdir( os.path.join( root, name ))
  os.rmdir( path )

  
if __name__ == "__main__" :
    main( sys.argv )
