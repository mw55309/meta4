#!/usr/bin/perl

use CGI;
use DBI;
use HTML::Table;

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

my $bodyform = 'changeList(document.forms[' . "'meta4'" . '].sample_id)';
print $q->start_html(-title => "Meta4",
		     -style=>{'code'=>$css},
		     -onload=>"$bodyform");

my $dbh = DBI->connect('DBI:mysql:meta4','root','mysqlroot') || die "Could not connect to database: $DBI::errstr";

unless ($q->param("sample_id")) {
	&show_form;
	print $q->end_html;
	exit;
}

# build the caveats
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

my $tbl = new HTML::Table(-align=>'center', -class=>'result');

my $sql = "select  s.sample_name,"
#        ."s.sample_description,"
#        ."a.assembly_description,"
#        ."c.contig_name,"
#        ."c.contig_desc,"
#        ."c.contig_length,"
#        ."c.contig_coverage,"
        ."g.gene_name,"
#        ."g.gene_description,"
        ."g.gene_length,"
        ."g.protein_length,"
#	."g.dna_sequence,"
#	."g.protein_sequence,"
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

$sql .= " and " . join(" and ", @caveats);

$sth = $dbh->prepare($sql);
$sth->execute;

$tbl->addRow(@{$sth->{NAME}});
$tbl->setRowHead(1);
while(my(@array) = $sth->fetchrow_array) {
	$array[1] = "<a href=\"/cgi-bin/gene_pred.cgi?aid=$aid&gid=$array[1]\">$array[1]</a>";
	$tbl->addRow(@array);
}
$sth->finish;
$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";

$tbl->setAlign('center');

$tbl->print;
print $q->end_html();


sub show_form {

	&print_js;

	print "<form name =\"meta4\" action=\"meta4.cgi\" method=\"post\">\n";

	my $f = new HTML::Table(-class => 'form');

	my $sql = "select s.sample_id, s.sample_name, a.assembly_id, a.assembly_description
			from sample s, assembly a
			where s.sample_id = a.sample_id order by s.sample_id";

	my $sth = $dbh->prepare($sql);
	$sth->execute;

	my $ass;
	while(my @data = $sth->fetchrow_array) {
		$ass->{$data[0]}->{name} = $data[1];
		$ass->{$data[0]}->{a}->{$data[2]}=$data[3];
	}
	$sth->finish;

	$f->setCell(1,1,"Sample");
	$f->setCell(1,2,"Assembly");
	$f->setCell(1,3,"Accession");
	$f->setCell(1,4,"Name");
	$f->setCell(1,5,"Description");
	$f->setCell(1,6,"Min Length");
	$f->setCell(1,7,"Max Length");

	$f->setRowHead(1);

	my $sam_html = "<select name =\"sample_id\" size=1 onchange=\"changeList(this)\">\n";
	foreach $key (sort {$a<=>$b} keys %{$ass}) {
		$sam_html.="<option value=\"$key\">" . $key . ":" . $ass->{$key}->{name};
	}
	$sam_html.= "</select>\n";
	my $ass_html = "<select name =\"assembly_id\" size=1>\n</select>\n";
	my $acc_html = "<input type=text size=5 value='' name=accn>\n";
	my $nam_html = "<input type=text size=5 value='' name=name>\n";
	my $des_html = "<input type=text size=5 value='' name=desc>\n";
	my $min_html = "<input type=text size=5 value=0 name=min_length>\n";
	my $max_html = "<input type=text size=5 value=0 name=max_length>\n";

	$f->setCell(2,1,$sam_html);
	$f->setCell(2,2,$ass_html);
	$f->setCell(2,3,$acc_html);
	$f->setCell(2,4,$nam_html);
	$f->setCell(2,5,$des_html);
	$f->setCell(2,6,$min_html);
	$f->setCell(2,7,$max_html);

	$f->print;

	print "<input type=\"submit\" value=\"Submit\" />\n";
	print "</form>\n";

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