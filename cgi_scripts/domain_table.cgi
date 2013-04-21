#!/usr/bin/perl

use CGI;
use DBI;
use HTML::Table;

require META4DB;

my $q = new CGI;
print $q->header, "\n";

print $q->start_html(-title => "Meta4",
		     -style=>{'code'=>$META4DB::css});

my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

my $query = new CGI;
my $aid = $query->param("aid");
my $gid = $query->param("gid");

my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";
my $sql = "select gp.gene_name, gp.protein_length, d.domain_accession, d.domain_name, dm.aln_start, dm.aln_end, dm.e_value, d.domain_length, ddb.domain_db_name, ddb.domain_db_version
           from gene_prediction gp, domain_match dm, domain d, domain_db ddb, contig c
           where gp.contig_id = c.contig_id and gp.gene_prediction_id = dm.gene_prediction_id and dm.domain_id = d.domain_id and d.domain_db_id = ddb.domain_db_id
             and c.assembly_id = $aid and gp.gene_name = '$gid' order by dm.e_value";


$sth = $dbh->prepare($sql);
$sth->execute;

$tbl = new HTML::Table(-class=>'gene');
$tbl->addRow(("Name","Protein Length", "Accession","Domain","aln start", "aln end", "e value", "domain length", "DB Name", "DB Version"));
while(my @data = $sth->fetchrow_array) {
       $tbl->addRow(@data);
}
$tbl->setRowHead(1);
$tbl->print;
$sth->finish;
$dbh->disconnect;

print $q->end_html;
