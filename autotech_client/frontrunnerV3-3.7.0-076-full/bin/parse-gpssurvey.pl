#!/usr/bin/perl
$num_args = $#ARGV + 1;
if ($num_args != 1) {
  print "Missing Argument\nUsage: parse-gpssurvey.pl filename\n";
  exit;
}

$filename=$ARGV[0];
open FILE, $filename or die $!;
while (my $line = <FILE>) 
{
    if ( $line =~ /(.*)->(.*)GPS-POSITION-MSG\((.*)\)/ )
    {
    print "$1,$3\n";

    }
}
close FILE;
