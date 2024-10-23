#!/home/ascds/DS.release/bin/perl

BEGIN
{
    $ENV{SYBASE} = "/soft/SYBASE_OCS15.5";
}

use DBI;
use DBD::Sybase;

#################################################################################################
#												#
#	make_access_list.perl: create an access list for ocatdata2html.cgi			#
#												#
#		author: t. isobe (tisobe@cfa.harvard.edu)					#
#												#
#		last update: May 14, 2013							#
#												#
#################################################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011) --- this is user: mta version
#

open(IN, '/data/mta4/CUS/www/Usint/ocat/Info_save/dir_list');
while(<IN>){
        chomp $_;
        @atemp    = split(/:/, $_);
        $atemp[0] =~ s/\s+//g;
        if($atemp[0] =~ /obs_ss/){
                $obs_ss   = $atemp[1];
        }elsif($atemp[0]  =~ /pass_dir/){
                $pass_dir = $atemp[1];
        }elsif($atemp[0]  =~ /mtemp_dir/){
                $temp_dir = $atemp[1];
        }elsif($atemp[0]  =~ /too_dir/){
                $data_dir = $atemp[1];
        }elsif($atemp[0]  =~ /ocat_dir/){
                $real_dir = $atemp[1];
        }elsif($atemp[0]  =~ /test_dir/){
                $test_dir = $atemp[1];
        }elsif($atemp[0]  =~ /cus_dir/){
                $cus_dir  = $atemp[1];
        }
}
close(IN);

$ocat_dir = $real_dir;


#------------------------------------------------
#-------  database username, password, and server
#------------------------------------------------

$db_user = "browser";
$server  = "ocatsqlsrv";

#       $db_user="browser";
#       $server="sqlbeta";

$db_passwd =`cat $pass_dir/.targpass`;
chop $db_passwd;

#--------------------------------------
#-------- open connection to sql server
#--------------------------------------

my $db = "server=$server;database=axafocat";
$dsn1  = "DBI:Sybase:$db";
$dbh1  = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});

#------------------------------------------------------
#---------------  get stuff from target table, clean up
#------------------------------------------------------

@list = ();
$cnt  = 0;

$sqlh1 = $dbh1->prepare(qq(select
	obsid   , 
	status  , 
	type    ,
	ocat_propid
from target where status='unobserved'));
$sqlh1->execute();

while(@targetdata = $sqlh1->fetchrow_array){
	$type = lc($targetdata[2]);
	if($type !~/TOO/i && $type !~ /CAL/i && $type !~ /DDT/i){
		$line = "$targetdata[0]\t$targetdata[1]\t$type\t$targetdata[3]";
		push(@list, $line);
		$cnt++;
	}
}
$sqlh1->finish;

$sqlh1 = $dbh1->prepare(qq(select
	obsid   , 
	status  , 
	type    ,
	ocat_propid
from target where status='scheduled'));
$sqlh1->execute();

while(@targetdata = $sqlh1->fetchrow_array){
	$type = lc($targetdata[2]);
	if($type !~/TOO/i && $type !~ /CAL/i && $type !~ /DDT/i){
		$line = "$targetdata[0]\t$targetdata[1]\t$type\t$targetdata[3]";
		push(@list, $line);
		$cnt++;
	}
}
$sqlh1->finish;

#-------------------------------------------------------------
#<<<<<<------>>>>>>  switch to axafusers <<<<<<------>>>>>>>>
#-------------------------------------------------------------

$db   = "server=$server;database=axafusers";
$dsn1 = "DBI:Sybase:$db";
$dbh1 = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});

$save_data = ();
for($i = 0; $i < $cnt; $i++){
	@atemp = split(/\t+/, $list[$i]);
	$proposal_id = $atemp[3];

#--------------------------------
#-----  get proposer's name
#--------------------------------

       	$sqlh1 = $dbh1->prepare(qq(select
               	last from person_short s,axafocat..prop_info p
       	where p.ocat_propid=$proposal_id and s.pers_id=p.piid));
       	$sqlh1->execute();
       	@namedata = $sqlh1->fetchrow_array;
       	$sqlh1->finish;

       	$pi_last  = $namedata[0];

       	$sqlh1 = $dbh1->prepare(qq(select
               	first from person_short s,axafocat..prop_info p
       	where p.ocat_propid=$proposal_id and s.pers_id=p.piid));
       	$sqlh1->execute();
       	@namedata = $sqlh1->fetchrow_array;
       	$sqlh1->finish;

       	$pi_first  = $namedata[0];

#---------------------------------------------------------------------------
#------- if there is a co-i who is observer, get them, otherwise it's the pi
#---------------------------------------------------------------------------

        $sqlh1 = $dbh1->prepare(qq(select
               	coi_contact from person_short s,axafocat..prop_info p
        where p.ocat_propid = $proposal_id));
        $sqlh1->execute();
        ($observerdata) = $sqlh1->fetchrow_array;
        $sqlh1->finish;

       	if ($observerdata =~/N/){
               	$obsr_last  = $pi_last;
               	$obsr_first = $pi_first;
       	} else {
               	$sqlh1 = $dbh1->prepare(qq(select
                       	last  from person_short s,axafocat..prop_info p
               	where p.ocat_propid = $proposal_id and p.coin_id = s.pers_id));
               	$sqlh1->execute();
               	($observerdata) = $sqlh1->fetchrow_array;
               	$sqlh1->finish;

               	$obsr_last=$observerdata;

               	$sqlh1 = $dbh1->prepare(qq(select
                       	first from person_short s,axafocat..prop_info p
               	where p.ocat_propid = $proposal_id and p.coin_id = s.pers_id));
               	$sqlh1->execute();
               	($observerdata) = $sqlh1->fetchrow_array;
               	$sqlh1->finish;

               	$obsr_first=$observerdata;
       	}

	$pi_last    = lc($pi_last);
	$pi_first   = lc($pi_first);
	$obsr_last  = lc($obsr_last);
	$obsr_first = lc($obsr_first);

	$pi_name    = "$pi_last:$pi_first";
	$observer   = "$obsr_last:$obsr_first";

#
#--- check length of word
#

	@btemp      = split(//, $ pi_name);
	$type       = lc ($type);
	$PI_name    = lc ($PI_name);
	$Observer   = lc ($Observer);
	$letter_cnt = 0;
	foreach(@btemp){
		$letter_cnt++;
	}
#
#--- format each data line
#
	if($letter_cnt < 8){
		$s_line = "$atemp[0]\t$atemp[1]\t$atemp[2]\t$pi_name\t\t\t$observer";
	}elsif($letter_cnt < 16){
		$s_line = "$atemp[0]\t$atemp[1]\t$atemp[2]\t$pi_name\t\t$observer";
	}else{
		$s_line = "$atemp[0]\t$atemp[1]\t$atemp[2]\t$pi_name\t$observer";
	}

	push(@save_data, $s_line);
}
$dbh1->disconnect();

@sorted_list = sort{$a<=>$b} @save_data;

#
#--- print out the sorted data
#

open(OUT, ">$obs_ss/access_list");
foreach $ent (@sorted_list){
	print OUT "$ent\n";
}
