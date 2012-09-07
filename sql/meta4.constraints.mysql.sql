CREATE TABLE sample (
	sample_id int(5) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	sample_name varchar(255) NOT NULL UNIQUE KEY,
	sample_description TEXT) ENGINE=INNODB;;

CREATE TABLE assembly (
	assembly_id int(6) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	sample_id int(5) UNSIGNED NOT NULL,
	assembly_description TEXT,
	FOREIGN KEY (sample_id) REFERENCES sample(sample_id)) ENGINE=INNODB;;

CREATE TABLE assembly_param (
	assembly_param_id int(7) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	assembly_id int(6) UNSIGNED NOT NULL,
	param_name varchar(255) NOT NULL,
	param_argument varchar(20) NOT NULL,
	param_value varchar(20),
	FOREIGN KEY (assembly_id) REFERENCES assembly(assembly_id)) ENGINE=INNODB;;

CREATE TABLE contig (
	contig_id int(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	assembly_id int(6) UNSIGNED NOT NULL,
	contig_name varchar(255) NOT NULL,
	contig_desc TEXT,
	contig_length int(9) UNSIGNED,
	contig_coverage decimal(8,2),
	INDEX contig_name_idx (contig_name),
	FOREIGN KEY (assembly_id) REFERENCES assembly(assembly_id)) ENGINE=INNODB;;

CREATE TABLE gene_prediction (
	gene_prediction_id int(10) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	contig_id int(9) UNSIGNED NOT NULL,
	contig_start int(9) UNSIGNED NOT NULL,
	contig_end int(9) UNSIGNED NOT NULL,
	contig_strand varchar(1) NOT NULL,
	gene_name varchar(255) NOT NULL,
	gene_description TEXT,
	gene_length int(5) UNSIGNED NOT NULL,
	protein_length int(5) UNSIGNED NOT NULL,
	dna_sequence TEXT,
	protein_sequence TEXT,
	INDEX gene_name_idx (gene_name),
	KEY contig_id (contig_id),
	FOREIGN KEY (contig_id) REFERENCES contig(contig_id)) ENGINE=INNODB;

CREATE TABLE domain_db (
	domain_db_id int(4) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	domain_db_name varchar(255) NOT NULL,
	domain_db_version varchar(10) NOT NULL,
	domain_db_file varchar(255),
	domain_db_description varchar(255)) ENGINE=INNODB;;

CREATE TABLE domain (
	domain_id int(10) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	domain_db_id int(4) UNSIGNED NOT NULL,
	domain_accession varchar(255) NOT NULL,
	domain_name varchar(255),
	domain_description TEXT,
	domain_length int(5) UNSIGNED NOT NULL,
	FOREIGN KEY (domain_db_id) REFERENCES domain_db(domain_db_id)) ENGINE=INNODB;;

CREATE TABLE domain_match (
	domain_match_id int(9) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
	domain_id int(10) UNSIGNED NOT NULL,
	gene_prediction_id int(10) UNSIGNED NOT NULL,
	aln_start int(5) UNSIGNED NOT NULL,
	aln_end int(5) UNSIGNED NOT NULL,
	domain_start int(5) UNSIGNED NOT NULL,
	domain_end int(5) UNSIGNED NOT NULL,
	e_value double NOT NULL,
	bit_score decimal(7,2) NOT NULL,
	INDEX domain_id_idx (domain_id),
	FOREIGN KEY (domain_id) REFERENCES domain(domain_id),
	FOREIGN KEY (gene_prediction_id) REFERENCES gene_prediction(gene_prediction_id)) ENGINE=INNODB;;

	


