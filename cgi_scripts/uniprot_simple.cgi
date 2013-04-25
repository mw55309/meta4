#!/usr/bin/perl

# very simple script that queries the Meta4 database
# extracts domains for a particular gene prediction and
# then queries the UniProt web-service to find proteins
# that have the same domains

use LWP::Simple;
use CGI;
use DBI;
use HTML::Table;

# load Meta4 DB connection settings
require META4DB;

# create CGI object, print out header
my $q = new CGI;
print $q->header, "\n";

# and print out start html
print $q->start_html(-title => "Meta4",
                     -style=>{'code'=>$META4DB::css});

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# get the assembly_id (aid) and gene name (gid)
my $aid = $q->param("aid");
my $gid = $q->param("gid");

# connect to the database, build and execute the query
#
# NOTE: to prevent false positive domain assignments
# NOTE: we have included an e_value cut-off of 1e-05
# NOTE: you may wish to change this
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";
my $sql = "select d.domain_accession
           from gene_prediction gp, domain_match dm, domain d, contig c
           where gp.contig_id = c.contig_id and gp.gene_prediction_id = dm.gene_prediction_id and dm.domain_id = d.domain_id 
             and c.assembly_id = $aid and gp.gene_name = '$gid' and dm.e_value <= 1e-05";

$sth = $dbh->prepare($sql);
$sth->execute;

# build up a list of domains from the query
my @domains;
while(my ($acc) = $sth->fetchrow_array) {
       	$acc =~ s/\..+//g;	
	push(@domains, "content:$acc");
}

# if no domains are found, quit
if (@domains == 0) {
	print "<p>No domains meet the 1e-05 cut-off</p>\n";
	print $query->end_html;
	$sth->finish;
	$dbh->disconnect;
	exit(0);
}

# join the domains that have been found
# into a query that can be understood
# by the UniProt web service
my $cquery = join("+AND+", @domains);

# build the URL for the UniProt web-service
my $url = 'http://www.uniprot.org/uniprot/?query=' . $cquery . '&format=tab&columns=id,protein names,organism';

# now build the URL that will download to Excel
my $xurl = $url;
$xurl =~ s/format=tab/format=xls/;
  
# an HTML table to organise the header information
my $head = HTML::Table->new(-class=>'gene');

# show the query that was run and the link to Excel
$head->addRow(("Queried Uniprot for: $cquery", "Download this table to <a href='$xurl'>Excel</a>"));
$head->print;

# an HTML table for the results
my $tbl = HTML::Table->new(-class=>'gene');

# actually get the results, put into
# the @content array
my @content = split(/\n/, get($url));

# iterate over the array
# create links
# add row to table
foreach $row (@content) {
	my @data = split(/\t/, $row);
	$data[0] = "<a target='_blank' href='http://www.uniprot.org/uniprot/$data[0]'>$data[0]</a>" unless ($data[0] eq 'Entry');
	$tbl->addRow(@data);
}

# set the header, print the table
$tbl->setRowHead(1);
$tbl->print;

# finish and disconnect
$sth->finish;
$dbh->disconnect;

print $q->end_html;











