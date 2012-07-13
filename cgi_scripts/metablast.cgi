#!/usr/bin/perl

use CGI;
use DBI;
use HTML::Table;
use Bio::Seq;
use Bio::SeqIO;
use IO::String;
use SOAP::Lite;
use CGI;
use MIME::Base64;
use Bio::SearchIO;

require META4DB;

my $css = "
table.result
{
font-family:\"Trebuchet MS\", Arial, Helvetica, sans-serif;
border-collapse:collapse;
<!-- table-layout: fixed; -->
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
}";

my $q = new CGI;
print $q->header, "\n";

print $q->start_html(-title => "Meta4blast", -style=>{'code'=>$css});

my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

my $query = new CGI;
my $aid = $query->param("aid");
my $gid = $query->param("gid");
my $check = $query->param("check");

my $sql = "select gp.gene_name, gp.gene_description, gp.protein_sequence
           from gene_prediction gp, contig c
           where gp.contig_id = c.contig_id and c.assembly_id = $aid and gp.gene_name = '$gid'";

$sth = $dbh->prepare($sql);
$sth->execute;

my @data = $sth->fetchrow_array;

# WSDL URL for service
my $WSDL = 'http://www.ebi.ac.uk/Tools/services/soap/wublast?wsdl';

# Set interval for checking status
my $checkInterval = 3;

# For a document/literal service which has types with repeating elements
# namespace and endpoint need to be used instead of the WSDL.
my $serviceEndpoint = "http://www.ebi.ac.uk/Tools/services/soap/wublast";
my $serviceNamespace = "http://soap.jdispatcher.ebi.ac.uk";

# Create a service proxy from the WSDL. Specifying a SOAP fault handler which maps a fault to a die.
my $soap = SOAP::Lite->proxy($serviceEndpoint,	timeout => 6000)->uri($serviceNamespace);

# Default parameter values (should get these from the service)
my %tool_params = ();
my %params = ();
$tool_params{'program'} = 'blastp';
$tool_params{'stype'} = 'protein';
$tool_params{'sequence'} = ">$data[0] $data[1]\n$data[2]\n";
$params{'email'} = 'test@server.com';
$params{'database'} = 'uniprotkb_swissprot';
$params{'title'} = '$data[0]';


# load the databases
my (@dbList) = split /[ ,]/, $params{'database'};
	for ( my $i = 0 ; $i < scalar(@dbList) ; $i++ ) {
		$tool_params{'database'}[$i] =
		  SOAP::Data->type( 'string' => $dbList[$i] )->name('string');
	}

my $jobid = &soap_run( $params{'email'}, $params{'title'}, \%tool_params );

sleep 1;

my $jobStatus = 'PENDING';
while ( $jobStatus eq 'PENDING' || $jobStatus eq 'RUNNING' ) {
	sleep 5;    # Wait 5sec
	$jobStatus = soap_get_status($jobid);
	print STDERR 'Job status: ', $jobStatus, "\n";
}

my $result = soap_get_result( $jobid, "out");

my $fh = IO::String->new($result);
my $in = Bio::SearchIO->new(-fh => $fh, -format => 'blast');

my $tbl = new HTML::Table(-align=>'center', -class=>'result');

while( my $result = $in->next_result ) {
  while( my $hit = $result->next_hit ) {
	my $name = $hit->name;
	$name =~ s/\S+:(\S+)/<a target="_blank" href="http:\/\/www.uniprot.org\/uniprot\/$1">$1<\/a>/;
	$tbl->addRow($name, $hit->description, $hit->significance);
  }
}

$tbl->print;

$sth->finish;
$dbh->disconnect;
$query->end_html;


sub soap_get_result {
	my $jobid = shift;
	my $type  = shift;
	my $res = $soap->getResult(
		SOAP::Data->name( 'jobId' => $jobid )->attr( { 'xmlns' => '' } ),
		SOAP::Data->name( 'type'  => $type )->attr(  { 'xmlns' => '' } )
	);
	my $result = decode_base64( $res->valueof('//output') );
	return $result;
}

sub soap_get_status {
	my $jobid = shift;
	my $res = $soap->getStatus(
		SOAP::Data->name( 'jobId' => $jobid )->attr( { 'xmlns' => '' } ) );
	my $status_str = $res->valueof('//status');
	return $status_str;
}


sub soap_run {
	my $email  = shift;
	my $title  = shift;
	my $params = shift;
	if ( defined($title) ) {
	}

	my (@paramsList) = ();
	foreach my $key ( keys(%$params) ) {
		if ( defined( $params->{$key} ) && $params->{$key} ne '' ) {
			push @paramsList,
			  SOAP::Data->name( $key => $params->{$key} )
			  ->attr( { 'xmlns' => '' } );
		}
	}

	my $ret = $soap->run(
		SOAP::Data->name( 'email' => $email )->attr( { 'xmlns' => '' } ),
		SOAP::Data->name( 'title' => $title )->attr( { 'xmlns' => '' } ),	
		SOAP::Data->name( 'parameters' => \SOAP::Data->value(@paramsList) )
		  ->attr( { 'xmlns' => '' } )
	);
	return $ret->valueof('//jobId');
}










