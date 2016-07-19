#!/usr/bin/perl

##################################################################################################
#
# This script borrows heavily from the EBI script here:
# 
# http://www.ebi.ac.uk/Tools/webservices/download_clients/perl/soaplite/iprscan_soaplite.pl
#
# we have taken out some uneccesary code, but plenty remains
# and can be credited to EBI
#
##################################################################################################

# this script extracts sequence from the Meta4 database and 
# runs InterProScan on it using the EBI web service
#
# http://www.ebi.ac.uk/Tools/webservices/services/pfa/iprscan_soap

# load libraries
use SOAP::Lite;
use MIME::Base64;
use DBI;
use CGI;
use HTML::Table;

# get the database connection credentials
require META4DB;

# create a CGI object, print out header
my $q = new CGI;
print $q->header, "\n";
print $q->start_html(-title => "Meta4ipr", -style=>{'code'=>$META4DB::css});

# connect to the Meta4 database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# get the assembly_id (aid) and gene name (gid)
my $aid = $q->param("aid");
my $gid = $q->param("gid");

# build and execute the query
my $sql = "select gp.gene_name, gp.gene_description, gp.protein_sequence
           from gene_prediction gp, contig c
           where gp.contig_id = c.contig_id and c.assembly_id = $aid and gp.gene_name = '$gid'";
$sth = $dbh->prepare($sql);
$sth->execute;

# get the whole result set as an array
my @data = $sth->fetchrow_array;

# get rid of trailing stars
$data[2] =~ s/\*$//;

# WSDL URL for service
my $WSDL = 'http://www.ebi.ac.uk/Tools/services/soap/iprscan5?wsdl';

# Default parameter values 
my %tool_params = ();

# set the end-point and name space
my $serviceEndpoint  = "http://www.ebi.ac.uk/Tools/services/soap/iprscan5";
my $serviceNamespace = "http://soap.jdispatcher.ebi.ac.uk";

# Create a service proxy from the WSDL. 
my $soap = SOAP::Lite->proxy($serviceEndpoint,	timeout => 6000)->uri($serviceNamespace);

# Load the sequence data and submit.
$tool_params{'sequence'} = ">$data[0] $data[1]\n$data[2]\n";

# using dummy e-mail - this should change
my $jobid = &soap_run( 'dummy@abc.com', "meta4", \%tool_params );

# wait
sleep 1;

# poll the service to see if the job has finished
my $jobStatus = 'PENDING';
while ( $jobStatus eq 'PENDING' || $jobStatus eq 'RUNNING' ) {
	sleep 5;    # Wait 5sec
	$jobStatus = soap_get_status($jobid);
}

# get the text-result
my $txt = &soap_get_result( $jobid, "tsv" );

# if there actually is some text (i.e. if there is a result
if ($txt =~ m/\S+/) {

	# get the PNG image
	my $svg =  &soap_get_result( $jobid, "svg" );
	#$png = encode_base64($png);

	# print it out directly to the browser
	#print "<img src=\"data:image/png;base64,$png\">\n";
	print "$svg\n";
	print "<pre>$txt</pre>\n";
} else {
	print "<pre>No InterProScan hits</pre>\n";
}

# finish and disconnect etc
$sth->finish;
$dbh->disconnect;
print $q->end_html;

# subroutine the run the service
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

# subroutine to return the job status
sub soap_get_status {

	my $jobid = shift;
	my $res = $soap->getStatus(
		SOAP::Data->name( 'jobId' => $jobid )->attr( { 'xmlns' => '' } ) );
	my $status_str = $res->valueof('//status');
	return $status_str;
}

# subroutine to return the service result
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
