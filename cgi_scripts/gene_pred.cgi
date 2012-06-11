#!/usr/bin/perl

use CGI;
use DBI;
use HTML::Table;
use Bio::Seq;
use Bio::SeqIO;
use IO::String;

my $q = new CGI;
print $q->header, "\n";

my $css = "
table.result
{
font-family:\"Trebuchet MS\", Arial, Helvetica, sans-serif;
width:100%;
border-collapse:collapse;
table-layout: fixed;
}
table.form
{
font-family:\"Trebuchet MS\", Arial, Helvetica, sans-serif;
width:50%%;
border-collapse:collapse;
table-layout: fixed;
}
table.gene
{
font-family:\"Trebuchet MS\", Arial, Helvetica, sans-serif;
width:75%%;
border-collapse:collapse;
table-layout: fixed;
}
td, th 
{
font-size:8pt;
border:1px solid #98bf21;
padding:3px 7px 2px 7px;
word-wrap:break-word;
}
th 
{
font-size:8pt;
text-align:left;
padding-top:5px;
padding-bottom:4px;
background-color:#336699;
color:#ffffff;
}
";

print $q->start_html(-title => "Meta4",
		     -style=>{'code'=>$css});

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";

my $query = new CGI;
my $aid = $query->param("aid");
my $gid = $query->param("gid");
#my $aid = 1;
#my $gid = "CDS_1";
my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";
my $sql = "select gp.gene_name, gp.gene_description, gp.gene_length, gp.protein_length,  gp.dna_sequence, gp.protein_sequence 
	   from gene_prediction gp, contig c
	   where gp.contig_id = c.contig_id and c.assembly_id = $aid and gp.gene_name = '$gid'";

$sth = $dbh->prepare($sql);
$sth->execute;

my @data = $sth->fetchrow_array;

my $dna_obj = Bio::Seq->new(-seq        => $data[4],                        
                            -display_id => $data[0],                        
                            -desc       => $data[1]);
my $dna_formatted;
open($dna_io, ">", \$dna_formatted); 
my $sio = Bio::SeqIO->new(-fh=>$dna_io, -format=>'fasta');
$sio->write_seq($dna_obj);

my $prot_obj = Bio::Seq->new(-seq        => $data[5],                        
                            -display_id => $data[0],                        
                            -desc       => $data[1]);
my $prot_formatted;
open($prot_io, ">", \$prot_formatted); 
my $sio = Bio::SeqIO->new(-fh=>$prot_io, -format=>'fasta');
$sio->write_seq($prot_obj);


$tbl = new HTML::Table(-class=>'gene');

$tbl->setCell(1,1,"Name");
$tbl->setCell(2,1,"Description");
$tbl->setCell(3,1,"Gene Length");
$tbl->setCell(4,1,"Protein Length");
$tbl->setCell(5,1,"Domains");
$tbl->setCell(6,1,"DNA Sequence");
$tbl->setCell(7,1,"Prot Sequence");

$tbl->setCell(1,2,$data[0]);
$tbl->setCell(2,2,$data[1]);
$tbl->setCell(3,2,$data[2]);
$tbl->setCell(4,2,$data[3]);
$tbl->setCell(5,2,"<img src=\"/cgi-bin/show_domains.cgi?aid=$aid&gid=$gid\">");
$tbl->setCell(6,2,"<pre>$dna_formatted</pre>");
$tbl->setCell(7,2,"<pre>$prot_formatted</pre>");

$tbl->setColHead(1);

$tbl->print;

$sth->finish;
$dbh->disconnect;
$query->end_html;



