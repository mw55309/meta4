#!/usr/bin/perl

use CGI;
use DBI;
use Bio::Graphics;
use Bio::SeqIO;
use Bio::SeqFeature::Generic;

# get the database connection details
require META4DB;

# create CGI object
my $query = new CGI;

# get the assembly_id (aid) and gene name (gid)
my $aid = $query->param("aid");
my $gid = $query->param("gid");

# connect to the database, build SQL
# and execute
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";
my $sql = "select gp.gene_name, gp.protein_length, d.domain_accession, d.domain_name, dm.aln_start, dm.aln_end, ddb.domain_db_id, ddb.domain_db_name, ddb.domain_db_version
	   from gene_prediction gp, domain_match dm, domain d, domain_db ddb, contig c
	   where gp.contig_id = c.contig_id and gp.gene_prediction_id = dm.gene_prediction_id and dm.domain_id = d.domain_id and d.domain_db_id = ddb.domain_db_id
	     and c.assembly_id = $aid and gp.gene_name = '$gid' order by dm.e_value";


$sth = $dbh->prepare($sql);
$sth->execute;

# hash ref to hold the information
my $info;

# gene name
my $gname;

# protein length
my $plength;

# iterate over the results
while(my @data = $sth->fetchrow_array) {

	# get the domain db name and version
	$info->{$data[6]}->{dbinfo}->{name} = $data[7];
	$info->{$data[6]}->{dbinfo}->{version} = $data[8];

	# set the gene name and protein length
	$gname   = $data[0];
	$plength = $data[1];

	# push domain information anonymous hash
	# into an array
	push(@{$info->{$data[6]}->{domains}}, {'accn' => $data[2], 'name' => $data[3], 'start' => $data[4], 'end' => $data[5]});
}

# disconnect from DB
$sth->finish;
$dbh->disconnect;

# use Bio::Graphics to build an image

# create the gene feature and add to a panel
my $wholeseq = Bio::SeqFeature::Generic->new(
                                             -start        => 1,
                                             -end          => $plength,
                                             -display_name => $gname
                                            );

my $panel = Bio::Graphics::Panel->new(
                                      -length    => $plength,
                                      -key_style => 'between',
                                      -width     => 800,
                                      -pad_left  => 10,
                                      -pad_right => 10,
                                     );

# add a track to show the whole sequence
$panel->add_track($wholeseq,
                  -glyph   => 'generic',
                  -bgcolor => 'blue',
                  -label   => 1,
                 );

# add a track to show a scale/arrow
$panel->add_track($wholeseq,
                  -glyph  => 'arrow',
                  -bump   => 0,
                  -double => 1,
                  -tick   => 2);
 

# array to hold feature objects
my @feat;

# iterate over the $info anonymous hash
# build Bio::SeqFeature objects and
# add those to the image
while( my($db,$hr) = each %{$info}) {

	# array of domain anon hashes
	my @dhr = @{$hr->{domains}};
	
	# create a Bio::SeqFeature from each one
	foreach $d (@dhr) {
		push(@feat, Bio::SeqFeature::Generic->new(-start=>$d->{start},-end=>$d->{end},-display_name=>$d->{accn}.":".$d->{name}));
	}

	# add as a track
	$panel->add_track(\@feat,
                    -glyph       =>  'generic',
                    -bgcolor     =>  'chartreuse',
                    -fgcolor     => 'black',
                    -font2color  => 'red',
                    -key         => $hr->{dbinfo}->{name} . ":" . $hr->{dbinfo}->{version},
		    -label       => \&gene_label,
                    -bump        => +2,
                    -height      => 8,
                   );
}

# print out the image directly
# as a content-type image/png
print "Content-type: image/png\n\n";
binmode STDOUT; 
print $panel->png;

# exit
exit 0;

# subroutine to extract the gene label from the
# object
sub gene_label {
	my $feat = shift;
	my $did  = $feat->display_name;
	#warn "Got $did\n";
	return $did;

}

