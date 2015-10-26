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
#
# requires server.config file

import os
import sys
import time
import smtplib
import pysftp

# create dictionary to hold all server, user and pass data
serverConfig = {}

def main( args ) :
  """ just keeping the peace """

  getConfig()
  doUpload( args[1] )
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


def doUpload( putfile ) :
  """ use SFTP to upload the movie file 
  perhaps a log file in the future as well

  Should put a post-upload check in before
  cleaning house"""

  sftp = pysftp.Connection( serverConfig['FTPSERVER'], username=serverConfig['USER'], password=serverConfig['PASS'] ) 
  sftp.cwd( serverConfig['FTPDIR'] )
  sftp.put( putfile )
  sftp.close()

def sendEmail( filepath ) :
  """ send an email regarding the upload and time
  Ideally this will get much more information """

  server = smtplib.SMTP( serverConfig['EMAILSMTP'], 587 )
  server.starttls()
  server.login( serverConfig['EMAILUSER'], serverConfig['EMAILPASS'] )

  dicePath = filepath.split("/")
  msg = "a new movie has been uploaded!\n\n"
  msg = msg + "Movie Name: " + dicePath[-1] + "\n"
  msg = msg + "uploaded on " + time.strftime('%Y-%m-%d %H:%M')

  server.sendmail(serverConfig['EMAILUSER'], serverConfig['EMAILTO'], msg)
  server.quit()
                    

def cleanUp( path ) :
  """ Remove all files, then delete the dir """

  dirlist = os.listdir( path )

  for f in dirlist :
    os.remove(path + "/" + f)
  os.rmdir( path )

  
if __name__ == "__main__" :
    main( sys.argv )
