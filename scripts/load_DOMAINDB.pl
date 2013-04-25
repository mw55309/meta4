#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;
use File::Basename;
use lib dirname(__FILE__);

# load the database access credentials
# should be in the same folder as the script
require META4DB;

# print out usage message
unless (@ARGV) {
	print "USAGE: perl load_DOMAINDB.pl --name <domain DB name> --version <domain DB version> --file <domain DB file> --desc <domain DB description>\n\n";
	print "Domain DB name is required\n";
	print "Domain DB version is required\n";
	print "Domain DB file is optional\n";
	print "Domain DB description is optional\n\n";
	print "EXAMPLE: perl load_DOMAINDB.pl --name Pfam-A --version 26.0 --file Pfam-A.hmm --desc 'Pfam-A version 26.0'\n";
	exit;
}

# get options from the command line
my $name = undef;
my $version = undef;
my $file = undef;
my $desc = undef;
GetOptions('name=s' => \$name, 'version=s' => \$version, 'file=s' => \$file, 'desc=s' => \$desc);

# check for valid options
unless (defined $name) {
	warn "Must at least provide a DB name\n";
	exit;
}
unless (defined $version) {
	warn "Must at least provide a DB version\n";
	exit;
}

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# insert the domain database
my $query = "INSERT INTO domain_db(domain_db_name, domain_db_version, domain_db_file, domain_db_description) values('$name','$version','$file','$desc')";
$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

# get the inserted ID
my $id = $dbh->last_insert_id(undef, undef, qw(sample sample_id)) or die "no insert id?";

# print out message
print "Inserted domain DB with id: $id\n";

# dicsonnect from the databse
$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
