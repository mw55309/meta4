#!/usr/bin/perl

use CGI;
use DBI;
use HTML::Table;
use Bio::Seq;
use Bio::SeqIO;
use IO::String;

require META4DB;

my $q = new CGI;
print $q->header, "\n";

print $q->start_html(-title => "Meta4",
		     -style=>{'code'=>$META4DB::css});

my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

my $query = new CGI;
my $aid = $query->param("aid");
my $gid = $query->param("gid");

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


my $tbl = new HTML::Table(-class=>'gene');

$tbl->setCell(1,1,"Name");
$tbl->setCell(2,1,"Description");
$tbl->setCell(3,1,"Gene Length");
$tbl->setCell(4,1,"Protein Length");
$tbl->setCell(5,1,"Domain Table");
$tbl->setCell(6,1,"Domain Image");
$tbl->setCell(7,1,"DNA Sequence");
$tbl->setCell(8,1,"Prot Sequence");
$tbl->setCell(9,1,"Uniprot similarity (live)");
$tbl->setCell(10,1,"BLAST hits (live)");
$tbl->setCell(11,1,"InterProScan hits (live)");


$tbl->setCell(1,2,$data[0]);
$tbl->setCell(2,2,$data[1]);
$tbl->setCell(3,2,$data[2]);
$tbl->setCell(4,2,$data[3]);
$tbl->setCell(5,2,"<p id=\"loader1\">Domain table loading.  Please wait....</p>\n<iframe frameborder=\"0\" height=100px width=100\% src=\"/cgi-bin/domain_table.cgi?aid=$aid&gid=$gid\" onload=\"hideProgress('loader1')\"></iframe>");
$tbl->setCell(6,2,"<img src=\"/cgi-bin/show_domains.cgi?aid=$aid&gid=$gid\">");
$tbl->setCell(7,2,"<pre>$dna_formatted</pre>");
$tbl->setCell(8,2,"<pre>$prot_formatted</pre>");
$tbl->setCell(9,2,"<p id=\"loader4\">Uniprot results loading.  Please wait....</p>\n<iframe frameborder=\"0\" height=200px width=100\% src=\"/cgi-bin/uniprot_simple.cgi?aid=$aid&gid=$gid\" onload=\"hideProgress('loader4')\"></iframe>");
$tbl->setCell(10,2,"<p id=\"loader2\">Blast results loading.  Please wait....</p>\n<iframe frameborder=\"0\" height=100px width=100\% src=\"/cgi-bin/metablast.cgi?aid=$aid&gid=$gid\" onload=\"hideProgress('loader2')\"></iframe>");
$tbl->setCell(11,2,"<p id=\"loader3\">InterProScan results loading.  Please wait....</p>\n<iframe frameborder=\"0\" height=400px width=955px src=\"/cgi-bin/meta4ipr.cgi?aid=$aid&gid=$gid\" onload=\"hideProgress('loader3')\"></iframe>");

$tbl->setColHead(1);

$tbl->setColWidth(1,"100px");

print <<SCRIPT;
<script type="text/javascript">
function hideProgress(eid){
        document.getElementById(eid).style.display = 'none';
}
</script>
SCRIPT


$tbl->print;

$sth->finish;
$dbh->disconnect;
$query->end_html;



