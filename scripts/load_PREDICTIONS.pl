#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;
use Bio::SeqIO;
use File::Basename;
use lib dirname(__FILE__);

# load the database access credentials
# should be in the same folder as the script
require META4DB;

# print out usage message
unless (@ARGV) {
	print "USAGE: perl load_PREDICTIONS.pl --assembly_id <assembly ID> --gff <GFF/GTF file of gene predictions> --nucfile <nucleotide FASTA file> --profile <protein FASTA file>\n\n";
	print "Assembly ID should be an assembly ID from the assembly table\n";
	print "GFF should be a GFF/or GTF file of gene predictions.  One gene prediction per line.  Same order as nucleotide and protein FASTA file\n";
	print "Nucleotide FASTA file consisting of the nucleotide sequences of the gene predictions.  Same order as protein and GFF file\n";
	print "Protein FASTA file consisting of the protein sequences of the gene predictions.  Same order as nucleotide and GFF file\n\n";
	print "EXAMPLE: perl load_PREDICTIONS.pl --assembly_id 1 --gff examples/predictions.gtf --nucfile examples/nucs_out.fasta --profile examples/prots_out.fasta\n";
	exit;
}

# get options from the command line
my $assembly_id = undef;
my $nucfile     = undef;
my $profile     = undef;
my $gff         = undef;
GetOptions('assembly_id=s' => \$assembly_id, 'nucfile=s' => \$nucfile, 'profile=s' => \$profile, 'gff=s', \$gff);

# check for valid options
unless (defined $assembly_id) {
	warn "Must at least provide a name\n";
	exit;
}
unless (-f $nucfile) {
	warn "Must provide a nucleotide fasta file for predictions\n";
	exit;
}
unless (-f $profile) {
	warn "Must provide a protein fasta file for predictions\n";
	exit;
}
unless (-f $gff) {
	warn "Must provide a gff file of features\n";
	exit;
}

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# build a hash of contigs for this assembly
# keyed by contig name
my %cmap;
my $sql = "select contig_id, contig_name from contig where assembly_id = $assembly_id";
my $sth = $dbh->prepare($sql);
$sth->execute;
while (my($id,$name) = $sth->fetchrow_array) {
	$cmap{$name} = $id;
}
$sth->finish;

# open the nucleotide and protein files
# using BioPerl
my $nuc = Bio::SeqIO->new(-file => $nucfile);
my $pro = Bio::SeqIO->new(-file => $profile);

# iterate over the GFF file
my $gcount = 0;
open(GFF, "$gff") || die "Cannot open $gff\n";
while(<GFF>) {

	# skip comments
	next if (m/^#/);

	# get rid of new line and split on tab
	chomp();
	my @data = split(/\t/, $_);

	# look up the contig_id by conting name
	my $cid;
	if (exists $cmap{$data[0]}) {
		$cid = $cmap{$data[0]};
	} else {
		warn "Cannot map $data[0]\n";
		next;
	}

	# get the start, end and strand information
	my $start = $data[3];
	my $end   = $data[4];
	my $str   = $data[6];

	# get nucleotide and protein sequences as objects
	my $nseq = $nuc->next_seq;
	my $pseq = $pro->next_seq;
	
	# extract more information from the sequence object
	my $name = $nseq->display_id;
	my $desc = $nseq->description;
	my $nlen = $nseq->length;
	my $plen = $pseq->length;

	# get nucleotide and protein sequences as strings
	my $seqn = $nseq->seq;
	my $seqp = $pseq->seq;

	# insert into the database
	my $sql = "insert into gene_prediction(contig_id, contig_start, contig_end, contig_strand, gene_name, gene_description, gene_length, protein_length, dna_sequence, protein_sequence)
				        values($cid,$start,$end,'$str','$name','$desc',$nlen,$plen,'$seqn','$seqp')";

	$dbh->do($sql) || die "Could not execute '$query': $DBI::errstr\n";
	
	$gcount++;
}
close GFF;

# disconnect and print out user message
$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
print "Inserted $gcount gene predictions\n";
 
