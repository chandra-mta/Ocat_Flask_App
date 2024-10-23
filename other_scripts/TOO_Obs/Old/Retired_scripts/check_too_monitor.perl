#!/home/ascds/DS.release/bin/perl

use DBI;
use DBD::Sybase;

#################################################################################################
#												#
#	check_too_monitor.perl: check monitor_too_ddt file to see whether we can drop any entry	#
#												#
#		author: t. isobe (tisobe@cfa.harvard.edu)					#
#												#
#		last update: Oct 02, 2012							#
#												#
#################################################################################################

#
#--- read and set directory pathes
#

open(IN, '/data/udoc1/ocat/Info_save/dir_list');
while(<IN>){
        chomp $_;
        @atemp    = split(/:/, $_);
        $atemp[0] =~ s/\s+//g;
        if($atemp[0] =~ /obs_ss/){
                $obs_ss   = $atemp[1];
        }elsif($atemp[0]  =~ /pass_dir/){
                $pass_dir = $atemp[1];
        }elsif($atemp[0]  =~ /ctemp_dir/){
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


#
#--- read too/ddt obsid in monitor list
#

open(FH, "$data_dir/monitor_too_ddt");

@obsid_list = ();
@user       = ();
@group      = ();
$total      = 0;

while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	push(@obsid_list, $atemp[0]);
	push(@user,       $atemp[1]);
	push(@group,      $atemp[2]);
	$total++;
}
close(FH);

#
#--- read an older monitor list
#

open(FH, "$data_dir/monitor_too_ddt~");

@old_obsid_list = ();
@old_user       = ();
@old_group      = ();
$old_total      = 0;

while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	push(@old_obsid_list, $atemp[0]);
	push(@old_user,       $atemp[1]);
	push(@old_group,      $atemp[2]);
	$old_total++;
}
close(FH);

#
#--- check whether there are any updates
#

$print_status1 = 0;
if($total == $old_total){
	OUTER:
	for($i = 0; $i < $total; $i++){
		if($obsid_list[$i] != $old_obsid_list[$i]){
			$print_status1 = 1;
			last OUTER;
		}
	}
}else{
	$print_status1 = 1;
}




#
#--- update initial setup
#

@update_obsid  = ();
@updated_user  = ();
@updatedgroup  = ();
$cnt           = 0;

@chk_obsid     = ($obsid_list[0]);
$guser         = $user[0];
$gchk          = $group[0];
$begin         = 0;
$lastone       = $total -1;

FOUTER:
for($i = 1; $i < $total; $i++){

#
#--- find obsid in the same monitor group
#

	if($group[$i] == $gchk){
		push(@chk_obsid, $obsid_list[$i]);

		if($i == $lastone){
#
#--- if this is the last entry, check the status for the group entries
#
			OUTER:
			foreach $obsid (@chk_obsid){

				find_group();

				if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){
					for($m = $bdgin; $m < $total; $m++){
						push(@update_obsid, $obsid_list[$m]);
						push(@update_user,  $guser);
						push(@updategroup,  $gchk);
						$cnt++;
					}
					last FOUTER;
				}
			}
		}
	}elsif($group[$i] != $gchk){
#
#--- if the group is changed, check the status of the previous group.
#

		OUTER:
		foreach $obsid (@chk_obsid){
			find_group();
			if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){
				for($m = $bdgin; $m < $i; $m++){
					push(@update_obsid, $obsid_list[$m]);
					push(@update_user,  $guser);
					push(@updategroup,  $gchk);
					$cnt++;
				}
				last OUTER;
			}
		}

		@chk_obsid = ($obsid_list[$i]);
		$guser     = $user[$i];
		$gchk      = $group[$i];
		$bdgin     = $i;
#
#--- if this is the last one, check its status
#
		if($begin == $lastone){
			$obsid = $chk_obsid[0];
			find_group();
			if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){
				push(@update_obsid, $obsid);
				push(@update_user,  $guser);
				push(@updategroup,  $gchk);
				$cnt++;
			}
			last FOUTER;
		}
	}
}


#
#--- check any chanages occurred 
#

$print_status2 = 0;
if($total == $cnt){
	OUTER:
	for($i = 0; $i < $total; $i++){
		if($obsid_list[$i] != $update_obsid[$i]){
			$print_status2 = 1;
			last OUTER;
		}
	}
}else{
	$print_status2 = 1;
}

#
#--- if any changes occurred, update the list 
#

if($print_status2 == 1){

#
#--- move the old one to "~" save
#

	system("mv $data_dir/monitor_too_ddt $data_dir/monitor_too_ddt~");	

#
#--- print out the updates
#

	open(OUT, ">$data_dir/monitor_too_ddt");

	for($i = 0; $i < $cnt; $i++){
		print OUT "$update_obsid[$i]\t$update_user[$i]\t$updategroup[$i]\n";
	}
	close(OUT);
}

#
#--- notify admin if any changes happened
#

if($print_status1 == 1 || $print_status2 == 1){
	open(OUT, ">$temp_dir/zztemp");
	print OUT "$data_dir/monitor_too_ddt is updated. Please check whether the change was made correctly.\n";
	close(OUT);

	system("cat $temp_dir/zztemp | mailx -s\"Subject:monitor_too_ddt is updated\n\" isobe\@head.cfa.harvard.edu");
	system("rm  $temp_dir/zztemp");
}
				
		
###########################################################################################
### find_group: find related obsids                                                     ###
###########################################################################################

sub find_group {

#------------------------------------------------
#-------  database username, password, and server
#------------------------------------------------

        $db_user = "browser";
        $server  = "ocatsqlsrv";

        $db_passwd =`cat $pass_dir/.targpass`;
        chomp $db_passwd;

#--------------------------------------
#-------- open connection to sql server
#--------------------------------------

        my $db = "server=$server;database=axafocat";
        $dsn1  = "DBI:Sybase:$db";
        $dbh1  = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});


#
#--- find a group_id etc
#

#------------------------------------------------------
#---------------  get stuff from target table, clean up
#------------------------------------------------------

        $sqlh1 = $dbh1->prepare(qq(select
                        group_id,pre_id,pre_min_lead,pre_max_lead,grating,type,instrument,obs_ao_str,status,seq_nbr,ocat_propid,
			soe_st_sched_date,lts_lt_plan
        from target where obsid=$obsid));

        $sqlh1->execute();
        @targetdata   = $sqlh1->fetchrow_array;
        $sqlh1->finish;

        $group_id     = $targetdata[0];
        $pre_id       = $targetdata[1];
        $pre_min_lead = $targetdata[2];
        $pre_max_lead = $targetdata[3];
        $grating      = $targetdata[4];
        $type         = $targetdata[5];
        $instrument   = $targetdata[6];
        $obs_ao_str   = $targetdata[7];
	$status       = $targetdata[8];
	$seq_nbr      = $targetdata[9];
	$ocat_propid  = $targetdata[10];
	$soe_st_sched_date = $targetdata[11];
	$lts_lt_plan  = $targetdata[12];

        $group_id     =~ s/\s+//g;
        $pre_id       =~ s/\s+//g;
        $pre_min_lead =~ s/\s+//g;
        $pre_max_lead =~ s/\s+//g;
        $grating      =~ s/\s+//g;
        $type         =~ s/\s+//g;
        $instrument   =~ s/\s+//g;
        $obs_ao_str   =~ s/\s+//g;
        $status       =~ s/\s+//g;
        $seq_nbr      =~ s/\s+//g;
        $ocat_propid  =~ s/\s+//g;

        $monitor_flag = "N";
        if ($pre_id){
                $monitor_flag = "Y";
        }

        $sqlh1 = $dbh1->prepare(qq(select distinct pre_id from target where pre_id=$obsid));
        $sqlh1->execute();
        $pre_id_match = $sqlh1->fetchrow_array;
        $sqlh1->finish;
        if($pre_id_match){
                $monitor_flag = "Y";
        }

        if ($group_id){
                $monitor_flag = "N";
                undef $pre_min_lead;
                undef $pre_max_lead;
                undef $pre_id;

                $sqlh1 = $dbh1->prepare(qq(select
                        obsid
                from target where group_id = \'$group_id\'));
                $sqlh1->execute();

                while(@group_obsid = $sqlh1->fetchrow_array){
                        $group_obsid = join( @group_obsid);
                        if($usint_on =~ /test/){
                                @group       = (@group, "<a href=\"$test_http\/ocatdata2html.cgi\?$group_obsid\">
$group_obsid<\/a> ");
                        }else{
                                @group       = (@group, "<a href=\"$usint_http\/ocatdata2html.cgi\?$group_obsid\"
>$group_obsid<\/a> ");
                        }
                }

#------  output formatting

                $group_count = 0;
                foreach (@group){
                        $group_count ++;
                        if(($group_count % 10) == 0){
                                @group[$group_count - 1] = "@group[$group_count - 1]<br>";
                        }
                }
                $group_cnt    = $group_count;
                $group_count .= " obsids for ";
        }

#------------------------------------------------------------------
#---- if monitoring flag is Y, find which ones are monitoring data
#------------------------------------------------------------------

        if($monitor_flag =~ /Y/i){
                &series_rev($obsid);
                &series_fwd($obsid);
                %seen = ();
                @uniq = ();
                foreach $monitor_elem (@monitor_series) {
                        push(@uniq, $monitor_elem) unless $seen{$monitor_elem}++;
                }
                @monitor_series = sort @uniq;
        }

#-------------------------------------------------
#---- updating AO number for the observation
#---- ao value is different from org and current
#-------------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select
		ao_str
	from prop_info where ocat_propid=$ocat_propid ));

	$sqlh1->execute();
	@updatedata   = $sqlh1->fetchrow_array;
	$sqlh1->finish;
	if($updatedata[0] =~ /\d/){
		$obs_ao_str = $updatedata[0];
		$obs_ao_str =~ s/\s+//g;
	}
	
	


}

####################################################################
### series_rev: getting mointoring observation things           ####
####################################################################

sub series_rev{

#--------------------------------------------------------------
#--- this one and the next subs are taken from target_param.cgi
#--- written by Mihoko Yukita.(10/28/2003)
#--------------------------------------------------------------

        push @monitor_series, $_[0];
        my @partial_series;
        $sqlh1 = $dbh1->prepare(qq(select
                pre_id from target where obsid = $_[0]));
        $sqlh1->execute();
        my $row;

        while ($row = $sqlh1->fetchrow){
                return if (! $row =~ /\d+/);
                push @partial_series, $row;
                $sqlh2 = $dbh1->prepare(qq(select
                        obsid from target where pre_id = $row));
                $sqlh2->execute();
                my $new_row;

                while ($new_row = $sqlh2->fetchrow){
                        if ($new_row != $_[0]){
                                &series_fwd($new_row);
                        }
                }
                $sqlh2->finish;
        }
        $sqlh1->finish;

        $skip = 0;
        OUTER:
        foreach $ent (@monitor_series){
                foreach $comp (@partial_series){
                        if($ent == $comp){
                                $skip = 1;
                                last OUTER;
                        }
                }
        }


        if($skip == 0){
                foreach $monitor_elem (@partial_series) {
                        &series_rev($monitor_elem);
                }
        }
}

####################################################################
### series_fwd: getting monitoring observation things           ####
####################################################################

sub series_fwd{
        push @monitor_series, $_[0];
        my @partial_series;
        $sqlh1 = $dbh1->prepare(qq(select
                obsid from target where pre_id = $_[0]));
        $sqlh1->execute();
        my $row;

        while ($row = $sqlh1->fetchrow){
                push @partial_series, $row;
                $sqlh2 = $dbh1->prepare(qq(select
                        pre_id from target where obsid = $row));
                $sqlh2->execute();
                my $new_row;

                while ($new_row = $sqlh2->fetchrow){
                        if ($new_row != $_[0]){
                                &series_rev($new_row);
                        }
                }
                $sqlh2->finish;
        }
        $sqlh1->finish;

        $skip = 0;
        OUTER:
        foreach $ent (@monitor_series){
                foreach $comp (@partial_series){
                        if($ent == $comp){
                                $skip = 1;
                                last OUTER;
                        }
                }
        }

        if($skip == 0){
                foreach $monitor_elem (@partial_series) {
                        &series_fwd($monitor_elem);
                }
        }
}

