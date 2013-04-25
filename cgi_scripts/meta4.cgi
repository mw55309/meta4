#!/usr/bin/perl

# this is the point of entry to query the Meta4
# database.  It creates a web form to query the database
# and returns a table of results

use CGI;
use DBI;
use HTML::Table;

# load the database credentials
# should be in the same folder
require META4DB;

# create new CGI object, print out HTML header
my $q = new CGI;
print $q->header, "\n";

# javascript to execute when HTML loads
my $bodyform = 'changeList(document.forms[' . "'meta4'" . '].sample_id)';

# print out the start of the HTML
print $q->start_html(-title => "Meta4",
		     -style=>{'code'=>$META4DB::css},
		     -onload=>"$bodyform");

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# unless there are parameters on the URL
# then print the form, end the HTML and exit
unless ($q->param("sample_id")) {
	&show_form;
	print $q->end_html;
	exit;
}

# if we get to here, then we have parameters

# build the SQL clauses from the parameters
my @caveats;
if ($q->param("sample_id")) {
	push(@caveats, "s.sample_id=".$q->param("sample_id"));
}

my $aid;
if ($q->param("assembly_id")) {
	$aid = $q->param("assembly_id");
	push(@caveats, "a.assembly_id=".$q->param("assembly_id"));
}

if ($q->param("min_length")) {
	push(@caveats, "g.gene_length>=".$q->param("min_length"));
}

if ($q->param("max_length")) {
	push(@caveats, "g.gene_length<=".$q->param("max_length"));
}

if ($q->param("accn")) {
	my $accn = $q->param("accn");
	$accn =~ tr/[A-Z]/[a-z]/;
	push(@caveats, "lower(d.domain_accession) like '\%$accn\%'");
}

if ($q->param("name")) {
	my $name = $q->param("name");
	$name =~ tr/[A-Z]/[a-z]/;
	push(@caveats, "lower(d.domain_name) like '\%$name\%'");
}

if ($q->param("desc")) {
	my $desc = $q->param("desc");
	$desc =~ tr/[A-Z]/[a-z]/;
	push(@caveats, "lower(d.domain_description) like '\%$desc\%'");
}

# by default set the mr (maximum results) to zero
# i.e. get all results.  Only change this if the max_results parameter
# has changed
my $mr = 0;
if ($q->param("max_results")) {
	$mr = $q->param("max_results");
}

# create a table for the output
my $tbl = new HTML::Table(-align=>'center', -class=>'result');

# build the SQL statement
my $sql = "select  s.sample_name,"
        ."g.gene_name,"
        ."g.gene_length,"
        ."g.protein_length,"
        ."d.domain_accession,"
        ."d.domain_name,"
        ."d.domain_description,"
        ."dm.aln_start,"
        ."dm.aln_end,"
        ."dm.domain_start,"
        ."dm.domain_end,"
        ."d.domain_length,"
        ."dm.e_value,"
        ."dm.bit_score
from    sample s,
        assembly a,
        contig c,
        gene_prediction g,
        domain d,
        domain_match dm
where   s.sample_id = a.sample_id
  and   a.assembly_id = c.assembly_id
  and   c.contig_id = g.contig_id
  and   g.gene_prediction_id = dm.gene_prediction_id
  and   dm.domain_id = d.domain_id";

# add the clauses
$sql .= " and " . join(" and ", @caveats);

# limit to maximum results if relevant
if ($mr) {
	$sql .= " limit $mr";
}

# prepare and execute the SQL 
$sth = $dbh->prepare($sql);
$sth->execute;

# keep a counter
my $rcount = 0;

# get the headers from the statement handle and use as table
# headers
$tbl->addRow(@{$sth->{NAME}});
$tbl->setRowHead(1);

# iterate over the result set
while(my(@array) = $sth->fetchrow_array) {

	# create the necessary link
	$array[1] = "<a href=\"/cgi-bin/gene_pred.cgi?aid=$aid&gid=$array[1]\" target=\"_blank\">$array[1]</a>";

	# add to the output and cout
	$tbl->addRow(@array);
	$rcount++;
}

# finish the statement and disconnect
$sth->finish;
$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";

# set alignemnt of the table
$tbl->setAlign('center');

# warn about there being less results
# of the user specified max_results
if ($mr) {
	if ($rcount == $mr) {
		print "<p>Results limited to first $mr; there may be more</p>";
	}
}

#print the table and the end of the HTML
$tbl->print;
print $q->end_html();



# subroutines


# print out the basic query form
sub show_form {


	# print javascript that links the sample
	# and assembly drop down lists
	&print_js;

	# print out the title
	print "<h1>Query Meta4 database</h1>\n";

	# print out the help
	while(<DATA>) {print;}

	# start the form
	print "<form name =\"meta4\" action=\"meta4.cgi\" method=\"post\">\n";

	# start an HTML table to organise the form
	my $f = new HTML::Table(-class => 'form');

	# the SQL statement used to populate the drop downs
	my $sql = "select s.sample_id, s.sample_name, a.assembly_id, a.assembly_description
			from sample s, assembly a
			where s.sample_id = a.sample_id order by s.sample_id";
	my $sth = $dbh->prepare($sql);
	$sth->execute;

	# iterate over the query and set
	# the data for the drop downs
	my $ass;
	while(my @data = $sth->fetchrow_array) {
		$ass->{$data[0]}->{name} = $data[1];
		$ass->{$data[0]}->{a}->{$data[2]}=$data[3];
	}
	$sth->finish;

	# set the titles of the table
	$f->setCell(1,1,"Sample");
	$f->setCell(1,2,"Assembly");
	$f->setCell(1,3,"Accession");
	$f->setCell(1,4,"Name");
	$f->setCell(1,5,"Description");
	$f->setCell(1,6,"Min Length");
	$f->setCell(1,7,"Max Length");
	$f->setCell(1,8,"Max Results");
	$f->setRowHead(1);

	# add the event to update the drop downs
	my $sam_html = "<select name =\"sample_id\" size=1 onchange=\"changeList(this)\">\n";
	foreach $key (sort {$a<=>$b} keys %{$ass}) {
		$sam_html.="<option value=\"$key\">" . $key . ":" . $ass->{$key}->{name};
	}
	$sam_html.= "</select>\n";

	# create the HTML form elements
	my $ass_html = "<select name =\"assembly_id\" size=1>\n</select>\n";
	my $acc_html = "<input type=text size=5 value='' name=accn>\n";
	my $nam_html = "<input type=text size=5 value='' name=name>\n";
	my $des_html = "<input type=text size=5 value='' name=desc>\n";
	my $min_html = "<input type=text size=5 value=0 name=min_length>\n";
	my $max_html = "<input type=text size=5 value=0 name=max_length>\n";
	my $max_results = "<input type=text size=5 value=100 name=max_results>\n";

	# add to the table
	$f->setCell(2,1,$sam_html);
	$f->setCell(2,2,$ass_html);
	$f->setCell(2,3,$acc_html);
	$f->setCell(2,4,$nam_html);
	$f->setCell(2,5,$des_html);
	$f->setCell(2,6,$min_html);
	$f->setCell(2,7,$max_html);
	$f->setCell(2,8,$max_results);

	# print the table/form
	$f->print;

	# print the submit button
	print "<input type=\"submit\" value=\"Submit\" />\n";
	print "</form>\n";

	# create the javascript that links the drop down
	# lists together
	print "<script language=\"javascript\">\n";
	print "var lists = new Array();\n";

	foreach $key (sort {$a<=>$b} keys %{$ass}) {
		my @display_text;
		my @values;
		print "lists['" .$key."'] = new Array();\n";
		foreach $a (sort {$a<=>$b} keys %{$ass->{$key}->{a}}) {
			push(@values, "'$a'");
			push(@display_text, "'$a:".$ass->{$key}->{a}->{$a}."'");
		}
		print "lists['" .$key."'][0] = new Array(" . join(",",@display_text) . ");\n";
		print "lists['" .$key."'][1] = new Array(" . join(",",@values) . ");\n";
	}
	print "</script>\n";
}

# this function prints out the Javascript that
# links the two drop down lists together
sub print_js {
	print <<ENDOFJS;

<script language="javascript">

// This function goes through the options for the given
// drop down box and removes them in preparation for
// a new set of values

function emptyList( box ) {
	// Set each option to null thus removing it
	while ( box.options.length ) box.options[0] = null;
}

// This function assigns new drop down options to the given
// drop down box from the list of lists specified

function fillList( box, arr ) {
	// arr[0] holds the display text
	// arr[1] are the values

	for ( i = 0; i < arr[0].length; i++ ) {

		// Create a new drop down option with the
		// display text and value from arr

		option = new Option( arr[0][i], arr[1][i] );

		// Add to the end of the existing options

		box.options[box.length] = option;
	}

	// Preselect option 0

	box.selectedIndex=0;
}

// This function performs a drop down list option change by first
// emptying the existing option list and then assigning a new set

function changeList( box ) {
	// Isolate the appropriate list by using the value
	// of the currently selected option

	list = lists[box.options[box.selectedIndex].value];

	// Next empty the assembly_id list

	emptyList( box.form.assembly_id );

	// Then assign the new list values

	fillList( box.form.assembly_id, list );
}
</script>
ENDOFJS
}


# below is the customisable help that is displayed at the top
# of the web-form.  Feel free to edit!
__DATA__
<table class="form">
<tr>
<td>
<p>Meta4 allows users to query metagenomic datasets using a simple web interface.&nbsp; Here we present an assembly and annotation of the data from:</p><ol><li>
<pre>
Hess M et al (2011) Metagenomic discovery of biomass-degrading genes and genomes from cow rumen. <em>Science </em><strong>331(6016)</strong>:463-7</pre>
</li></ol><p>Users can query predicted genes/proteins based on their Pfam domains (Accession; Name; Description) and minimum and maximum length gene length (Min Length; Max Length).&nbsp; By default, the first 100 records will be returned.&nbsp; Please alter &quot;Max Results&quot; to change this (set it to 0 to return everything).</p><p>As an example, enter <em>Glyco_hydro</em> into the Name field and click <strong>Submit</strong></p>
</td>
</tr>
</table>
<br/>
