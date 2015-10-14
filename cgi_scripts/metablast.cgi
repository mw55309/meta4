#!/usr/bin/perl

##################################################################################################
#
# This script borrows heavily from the EBI script here:
#
# http://www.ebi.ac.uk/Tools/webservices/download_clients/perl/lwp/ncbiblast_lwp.pl
#
# we have taken out some uneccesary code, but plenty remains
# in and can be credited to EBI
#
##################################################################################################

use CGI;
use DBI;
use HTML::Table;
use Bio::Seq;
use Bio::SeqIO;
use IO::String;
use MIME::Base64;
use Bio::SearchIO;
use English;
use LWP;
use XML::Simple;
use File::Basename;
use Data::Dumper;

# get the database credentials
require META4DB;

# create CGI object and print header
my $q = new CGI;
print $q->header, "\n";
print $q->start_html(-title => "Meta4blast", -style=>{'code'=>$META4DB::css});

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# get the assembly_id (aid) and gene name (gid)
my $aid = $q->param("aid");
my $gid = $q->param("gid");

# prepare and execute the SQL
my $sql = "select gp.gene_name, gp.gene_description, gp.protein_sequence
           from gene_prediction gp, contig c
           where gp.contig_id = c.contig_id and c.assembly_id = $aid and gp.gene_name = '$gid'";
$sth = $dbh->prepare($sql);
$sth->execute;

# get entire result set as an array
my @data = $sth->fetchrow_array;

# Base URL for service
my $baseUrl = 'http://www.ebi.ac.uk/Tools/services/rest/ncbiblast';

# Set interval for checking status
my $checkInterval = 3;

# Set maximum number of 'ERROR' status calls to call job failed.
my $maxErrorStatusCount = 3;

# Output level
my $outputLevel = 1;

# Process command-line options
my $numOpts = scalar(@ARGV);
my %params = ( 
	'debugLevel' => 0, 
	'maxJobs'    => 1
);

# set up parameters for the REST service
my %tool_params = ();
$tool_params{'program'} = 'blastp';                            # protein blast
$tool_params{'stype'} = 'protein';                             # protein sequences
$tool_params{'sequence'} = ">$data[0] $data[1]\n$data[2]\n";   # the fasta formatted sequence
$tool_params{'email'} = 'you@server.com';                      # dummy e-mail: should change
$tool_params{'database'} = 'uniprotkb_trembl';                 # search uniprot trembl
$tool_params{'title'} = $data[0];                              # use gene name as the title

# set scriptname
my $scriptName = "metablast.cgi";

# LWP UserAgent for making HTTP calls (initialised when required).
my $ua;

# Seq ID
my $seq_id = $data[0];

# run rest
my $jobid = &rest_run( $tool_params{'email'}, $tool_params{'title'}, \%tool_params);

select( undef, undef, undef, 0.5 );     # 0.5 second sleep.

# Check status, and wait if not finished
&client_poll($jobid);

# get result object
my $result = rest_get_result( $jobid, "out");

# create dummy filehandle using the text-output
# from the service and IO::String
my $fh = IO::String->new($result);

# create a Search::IO BioPerl object
my $in = Bio::SearchIO->new(-fh => $fh, -format => 'blast');

# create a table to store the output
my $tbl = new HTML::Table(-class=>'gene');
$tbl->addRow(("Hit","Description","Query Length","Hit Length","E value"));

# iterate over the BLAST results
while( my $result = $in->next_result ) {
  while( my $hit = $result->next_hit ) {
	my $name = $hit->name;
	$name =~ s/\S+:(\S+)/<a target="_blank" href="http:\/\/www.uniprot.org\/uniprot\/$1">$1<\/a>/;
	$tbl->addRow($name, $hit->description, $result->query_length, $hit->length, $hit->significance);
  }
}
$tbl->setRowHead(1);
$tbl->print;

$sth->finish;
$dbh->disconnect;
$q->end_html;


sub client_poll {
	my $jobid  = shift;
	my $status = 'PENDING';

	# Check status and wait if not finished. Terminate if three attempts get "ERROR".
	my $errorCount = 0;
	while ($status eq 'RUNNING'
		|| $status eq 'PENDING'
		|| ( $status eq 'ERROR' && $errorCount < $maxErrorStatusCount ) )
	{
		$status = rest_get_status($jobid);
		#print STDERR "$status\n" if ( $outputLevel > 0 );
		if ( $status eq 'ERROR' ) {
			$errorCount++;
		}
		elsif ( $errorCount > 0 ) {
			$errorCount--;
		}
		if (   $status eq 'RUNNING'
			|| $status eq 'PENDING'
			|| $status eq 'ERROR' )
		{

			# Wait before polling again.
			sleep $checkInterval;
		}
	}
	return $status;
}


sub rest_run {
	
	my $email  = shift;
	my $title  = shift;
	my $params = shift;
	$email = '' if(!$email);
	
	# Get an LWP UserAgent.
	$ua = &rest_user_agent() unless defined($ua);

	# Clean up parameters
	my (%tmp_params) = %{$params};
	$tmp_params{'email'} = $email;
	$tmp_params{'title'} = $title;
	foreach my $param_name ( keys(%tmp_params) ) {
		if ( !defined( $tmp_params{$param_name} ) ) {
			delete $tmp_params{$param_name};
		}
	}

	# Submit the job as a POST
	my $url = $baseUrl . '/run';
	my $response = $ua->post( $url, \%tmp_params );
	
	# Check for an error.
	&rest_error($response);

	# The job id is returned
	my $job_id = $response->content();

	return $job_id;
}

sub rest_get_status {
	
	my $job_id = shift;
	
	my $status_str = 'UNKNOWN';
	my $url        = $baseUrl . '/status/' . $job_id;
	$status_str = &rest_request($url);
	
	return $status_str;
}

sub rest_user_agent() {

	# Create an LWP UserAgent for making HTTP calls.
	my $ua = LWP::UserAgent->new();
	# Set 'User-Agent' HTTP header to identifiy the client.
	my $revisionNumber = 0;	
	$revisionNumber = $1 if('$Revision: 2791 $' =~ m/(\d+)/);	
	$ua->agent("EBI-Sample-Client/$revisionNumber ($scriptName; $OSNAME) " . $ua->agent());
	# Configure HTTP proxy support from environment.
	$ua->env_proxy;
	return $ua;
}


sub rest_error() {

	my $response = shift;
	my $contentdata;
	if(scalar(@_) > 0) {
		$contentdata = shift;
	}
	if(!defined($contentdata) || $contentdata eq '') {
		$contentdata = $response->content();
	}
	# Check for HTTP error codes
	if ( $response->is_error ) {
		my $error_message = '';
		# HTML response.
		if(	$contentdata =~ m/<h1>([^<]+)<\/h1>/ ) {
			$error_message = $1;
		}
		#  XML response.
		elsif($contentdata =~ m/<description>([^<]+)<\/description>/) {
			$error_message = $1;
		}
		die 'http status: ' . $response->code . ' ' . $response->message . '  ' . $error_message;
	}
	
}


sub rest_request {
	
	my $requestUrl = shift;
	

	# Get an LWP UserAgent.
	$ua = &rest_user_agent() unless defined($ua);
	# Available HTTP compression methods.
	my $can_accept;
	eval {
	    $can_accept = HTTP::Message::decodable();
	};
	$can_accept = '' unless defined($can_accept);
	# Perform the request
	my $response = $ua->get($requestUrl,
		'Accept-Encoding' => $can_accept, # HTTP compression.
	);
	
	# Unpack possibly compressed response.
	my $retVal;
	if ( defined($can_accept) && $can_accept ne '') {
	    $retVal = $response->decoded_content();
	}
	# If unable to decode use orginal content.
	$retVal = $response->content() unless defined($retVal);
	# Check for an error.
	&rest_error($response, $retVal);

	# Return the response data
	return $retVal;
}


sub rest_get_result {
	
	my $job_id = shift;
	my $type   = shift;

	my $url    = $baseUrl . '/result/' . $job_id . '/' . $type;
	my $result = &rest_request($url);
	
	return $result;
}
