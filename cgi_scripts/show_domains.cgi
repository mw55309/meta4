#!/usr/bin/perl

use CGI;
use DBI;

use Bio::Graphics;
use Bio::SeqIO;
use Bio::SeqFeature::Generic;

require META4DB;

# get information from the database;
my $query = new CGI;
my $aid = $query->param("aid");
my $gid = $query->param("gid");

my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";
my $sql = "select gp.gene_name, gp.protein_length, d.domain_accession, d.domain_name, dm.aln_start, dm.aln_end, ddb.domain_db_id, ddb.domain_db_name, ddb.domain_db_version
	   from gene_prediction gp, domain_match dm, domain d, domain_db ddb, contig c
	   where gp.contig_id = c.contig_id and gp.gene_prediction_id = dm.gene_prediction_id and dm.domain_id = d.domain_id and d.domain_db_id = ddb.domain_db_id
	     and c.assembly_id = $aid and gp.gene_name = '$gid' order by dm.e_value";


$sth = $dbh->prepare($sql);
$sth->execute;

my $info;
my $gname;
my $plength;
while(my @data = $sth->fetchrow_array) {
	$info->{$data[6]}->{dbinfo}->{name} = $data[7];
	$info->{$data[6]}->{dbinfo}->{version} = $data[8];
	$gname   = $data[0];
	$plength = $data[1];
	push(@{$info->{$data[6]}->{domains}}, {'accn' => $data[2], 'name' => $data[3], 'start' => $data[4], 'end' => $data[5]});
}
$sth->finish;
$dbh->disconnect;

#print "Adding $gname, $plength\n";

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

$panel->add_track($wholeseq,
                  -glyph   => 'generic',
                  -bgcolor => 'blue',
                  -label   => 1,
                 );

$panel->add_track($wholeseq,
                  -glyph  => 'arrow',
                  -bump   => 0,
                  -double => 1,
                  -tick   => 2);
 

my @feat;
while( my($db,$hr) = each %{$info}) {
	my @dhr = @{$hr->{domains}};
	
	foreach $d (@dhr) {
		push(@feat, Bio::SeqFeature::Generic->new(-start=>$d->{start},-end=>$d->{end},-display_name=>$d->{accn}.":".$d->{name}));
	}

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


print "Content-type: image/png\n\n";
binmode STDOUT; #just in case we're on NT
print $panel->png;
exit 0;

sub gene_label {
	my $feat = shift;
	my $did  = $feat->display_name;
	#warn "Got $did\n";
	return $did;

}

__DATA__
hsHOX3          381     2       200
scHOX3          210     2       210
xlHOX3          800     2       200
hsHOX2          1000    380     921
scHOX2          812     402     972
xlHOX2          1200    400     970
BUM             400     300     620
PRES1           127     310     700
