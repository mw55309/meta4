#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;

unless (@ARGV) {
	print "USAGE: perl load_DOMAINDB.pl --name <domain DB name> --version <domain DB version> --file <domain DB file> --desc <domain DB description>\n\n";
	print "Domain DB name is required\n";
	print "Domain DB version is required\n";
	print "Domain DB file is optional\n";
	print "Domain DB description is optional\n\n";
	print "EXAMPLE: perl load_DOMAINDB.pl --name Pfam-A --version 26.0 --file Pfam-A.hmm --desc 'Pfam-A version 26.0'\n";
	exit;
}

my $name = undef;
my $version = undef;
my $file = undef;
my $desc = undef;

GetOptions('name=s' => \$name, 'version=s' => \$version, 'file=s' => \$file, 'desc=s' => \$desc);

unless (defined $name) {
	warn "Must at least provide a DB name\n";
	exit;
}

unless (defined $version) {
	warn "Must at least provide a DB version\n";
	exit;
}

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";
my $query = "INSERT INTO domain_db(domain_db_name, domain_db_version, domain_db_file, domain_db_description) values('$name','$version','$file','$desc')";
$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

my $id = $dbh->last_insert_id(undef, undef, qw(sample sample_id)) or die "no insert id?";

print "Inserted domain DB with id: $id\n";

$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
