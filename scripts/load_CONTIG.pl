#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;
use Bio::SeqIO;

unless (@ARGV) {
	print "USAGE: perl load_CONTIG.pl --assembly_id <assembly id> --file <fasta file of sequences>\n\n";
	print "Assembly id is required and should be a unique ID from the sample table\n";
	print "A fasta file of contig sequences should also be provided\n\n";
	print "EXAMPLE: perl load_CONTIF.pl --assembly_id 5 --file /path/to/contigs.fasta\n";
	exit;
}

my $assembly_id = undef;
my $file = undef;

GetOptions('assembly_id=i' => \$assembly_id, 'file=s' => \$file);

unless (defined $assembly_id  && defined $file && -f $file) {
	warn "Must at least provide a name and a file and the file must exist\n";
	exit;
}

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";

my $in = Bio::SeqIO->new(-file => $file, -format => 'fasta');
while(my $seq = $in->next_seq()) {

	my $name = $seq->display_id;
	my $desc = $seq->description;
	my $len  = $seq->length;

	my $query = "INSERT INTO contig(assembly_id, contig_name, contig_desc, contig_length) values($assembly_id,'$name','$desc',$len)";
	$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

}

$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
