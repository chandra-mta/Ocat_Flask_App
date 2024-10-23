#!/home/ascds/DS.release/bin/perl

use DBI;
use DBD::Sybase;
use CGI qw/:standard :netscape /;

#########################################################################################################
#													#
#	extract_too_list.perl: extract information about too and ddt, and figure out who is in charge	#
#			       of these observations.							#
#													#
#		author: t. isobe (tisobe@cfa.harvard.edu)						#
#													#
#		last update: Oct 02, 2012								#
#													#
#########################################################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011)  this is user cus version
#

$test_run  = 0;                                                                # live run
#$test_run  = 1;                                                                 # tst run case  

if($test_run == 1){
        $d_path = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/";           # test directory list path
}else{  
        $d_path = "/data/udoc1/ocat/Info_save/";                               # live directory list path
}

open(IN, "$d_path/dir_list");

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
#--- current ao number
#

$current_ao_no = 14;			#---- 	THIS MUST BE UPDATE EVERY TIME NEW AO CYCLE STARTS !!

#
#--- find today's date
#

($usec, $umin, $uhour, $umday, $umon, $uyear, $uwday, $uyday, $uisdst)= localtime(time);
$this_year = 1900 + $uyear;
$past_year = $this_year -1;

#
#--- find who is in charge today
#

$today_person = find_person_in_charge();

#
#---- read too and ddt in the previous monitoring list
#

open(FH, "$data_dir/monitor_too_ddt");

@too_ddt_monitoring = ();
@tdm_person	    = ();
@tdm_cnt            = 0;

while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	push(@too_ddt_monitoring, $atemp[0]);
	push(@tdm_person,         $atemp[1]);
	$tdm_cnt++;
}
close(FH);


#
#--- read currnet ddt and too lists
#
@sp_obsid = ();
@sp_poc   = ();
$sp_cnt   = 0;
open(FH, "$data_dir/ddt_list");
while(<FH>){
	chomp $_;
	@atemp = split(/\t+/, $_);
	push(@sp_obsid, $atemp[2]);
	push(@sp_poc,   $atemp[4]);
	$sp_cnt++;
}
close(FH);

open(FH, "$data_dir/too_list");
while(<FH>){
	chomp $_;
	@atemp = split(/\t+/, $_);
	push(@sp_obsid, $atemp[2]);
	push(@sp_poc,   $atemp[4]);
	$sp_cnt++;
}
close(FH);


#
#--- now read the entire records
#

open(FH, "$obs_ss/sot_ocat.out");

@new_obs_list = ();
@unobserved   = ();

system("cp $data_dir/normal_list $data_dir/normal_list~");
open(OUT, ">$data_dir/normal_list");	#--- print out none ddt/too data (at the end of the loop)

OUTER:
while(<FH>){
	chomp $_;
	@atemp  =  split(/\^/, $_);
	@btemp  =  split(/\s+/, $atemp[15]);
	$obsid  =  $atemp[1];
	$obsid  =~ s/\s+//g;
	$seqno  =  $atemp[3];
	$seqno  =~ s/\s+//g;
	$otype  =  lc($atemp[14]);
	$otype  =~ s/\s+//g;
	$status =  $atemp[16];
	$status =~ s/\s+//g;

	%{status.$obsid} = (status => ["$status"]);

	push(@new_obs_list, $obsid);
	if($status =~ /scheduled/ || $status =~ /unobserved/){
			push(@unobserved, $_);
	}

#
#--- we care only unobserved, scheduled, or observed and achived but less than a year old data
#
	if($status =~ /scheduled/ || $status =~ /unobserved/ 
			|| (($status =~ /observed/ || $status =~ /archived/) && $btemp[2] >= $past_year)){

		find_group();
#
#--- if AO is really old, ignore
#

		%{obs_ao_str.$obsid} = (ao =>["$obs_ao_str"]);

		$ao_diff = $current_ao_no - $obs_ao_str;
		if($ao_diff > 3){
			next OUTER;
		}

		if($otype !~ /ddt/i || $otype !~ /too/i){
			print OUT "$otype\t$seq_nbr\t$obsid\t$status\n";
		}
	}
}
close(OUT);
close(FH);


@new_obs_list_sorted = sort{$a<=>$b} @new_obs_list;

#
#--- read the previous obsid list
#

open(FH, "$data_dir/past_obs_list");
@past_obs_list = ();
$ptot          = 0;
while(<FH>){
	chomp $_;
	push(@past_obs_list, $_);
	$ptot++;
}
close(FH);

@past_obs_list_sorted = sort{$a<=>$b} @past_obs_list;

#
#--- compare the past and current obsid lists to find possible new entries
#

@keep = ();
$kcnt = 0;
system("mv $data_dir/past_obs_list $data_dir/past_obs_list~");
open(OUT2, "> $data_dir/past_obs_list");
$j = 0;
OUTER:
foreach $ent (@new_obs_list_sorted){
	print OUT2 "$ent\n";

	if($j >= $ptot){
		push(@keep, $ent);
		$kcnt++;
	}elsif($ent == $past_obs_list_sorted[$j]){
		$j++;
		next OUTER;
	}elsif($ent < $past_obs_list_sorted[$j]){
		$k = $j - 10;
		for($m = $k; $m < $j; $m++){
			if($ent == $past_obs_list_sorted[$m]){
				next OUTER;
			}
		}	
		push(@keep, $ent);
		$kcnt++;
		next OUTER;
	}elsif($ent > $past_obs_list_sorted[$j]){
		OUTER2:
		while($ent > $past_obs_list_sorted[$j]){
			$j++;
			if($ent <= $past_obs_list[$j]){
				if($ent < $past_obs_list[$j]){
					push(@keep, $ent);
					$kcnt++;	
				}
				next OUTER2;
			}
		}
	}
}	
close(OUT2);
		
system("cp $data_dir/new_obs_list $data_dir/new_obs_list~");
#
#--- check whether the status changed from the last time
#
open(FH, "$data_dir/new_obs_list");
open(OUT, ">$temp_dir/temp_new_obs_list");
OUTER:
while(<FH>){
	chomp $_;
	@atemp   = split(/\s+/, $_);
	$ao      = ${obs_ao_str.$atemp[2]}{ao}[0];
#
#--- if the observation is really old, ignore
#
	$ao_diff = $current_ao_no  - $ao;
	if($ao_diff > 3){
		next OUTER;
	}

	$obsid = $atemp[2];
	find_group();
#	if($atemp[5] == $ao && $type !~ /TOO/i && $type !~ /DDT/i){
	if($type !~ /TOO/i && $type !~ /DDT/i){
		match_usint_person();
	}else{
		$mup = $atemp[4];
	}

	if(${status.$atemp[2]}{status}[0] !~ /archived/){
		if($status =~ /observed/ && $status !~ /unobserved/){
			find_obs_date();
		}else{
			if($soe_st_sched_date ne ''){
				$date = $soe_st_sched_date;
			}elsif($lts_lt_plan ne ''){
				$date = $lts_lt_plan;
			}else{
				$date = 'NA';
			}
		}

		print OUT  "$atemp[0]\t";
		print OUT  "$atemp[1]\t";
		print OUT  "$atemp[2]\t";
#		print OUT  "${status.$atemp[2]}{status}[0]\t";
		print OUT  "$status\t";
		print OUT  "$mup\t";
		print OUT  "$ao\t";
		print OUT  "$date\n";
	}
}
close(OUT);
close(FH);

system("mv $temp_dir/temp_new_obs_list $data_dir/new_obs_list");
		

#
#--- if there are new observation, check it status, and add person in charge
#

if($kcnt > 0){
	$notify = 0;
	$save_lien = '';
	open(OUT2, ">> $data_dir/new_obs_list");
	OUTER3:
	foreach $ent (@unobserved){
		@atemp = split(/\^/, $ent);
		$atemp[1] =~ s/\s+//g;
		$atemp[2] =~ s/\s+//g;
		foreach $comp (@keep){
			if($comp =~ /$atemp[1]/){

				$obsid = $atemp[1];
				find_group();			#---- find instrument, grating, seq #, ao # etc

				if($soe_st_sched_date ne ''){
					$date = $soe_st_sched_date;
				}elsif($lts_lt_plan ne ''){
					$date = $lts_lt_plan;
				}else{
					$date = 'NA';
				}

#				if($type =~ /too/i || $type =~ /ddt/i || $obs_ao_str < $current_ao_no){
				if($type =~ /too/i || $type =~ /ddt/i){
					$person_in_charge = $today_person;

					if($type =~ /too/i || $type =~ /ddt/i){
						check_monitoring();			#--- check whether this obsid is in monitoring list
					}

					if($targname =~ /Crab/i){
						$person_in_charge = 'ppp';
					}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
						$person_in_charge = 'sjw';
					}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
						$person_in_charge = lc($grating);
					}
				}else{
					match_usint_person();		#---- find who is in charge

					if($targname =~ /Crab/i){
						$person_in_charge = 'ppp';
					}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
						$person_in_charge = 'sjw';
#					}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
#						$person_in_charge = lc($grating);
					}
				}
				$ao_diff = $current_ao_no - $obs_ao_str;
				if($ao_diff > 3){
					next OUTER3;
				}elsif($type =~ /too/i || $type =~ /ddt/i){

					print OUT2 "$type\t$seq_nbr\t$atemp[1]\t$status\t$person_in_charge\t$obs_ao_str\t$date\n";
					$save_line = "$save_line"."$type\t$seq_nbr\t$atemp[1]\t$status\t$person_in_charge\n";
					if($obs_ao_str > $current_ao_no){
						$notify    = $obs_ao_str;
					}
				}elsif($obs_ao_str < $current_ao_no){

					print OUT2 "$type\t$seq_nbr\t$atemp[1]\t$status\t$person_in_charge\t$obs_ao_str\t$date\n";
#					$save_line = "$save_line"."$type\t$seq_nbr\t$atemp[1]\t$status\t$person_in_charge\n";
					$save_line = "$save_line"."$type\t$seq_nbr\t$atemp[1]\t$status\t$mup\n";

				}elsif($obs_ao_str > $current_ao_no){

					print OUT2 "$type\t$seq_nbr\t$atemp[1]\t$status\t$person_in_charge\t$obs_ao_str\t$date\n";
					$save_line = "$save_line"."$type\t$seq_nbr\t$atemp[1]\t$status\t$person_in_charge\n";
					$notify    = $obs_ao_str;

				}else{
					print OUT2 "$type\t$seq_nbr\t$atemp[1]\t$status\t$mup\t$obs_ao_str\t$date\n";
					$save_line = "$save_line"."$type\t$seq_nbr\t$atemp[1]\t$status\t$mup\n";
				}
				next OUTER3;
			}
		}
	}
	close(OUT2);
#
#--- if there is a new obsid which is not too or ddt, notify for verification
#

	open(OUT2, ">$temp_dir/temp_email");
	if($kcnt == 1){
		print OUT2 "There is a newly assigned ObsID. \n";
	}else{
		print OUT2 "There are $kcnt newly assigned ObsIDs. \n";
	}
	print OUT2 "$save_line";
	close(OUT2);

	system("cat $temp_dir/temp_email | mailx -s\"Subject: New ObsIDs added\n\" isobe\@head.cfa.harvard.edu");
	if($test_run == 0){
		system("cat $temp_dir/temp_email | mailx -s\"Subject: New ObsIDs added\n\" swolk\@head.cfa.harvard.edu");
	}
	$update =`date`;
	system("cat $temp_dir/temp_email >> $data_dir/added_obsids");
	system("rm $temp_dir/temp_email");

#
#--- if a new AO cycle started notify the fact. you need to update a part of the code.
#

	if($notify > 0){

		open(OUT2, ">$temp_dir/temp_email");
		print OUT2 "It seems a new AO cycle started. You should change the line 33 \n";
		print OUT2 "$current_ao_no vaule to $nofity in extract_too_list.perl. \n";
		close(OUT2);
	
		system("cat $temp_dir/temp_email | mailx -s\"Subject: New AO Cycle Started!!\n\"  isobe\@head.cfa.harvard.edu");
		system("rm $temp_dir/temp_email");
	}
}
			

###########################################################################################
###  find_person_in_charge: find person in charge                                       ###
###########################################################################################

sub find_person_in_charge{

        open(FH, "$data_dir/this_week_person_in_charge");

        TOUTER:
        while(<FH>){
                chomp $_;
                if($_ =~ /#/){
                        next TOUTER;
                }else{
                        @atemp     = split(/\,/, $_);
                        $poc_email = $atemp[4];
                        open(IN, "$data_dir/personal_list");
                        while(<IN>){
                                chomp $_;
                                if($_ =~ /$poc_email/){
                                        @btemp = split(/<>/, $_);
                                        $person_in_charge = $btemp[5];

					if($btemp[5] =~ /pzhao/i)    {$person_in_charge = "ping"}
					if($btemp[5] =~ /swolk/i)    {$person_in_charge = "sjw"}
					if($btemp[5] =~ /nadams/i)   {$person_in_charge = "nraw"}
					if($btemp[5] =~ /bwargelin/i){$person_in_charge = "bw"}
					
                                        last TOUTER;
                                }
                        }
                        close(IN);
                        $person_in_charge = 'TBD';
                }
        }
        close(FH);

        return $person_in_charge;
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
        }else{
		@group_obsid = ();
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
        }else{
		@monitor_series = ();
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
	
#------------------------------------
#-------    get values from prop_info
#------------------------------------

        $sqlh1 = $dbh1->prepare(qq(select
                prop_num,title,joint from prop_info
        where ocat_propid=$ocat_propid));
        $sqlh1->execute();
        @prop_infodata = $sqlh1->fetchrow_array;
        $sqlh1->finish;

        $proposal_number = $prop_infodata[0];
        $proposal_title  = $prop_infodata[1];
        $proposal_joint  = $prop_infodata[2];
        $proposal_hst    = $prop_infodata[3];
        $proposal_noao   = $prop_infodata[4];
        $proposal_xmm    = $prop_infodata[5];
        $proposal_rxte   = $prop_infodata[6];
        $proposal_vla    = $prop_infodata[7];
        $proposal_vlba   = $prop_infodata[8];

	


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


###########################################################################################
###########################################################################################
###########################################################################################

sub match_usint_person{

        if($type    =~ /cal/i){
                $mup = 'cal';
        }elsif($grating =~ /letg/i){
                $mup = 'letg';
        }elsif($grating =~ /hetg/i){
                $mup = 'hetg';
        }elsif($instrument =~ /hrc/i){
                $mup = 'hrc';
        }elsif($seq_nbr >= 100000 && $seq_nbr < 300000){
                $mup = 'sjw';
        }elsif($seq_nbr >= 300000 && $seq_nbr < 500000){
                $mup = 'nraw';
        }elsif($seq_nbr >= 500000 && $seq_nbr < 600000){
                $mup = 'jeanconn';
        }elsif($seq_nbr >= 600000 && $seq_nbr < 700000){
                $mup = 'ping';
        }elsif($seq_nbr >= 700000 && $seq_nbr < 800000){
#                $mup = 'emk';
                $mup = 'brad';
        }elsif($seq_nbr >= 800000 && $seq_nbr < 900000){
                $mup = 'ping';
        }elsif($seq_nbr >= 900000 && $seq_nbr < 1000000){
                $mup = 'das';
        }
}


##############################################################################################
### find_obs_date: extract obs starting date from mit web site                             ###
##############################################################################################

sub find_obs_date{
	system("/opt/local/bin/lynx -source http://acis.mit.edu/cgi-bin/get-obsid\?id=$obsid > $temp_dir/ztemp");
	open(IN, "$temp_dir/ztemp");
	$chk = 0;
	OUTER:
	while(<IN>){
		chomp $_;	
		if($chk > 0){
			@dtemp = split(/\<tt\>/, $_);
			@ftemp = split(/\</, $dtemp[1]);
			$date  = $ftemp[0];
			last OUTER;
		}
		if($_ =~ /Start Date:/){
			$chk = 1;
		}
	}
	close(IN);
	system("rm $temp_dir/ztemp");
	
	@dtemp = split(/\s+/, $date);
	@ftemp = split(/-/,   $dtemp[0]);
	
	if($ftemp[1] == 1){
		$mon = "Jan";
	}elsif($ftemp[1] == 2){
		$mon = "Feb";
	}elsif($ftemp[1] == 3){
		$mon = "Mar";
	}elsif($ftemp[1] == 4){
		$mon = "Apr";
	}elsif($ftemp[1] == 5){
		$mon = "May";
	}elsif($ftemp[1] == 6){
		$mon = "Jun";
	}elsif($ftemp[1] == 7){
		$mon = "Jul";
	}elsif($ftemp[1] == 8){
		$mon = "Aug";
	}elsif($ftemp[1] == 9){
		$mon = "Sep";
	}elsif($ftemp[1] == 10){
		$mon = "Oct";
	}elsif($ftemp[1] == 11){
		$mon = "Nov";
	}elsif($ftemp[1] == 12){
		$mon = "Dec";
	}
	
	@etemp = split(/:/, $dtemp[1]);
	$part = 'AM';
	$time = $etemp[0];
	if($time == 0){
		$time = 12;
	}elsif($etemp[0] >= 12){
		$part = 'PM';
		if($etemp[0] > 12){
			$time = $etemp[0] - 12;
		}
	}
	
	$time = "$time:$etemp[1]"."$part";
	
	$date = "$mon $ftemp[2] $ftemp[0] $time";
}

##############################################################################################################
### check_monitoring: check obsid is in a monitoring list, and if so, whether poc is already assigned      ###
##############################################################################################################

sub check_monitoring {

	$dm_chk = 0;
	OUTER:
	for($dm = 0; $dm < $tdm_cnt; $dm++){
		if($too_ddt_monitoring[$dm] == $obsid){
			$person_in_charge = $tdm_person[$dm];
			$dm_chk = 1;
			last OUTER;
		}
	}

	if($dm_chk == 0){
		$mchk = 0;
		foreach (@monitor_series){
			$mchk++;
		}
		$gchk = 0;
		foreach (@group_obsid){
			$gchk++;
		}

		if($mchk > 0 || $gchk > 0){
			system("cp $data_dir/monitor_too_ddt $data_dir/monitor_too_ddt~");
			open(DOUT, ">>$data_dir/monitor_too_ddt");
			for($dm = 0; $dm < $mchk; $dm++){
				print DOUT "$monitor_series[$dm]\t$person_in_charge\t$monitor_series[0]\t$proposal_number\n";
			}
			for($dm = 0; $dm < $gchk; $dm++){
				print DOUT "$group_obsid[$dm]\t$person_in_charge\t$group_obsid[0]\t$proposal_number\n";
			}
			close(DOUT);
		}
	}
}

				
