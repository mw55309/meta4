#!/usr/bin/perl

#use strict;
use DBI;
use Getopt::Long;
use Bio::SeqIO;

unless (@ARGV) {
	print "USAGE: perl load_SAMPLE.pl --name <sample name> --desc <sample description>\n\n";
	print "Sample name is required and should be unique\n";
	print "Sample description is optional\n\n";
	print "EXAMPLE: perl load_SAMPLE.pl --name 'A test sample' --desc 'A completely made up sample from my head'\n";
	exit;
}

my $assembly_id = undef;
my $nucfile     = undef;
my $profile     = undef;
my $gff         = undef;

GetOptions('assembly_id=s' => \$assembly_id, 'nucfile=s' => \$nucfile, 'profile=s' => \$profile, 'gff=s', \$gff);

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

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";

# map the contigs for this assembly
my %cmap;
my $sql = "select contig_id, contig_name from contig where assembly_id = $assembly_id";
my $sth = $dbh->prepare($sql);
$sth->execute;
while (my($id,$name) = $sth->fetchrow_array) {
	$cmap{$name} = $id;
	print "Mapping $name to $id\n"
}
$sth->finish;

my $nuc = Bio::SeqIO->new(-file => $nucfile);
my $pro = Bio::SeqIO->new(-file => $profile);

open(GFF, "$gff") || die "Cannot open $gff\n";
while(<GFF>) {
	next if (m/^#/);
	my @data = split(/\t/, $_);

	my $cid = $cmap{$data[0]};

	my $start = $data[3];
	my $end   = $data[4];

	my $nseq = $nuc->next_seq;
	my $pseq = $pro->next_seq;
	
	my $name = $nseq->display_id;
	my $desc = $nseq->description;
	my $nlen = $nseq->length;
	my $plen = $pseq->length;

	my $seqn = $nseq->seq;
	my $seqp = $pseq->seq;

	my $sql = "insert into gene_prediction(contig_id,gene_name, gene_description, gene_length, protein_length, dna_sequence, protein_sequence)
				        values($cid,'$name','$desc',$nlen,$plen,'$seqn','$seqp')";

	$dbh->do($sql) || die "Could not execute '$query': $DBI::errstr\n";
	
	
}
close GFF;

$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 
