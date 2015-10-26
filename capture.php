<?php

// if the status file does not exits, create it with default 'off'
// if the file exits, read what it says and that's the current status
// if there's weird stuff in there, replace w/ 'off'
$currentStatus = "0";
$filename = "tlstatus.txt";

if(!file_exists($filename)) {
   file_put_contents($filename, "0");
} else {
   $contents = file_get_contents($filename);
   $contents = trim($contents);

   if( $contents == "1" )
      $currentStatus = "1";
   elseif( $contents == "0" )
      $currentStatus = "0";
   else {
      $currentStatus = "0";
      file_put_contents($filename, "0");
   }
}

// if the value is "1" or "0" then if that is different from current status, amend the file
// if the value is "1" or "0" and not different from current status, do nothing
// if the value is not "1" or "0" then the submitted data is no use.
// getting status from the URL allows for a remote stop
if( isset($_GET['status'] )){
   $submittedStatus = trim( $_GET['status'] );
   if( $submittedStatus == "1" ){
      if( $currentStatus == "0" ){
          $currentStatus = "1";
          file_put_contents( $filename, "1" );
      }
   }  elseif( $submittedStatus == "0" ){
      if( $currentStatus == "1" ){
          $currentStatus = "0";
          file_put_contents( $filename, "0" );
      }
   }
}

//display the (maybe new) current status and a link to toggle that status
print "<h2><center>Raspi Timelapse</center></h2>";
if($currentStatus == "1")
  print "<h3 color = green><center>capture is running</center></h3>";
else
  print "<h3 color = red><center>capture is stopped</center></h3>";

print "<br><br>";
print "<hr>";

if($currentStatus == "1")
  print "<a href = 'capture.php?status=0'><h4><center>stop</center></h4></a>";
else
  print "<a href = 'capture.php?status=1'><h4><center>start</center></h4></a>";
?>
