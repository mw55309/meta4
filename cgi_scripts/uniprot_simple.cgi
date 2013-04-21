#!/usr/bin/perl

use LWP::Simple;
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
my $sql = "select d.domain_accession
           from gene_prediction gp, domain_match dm, domain d, contig c
           where gp.contig_id = c.contig_id and gp.gene_prediction_id = dm.gene_prediction_id and dm.domain_id = d.domain_id 
             and c.assembly_id = $aid and gp.gene_name = '$gid' and dm.e_value <= 1e-05";

$sth = $dbh->prepare($sql);
$sth->execute;

my @domains;
while(my ($acc) = $sth->fetchrow_array) {
       	$acc =~ s/\..+//g;	
	push(@domains, "content:$acc");
}

if (@domains == 0) {
	print "<p>No domains meet the 1e-05 cut-off</p>\n";
	print $query->end_html;
	$sth->finish;
	$dbh->disconnect;
	exit(0);
}

my $cquery = join("+AND+", @domains);


#my $agent = LWP::UserAgent->new();

my $url = 'http://www.uniprot.org/uniprot/?query=' . $cquery . '&format=tab&columns=id,protein names,organism';
my $xurl = $url;
$xurl =~ s/format=tab/format=xls/;
  
#my $response = $agent->get( $url );

#print $response->content, "\n";

my $head = HTML::Table->new(-class=>'gene');
$head->addRow(("Queried Uniprot for: $cquery", "Download this table to <a href='$xurl'>Excel</a>"));
$head->print;


my $tbl = HTML::Table->new(-class=>'gene');
my @content = split(/\n/, get($url));
foreach $row (@content) {
	my @data = split(/\t/, $row);
	$data[0] = "<a target='_blank' href='http://www.uniprot.org/uniprot/$data[0]'>$data[0]</a>" unless ($data[0] eq 'Entry');
	$tbl->addRow(@data);
}
$tbl->setRowHead(1);
$tbl->print;

$sth->finish;
$dbh->disconnect;

print $query->end_html;











