#!/usr/bin/env perl

# Load libraries
use SOAP::Lite;
use MIME::Base64;
use DBI;
use CGI;
use HTML::Table;

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

print $q->start_html(-title => "Meta4ipr", -style=>{'code'=>$css});

# get information from the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

my $aid = $q->param("aid");
my $gid = $q->param("gid");

my $sql = "select gp.gene_name, gp.gene_description, gp.protein_sequence
           from gene_prediction gp, contig c
           where gp.contig_id = c.contig_id and c.assembly_id = $aid and gp.gene_name = '$gid'";

$sth = $dbh->prepare($sql);
$sth->execute;

my @data = $sth->fetchrow_array;

# WSDL URL for service
my $WSDL = 'http://www.ebi.ac.uk/Tools/services/soap/iprscan?wsdl';

# Default parameter values (should get these from the service)
my %tool_params = ();

my $serviceEndpoint  = "http://www.ebi.ac.uk/Tools/services/soap/iprscan";
my $serviceNamespace = "http://soap.jdispatcher.ebi.ac.uk";

# Create a service proxy from the WSDL. Specifying a SOAP fault handler which maps a fault to a die.
my $soap = SOAP::Lite->proxy($serviceEndpoint,	timeout => 6000)->uri($serviceNamespace);

# Load the sequence data and submit.
$tool_params{'sequence'} = ">$data[0] $data[1]\n$data[2]\n";

my $jobid = &soap_run( 'dummy@abc.com', "meta4", \%tool_params );

sleep 1;

my $jobStatus = 'PENDING';
while ( $jobStatus eq 'PENDING' || $jobStatus eq 'RUNNING' ) {
	sleep 5;    # Wait 5sec
	$jobStatus = soap_get_status($jobid);
}

my $txt = &soap_get_result( $jobid, "txt" );

if ($txt =~ m/\S+/) {
	my $png =  &soap_get_result( $jobid, "visual-png" );
	$png = encode_base64($png);

	print "<img src=\"data:image/png;base64,$png\">\n";
	print "<pre>$txt</pre>\n";
} else {
	print "<pre>No InterProScan hits</pre>\n";
}

$sth->finish;
$dbh->disconnect;
print $q->end_html;


sub soap_run {
	my $email  = shift;
	my $title  = shift;
	my $params = shift;


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

sub soap_get_status {

	my $jobid = shift;
	my $res = $soap->getStatus(
		SOAP::Data->name( 'jobId' => $jobid )->attr( { 'xmlns' => '' } ) );
	my $status_str = $res->valueof('//status');
	return $status_str;
}




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
