#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;

unless (@ARGV) {
	print "USAGE: perl load_PFAMSCAN.pl --domain_db_id <Domain DB ID> --assembly_id <Assembly ID> --file <Output from Pfam scan>\n\n";
	print "Domain DB ID is required and should be unique\n";
	print "Assembly ID is required and should be the assembly that produced the gene prediction gene_names that appear in the pfam scan output\n";
	print "The output of a pfam_scan.pl run is required\n\n";
	print "EXAMPLE: perl load_PFAMSCAN.pl --domain_db_id 1 --assembly_id 1 --file examples/pfam.out\n";
	exit;
}

my $ddbid = undef;
my $file = undef;
my $aid = undef;

GetOptions('domain_db_id=s' => \$ddbid, 'file=s' => \$file, 'assembly_id=s' => \$aid);

unless (defined $ddbid) {
	warn "Must at least provide a domain DB ID\n";
	exit;
}

unless (defined $file && -f $file) {
	warn "Must at least provide a file and file must exist\n";
	exit;
}

unless (defined $aid) {
	warn "Must at least provide an assembly ID\n";
	exit;
}

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";

# get domains so far
my %dmap;
my $query = "Select domain_id, domain_accession from domain where domain_db_id = $ddbid";
my $sth = $dbh->prepare($query);
$sth->execute;
while(my($did,$name) = $sth->fetchrow_array) {
	$dmap{$name} = $did;
}
$sth->finish;

# get gene prediction gene_names for the given assembly
my %gmap;
my $query = "Select gp.gene_prediction_id, gp.gene_name from gene_prediction gp, contig c where gp.contig_id = c.contig_id and c.assembly_id = $aid";
my $sth = $dbh->prepare($query);
$sth->execute;
while(my($gid,$name) = $sth->fetchrow_array) {
	$gmap{$name} = $gid;
}
$sth->finish;

open(IN, $file) || die "Cannot open $file\n";
while(<IN>) {
	next if (m/^\#/);
	next if (m/^\s/);
	s/\n|\r//g;
	my @data = split(/\s+/);

	unless (exists $dmap{$data[5]}) {
		warn "Could not find $data[5] in dmap for $ddbid\n";
		next;
	}

	my $did = $dmap{$data[5]};

	unless (exists $gmap{$data[0]}) {
		warn "Could not find $data[0] in gmap for $aid\n";
		next;
	}

	my $gid = $gmap{$data[0]};

	my $query = "INSERT INTO domain_match(domain_id, gene_prediction_id, aln_start, aln_end, domain_start, domain_end, e_value, bit_score) values($did,$gid,$data[1],$data[2],$data[8], $data[9],$data[12], $data[11])";
	$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

}
close IN;

$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
