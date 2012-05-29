#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;

unless (@ARGV) {
	print "USAGE: perl load_SAMPLE.pl --name <sample name> --desc <sample description>\n\n";
	print "Sample name is required and should be unique\n";
	print "Sample description is optional\n\n";
	print "EXAMPLE: perl load_SAMPLE.pl --name 'A test sample' --desc 'A completely made up sample from my head'\n";
	exit;
}

my $name = undef;
my $desc = undef;

GetOptions('name=s' => \$name, 'desc=s' => \$desc);

unless (defined $name) {
	warn "Must at least provide a name\n";
	exit;
}

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";
my $query = "INSERT INTO sample(sample_name, sample_description) values('$name','$desc')";
$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

my $id = $dbh->last_insert_id(undef, undef, qw(sample sample_id)) or die "no insert id?";

print "Inserted sample with id: $id\n";

$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
