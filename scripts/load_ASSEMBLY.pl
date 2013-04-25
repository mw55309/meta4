#!/usr/bin/perl

use strict;
use DBI;
use Getopt::Long;
use File::Basename;
use lib dirname(__FILE__);

# load the database access credentials
# should be in the same folder as the script
require META4DB;

# print out usage message
unless (@ARGV) {
	print "USAGE: perl load_ASSEMBLY.pl --sample_id <sample id> --assembly_params <params file> --desc <assembly description>\n\n";
	print "Sample id is required and should be a unique sample_id from the sample table\n";
	print "Assembly parameters file is required\n";
	print "Assembly description is optional\n\n";
	print "EXAMPLE: perl load_ASSEMBLY.pl --sample_id 3 --assembly_params param_file.txt --desc 'SOAPdenovo assembly of sample 1'\n";
	exit;
}

# get options from the command line
my $sample_id = undef;
my $assembly_params = undef;
my $desc = undef;
GetOptions('sample_id=i' => \$sample_id, 'desc=s' => \$desc, 'assembly_params=s' => \$assembly_params);

# check for valid options
unless (defined $sample_id) {
	warn "Must provide a sample_id\n";
	exit;
}
unless (defined $assembly_params && -f $assembly_params) {
	warn "Must provide an assembly parameters file and must exist!\n";
	exit;
}

# connect to the database
my $dbh = DBI->connect('DBI:mysql:' . $META4DB::dbname, $META4DB::dbuser, $META4DB::dbpass) || die "Could not connect to database: $DBI::errstr";

# insert the assembly
my $query = "INSERT INTO assembly(sample_id, assembly_description) values('$sample_id','$desc')";
$dbh->do($query) || die "Could not execute '$query': $DBI::errstr\n";

# get and print the inserted ID
my $id = $dbh->last_insert_id(undef, undef, qw(assembly assembly_id)) or die "no insert id?";
print "Inserted assembly with id: $id\n";

# insert the information from the assembly params file
open(IN, $assembly_params);
while(<IN>) {
	s/\n|\r//g;
	my($name,$arg,$value) = split(/\t/);
	my $sql = "INSERT INTO assembly_param(assembly_id,param_name,param_argument,param_value) values($id,'$name','$arg','$value')";
	$dbh->do($sql) || die "Could not execute '$sql': $DBI::errstr\n";
}
close IN;

# disconnect
$dbh->disconnect
    or warn "Disconnection failed: $DBI::errstr\n";
 

