#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;

unless (@ARGV) {
	print "USAGE: perl load_DOMAINS.pl --domain_db_id <Domain DB ID> --file <File of domains>\n\n";
	print "Domain DB ID is required and should be the identifer of a domain database in the domain_db table\n";
	print "The file of domains is required.  This should be a plain text file, tab-delimited, with four columns: domain ID, domain Name, domain Length, domain description\n\n";
	print "EXAMPLE: perl load_DOMAINS.pl --domain_db_id 1 --file domains_hit.txt\n";
	exit;
}

my $ddbid = undef;
my $file = undef;

GetOptions('domain_db_id=s' => \$ddbid, 'file=s' => \$file);

unless (defined $ddbid) {
	warn "Must at least provide a domain DB ID\n";
	exit;
}

unless (defined $file && -f $file) {
	warn "Must at least provide a file and file must exist\n";
	exit;
}

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";

open(IN, $file) || die "Cannot open $file\n";
while(<IN>) {
	s/\n|\r//g;
	my($accn,$name,$len,$desc) = split(/\t/);
	my $query = "INSERT INTO domain(domain_db_id, domain_accession, domain_name, domain_length, domain_description) values($ddbid,'$accn','$name',$len,'$desc')";
	$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

}
close IN;

$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
