#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;
use File::Basename;
use lib dirname(__FILE__);

# load the database access credentials
# should be in the same folder as the script
require META4DB;

# print out the usage message
unless (@ARGV) {
	print "USAGE: perl load_SAMPLE.pl --name <sample name> --desc <sample description>\n\n";
	print "Sample name is required and should be unique\n";
	print "Sample description is optional\n\n";
	print "EXAMPLE: perl load_SAMPLE.pl --name 'A test sample' --desc 'A completely made up sample from my head'\n";
	exit;
}

# get options from the command line
my $name = undef;
my $desc = undef;
GetOptions('name=s' => \$name, 'desc=s' => \$desc);

# check for valid options
unless (defined $name) {
	warn "Must at least provide a name\n";
	exit;
}

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# insert sample information
my $query = "INSERT INTO sample(sample_name, sample_description) values('$name','$desc')";
$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

# get the last inserted DB and print user message
my $id = $dbh->last_insert_id(undef, undef, qw(sample sample_id)) or die "no insert id?";
print "Inserted sample with id: $id\n";

# disconnect from the database
$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
