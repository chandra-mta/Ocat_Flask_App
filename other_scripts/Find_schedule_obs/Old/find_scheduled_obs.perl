#!/usr/bin/perl

#################################################################################################
#												#
#	find_scheduled_obs.perl: find MP scheduled observations					#
#												#
#	author: t. isobe (tisobe@cfa.harvard.edu)						#
#												#
#	last update: Jun 08, 2016								#
#												#
#################################################################################################

#
#---- if this is usint version, set the following param to 'yes', otherwise 'no'
#

$usint_on = 'yes';                     ##### USINT Version
#$usint_on = 'no';                      ##### USER Version
#$usint_on = 'test_yes';                        ##### Test Version USINT
#$usint_on = 'test_no';                  ##### Test Version USER

#
#---- set a name and email address of a test person
#

$test_user  = 'isobe';
$test_email = 'isobe@head.cfa.harvard.edu';

#$test_user  = 'mta';
#$test_email = 'isobe@head.cfa.harvard.edu';

#$test_user  = 'brad';
#$test_email = 'brad@head.cfa.harvard.edu';

#$test_user  = 'swolk';
#$test_email = 'swolk@head.cfa.harvard.edu';

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


if($usint_on =~ /test/){
	$ocat_dir = $real_dir;
}else{
	$ocat_dir = $test_dir;
}

#
#--- find today's date
#

($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);

$uyear = 1900 + $year;
$mon   = $mon + 1;

$lmon  = conv_month_num_to_chr($mon);
$lmon  = uc($lmon);

$nmon  = $mon + 1;
$nyear = $uyear;

if($nmon > 12) {
	$nmon  = 1;
	$nyear = $uyear + 1;
}

$nlmon = conv_month_num_to_chr($nmon);
$nlmon = uc($nlmon);

#
#--- find today's date in sec from 1998.1.1.
#
	$today_in_sec = cnv_time_to_t1998("$uyear", "$yday", "00", "00", "00");
	
#
#--- find all MP OR lists scheduled to start after this day , use only the most recent one. 
#--- we check this month and the next (if exists).
#

$temp_list  = "$temp_dir/mpcrit_list";
$temp_list2 = "$temp_dir/mpcrit_list2";

system("ls -lrtd /data/mpcrit1/mplogs/$uyear/$lmon*  >  $temp_list");
$test = `ls -lrtd /data/mpcrit1/mplogs/$nyear/*`;
if($test =~ /$nlmon/){
    system("ls -lrtd /data/mpcrit1/mplogs/$nyear/$nlmon* >> $temp_list");
}

@line      = ();
@in_charge = ();
$cnt       = 0;

#
#--- find data file names which later than today's date
#

open(FH, "$temp_list");
while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	foreach $test (@atemp){
		if($test =~ /mplogs/){
			$dir = $test;
			last;
		}
	}
#
#--- check this month's data
#
	if($dir =~ /$lmon/){
        $test = "$dir".'/input/';
        $input = "$dir".'/input/';
        $chk  = is_dir_empty($test);
        if($chk == 1){
            $test = `ls $dir/input/*`;
            @tlist = split(/\n+/, $test);
            $chk2 = 0;
            foreach $ent (@tlist){
                @atemp = split(/\input\//, $ent);
                if($atemp[1] =~ /$lmon/){
                    $chk2 =1;
                    break;
                }
            }
            if($chk2 > 0){
                #$file = "$dir".'/input/'."$lmon*_*.or";            #--- -05/26/16

                $tchk = is_file_exist($dir, 'pre_scheduled');
                if($tchk == 1){
                    $nchk = is_dir_empty("$dir/pre_scheduled");
                }
                if($nchk ==1){
                    $file = "$dir".'/input/* '."$dir".'/pre_scheduled/* '."$dir".'/scheduled/*';
                }else{
                    $file = "$dir".'/input/* '."$dir".'/scheduled/*';
                }

	            system("ls -lrt $file > $temp_list2");

		        open(IN, "$temp_list2");
		        @list = ();
     
                $llmon = lc($lmon);
		        while(<IN>){
			        chomp $_;
			        @atemp = split(/\s+/,   $_);
                    $chk = 0;
			        foreach $test (@atemp){
				        if(($test =~ /mplogs/) && ($test =~ /\.or/)){
					        $in_line = $test;
                            $chk = 1;
					        last;
				        }
			        }

                    if($chk == 0){
                        next;
                    }

			        @btemp = split(/\//,    $in_line);

                    if($btemp[5] =~ /$lmon/){
			            @ctemp = split(/$lmon/, $btemp[5]);
                    }elsif($btemp[5] =~ /$llmon/){
			            @ctemp = split(/$llmon/, $btemp[5]);
                    }else{
                        next;
                    }
			        @dtemp = split(//,      $ctemp[1]);
			        $date  = "$dtemp[0]$dtemp[1]";
     
			        if($date > $mday){
				        @ctemp = split(/_/, $in_line);
				        @dtemp = split(/\.or/, $ctemp[1]);
				        if(($dtemp[0] =~ /\d/) || ($dtemp[0] =~ /[A-G]/)){      #---- 05/26/16
					        push(@list, $in_line);
				        }
			        }
		        }
		        close(IN);
		        system("rm $temp_list2");
#
#--- use only the last version of the same data file
#
		        $last = pop(@list);
		        push(@mp_list, $last);
     
		        if($atemp[2] =~ /\d/){
			        $aline = `ypcat -k passwd |grep $atemp[2]`;	# changing ID # to actual user name
			        @cline = split(/\s+/, $aline);
			        $person = $cline[0];
		        }else{
			        $person = $atemp[2];
		        }
		        push(@in_charge, $person);
            }
        }
#
#--- checking the next month
#
	}elsif($dir =~ /$nlmon/){
        $test = "$dir".'/input/';
        $chk  = is_dir_empty($test);
        if($chk == 1){
            $test = `ls $dir/input/*`;
            @tlist = split(/\n+/, $test);
            $chk2 = 0;
            foreach $ent (@tlist){
                @atemp = split(/\input\//, $ent);
                if($atemp[1] =~ /$nlmon/){
                    $chk2 =1;
                    break;
                }
            }
            if($chk2 > 0){
		        #$file = "$dir".'/input/'."$nlmon*_*.or";
                $tchk = is_file_exist($dir, 'pre_scheduled');
                if($tchk == 1){
                    $nchk = is_dir_empty("$dir/pre_scheduled");
                }
                if($nchk ==1){
                    $file = "$dir".'/input/* '."$dir".'/pre_scheduled/* '."$dir".'/scheduled/*';
                }else{
                    $file = "$dir".'/input/* '."$dir".'/scheduled/*';
                }

		        system("ls -lrt $file > $temp_list2");
		        open(IN, "$temp_list2");
		        @list = ();
     
                $lnlmon = lc($nlmon);
		        while(<IN>){
			        chomp $_;
			        @atemp = split(/\s+/,   $_);
                    $chk = 0;
			        foreach $test (@atemp){
				        if(($test =~ /mplogs/) && ($test =~ /\.or/)){
					        $in_line = $test;
                            $chk = 1;
					        last;
				        }
			        }
                    if($chk == 0){
                        $next;
                    }

			        @etemp = split(/_/, $in_line);
			        @ftemp = split(/\.or/, $etemp[1]);
			        if($ftemp[0] =~ /\d/){
				        @btemp = split(/\//,    $in_line);

                        if($btemp[5] =~ /$nlmon/){
				            @ctemp = split(/$nlmon/, $btemp[5]);
                        }elsif($btemp[5] =~ /$lnlmon/){
				            @ctemp = split(/$lnlmon/, $btemp[5]);
                        }else{
                            next;
                        }

				        @dtemp = split(//,      $ctemp[1]);
				        $date  = "$dtemp[0]$dtemp[1]";
				        push(@list, $in_line);
			        }
		        }
		        close(IN);
		        system("rm $temp_list2");

		        $last = pop(@list);
		        push(@mp_list, $last);
     
		        if($atemp[2] =~ /\d/){
			        $aline = `ypcat -k passwd |grep $atemp[2]`;
			        @cline = split(/\s+/, $aline);
			        $person = $cline[0];
		        }else{
			        $person = $atemp[2];
		        }
		        push(@in_charge, $person);
            }
        }
	}
}
close(FH);

system("rm $temp_list");

#
#--- open each file, and extreact obsids
#

@obsid_list    = ();
@need_sign_off = ();
$cnt_sign_off  = 0;
$cnt = 0;

foreach $ent (@mp_list){
	open(FH, "$ent");
	$start_read  = 0;
	$obs_read    = 0;
	$end_quick   = 0;
	$jchk        = 0;
	OUTER1:
	while(<FH>){
		chomp $_;
		if($_ =~ /SeqNbr/){
			$start_read++;
		}elsif($_ =~ /OR QUICK LOOK END/){
			$end_quick++;
		}elsif($start_read > 0 && $obs_read == 0 && $end_quick == 0){
			@atemp = split(/\s+/, $_);
			if($atemp[0] =~ /\d/ &&  $atemp[0] > 1000 && $atemp[1] =~ /\d/){
				push(@obsid_list, $atemp[1]);
				%{data.$atemp[1]} = (seqnbr    => ["$atemp[0]"],
						     name      => ["$atemp[2]"],
						     grating   => ['NONE'],
						     inst      => ['CAL'],
						     mp_person => ["$in_charge[$cnt]"]
						    );
			}
		}elsif($_ =~ /OBS\,/){
			$obs_read++;
		}elsif($obs_read > $jchk && $_ =~ /ID/){
			@atemp = split(/\,/, $_);
			@btemp = split(/=/,  $atemp[0]);
			$id    = $btemp[1];
			$jchk  = $obs_read;
		}elsif($obs_read > 0 && $obs_read == $jchk){
			if($_ =~ /CAL/i){
				$seqnbr  = ${data.$id}{seqnbr}[0];
				$name    = ${data.$id}{name}[0];
				$grating = ${data.$id}{grating}[0];
				$inst    = ${data.$id}{inst}[0];
				%{data.$id} = ( seqnbr    => ["$seqnbr"],
						name      => ['CAL'],
						grating   => ["$grating"],
						inst      => ["$inst"],
						mp_person => ["$in_charge[$cnt]"]
					      );
			}
			if($_ =~ /HETG/i){
				$seqnbr  = ${data.$id}{seqnbr}[0];
				$name    = ${data.$id}{name}[0];
				$grating = ${data.$id}{grating}[0];
				$inst    = ${data.$id}{inst}[0];
				%{data.$id} = ( seqnbr    => ["$seqnbr"],
						name      => ["$name"],
						grating   => ["HETG"],
						inst      => ["$inst"],
						mp_person => ["$in_charge[$cnt]"]
					      );
			}
			if($_ =~ /LETG/i){
				$seqnbr  = ${data.$id}{seqnbr}[0];
				$name    = ${data.$id}{name}[0];
				$grating = ${data.$id}{grating}[0];
				$inst    = ${data.$id}{inst}[0];
				%{data.$id} = ( seqnbr    => ["$seqnbr"],
						name      => ["$name"],
						grating   => ["LETG"],
						inst      => ["$inst"],
						mp_person => ["$in_charge[$cnt]"]
					      );
			}
			if($_  =~ /ACIS/){
				$seqnbr  = ${data.$id}{seqnbr}[0];
				$name    = ${data.$id}{name}[0];
				$grating = ${data.$id}{grating}[0];
				$inst    = ${data.$id}{inst}[0];
				%{data.$id} = ( seqnbr    => ["$seqnbr"],
						name      => ["$name"],
						grating   => ["$grating"],
						inst      => ["ACIS"],
						mp_person => ["$in_charge[$cnt]"]
					      );
			}
			if($_ =~ /HRC/){
				$seqnbr  = ${data.$id}{seqnbr}[0];
				$name    = ${data.$id}{name}[0];
				$grating = ${data.$id}{grating}[0];
				$inst    = ${data.$id}{inst}[0];
				%{data.$id} = ( seqnbr    => ["$seqnbr"],
						name      => ["$name"],
						grating   => ["$grating"],
						inst      => ["HRC"],
						mp_person => ["$in_charge[$cnt]"]
					      );
			}
		}
#
#--- if it is not signed off yet, keep it in a special list so that email can be sent out later
#
		if($_ =~ /not signed off/){
			$line = $_;
			$line =~ s/not signed off//g;
			$line =~ s/\*//g;
			push(@need_sign_off, $line);
			$cnt_sign_off++;
		}
	}
	close(FH);
	$cnt++;
}

foreach $ent (@obsid_list){

	$seq       = ${data.$ent}{seqnbr}[0];
	$target    = ${data.$ent}{name}[0];
	$grating   = ${data.$ent}{grating}[0];
	$inst      = ${data.$ent}{inst}[0];
	$mp_person = ${data.$ent}{mp_person}[0];

#
#--- find usint person who is in charge of this observation
#
	find_usint();

	%{mp_person.$ent} = (mp_person => ["$mp_person"],
			     usint     => ["$usint"]);
}


#
#--- sort the file, and remove duplicates
#

@sorted_obsid_list = sort{$a<=>$b} @obsid_list;
$first             = shift(@sorted_obsid_list);
@new_obsid_list    = ("$first");

OUTER:
foreach $ent(@sorted_obsid_list){
	foreach $comp (@new_obsid_list){
		if($ent =~ /$comp/){
			next OUTER;
		}
	}
	push(@new_obsid_list, $ent);
}


#
#--- print out the result
#

system("rm $obs_ss/scheduled_obs_list");
open(OUT,">$obs_ss/scheduled_obs_list");

foreach $ent (@new_obsid_list){
	print OUT "$ent\t${mp_person.$ent}{mp_person}[0]\n";
}
close(OUT);
system("chgrp mtagroup $obs_ss/scheduled_obs_list");

#
#---- read approved list
#

open(FH, "$ocat_dir/approved");
@app_obsid = ();
while(<FH>){
	chomp $_;
	@aptemp = split(/\s+/, $_);
	push(@app_obsid, $aptemp[0]);
}
close(FH);

#
#--- reverse the list so that the most recent approved obsid comes first
#

@rev_app_obsid = reverse (@app_obsid);

#
#---- read the past sign off request
#

@sign_off_obsid = ();
@sign_off_date  = ();

$test = `ls $obs_ss/*`;
if($test =~ /sign_off_request/){
	open(FH, "$obs_ss/sign_off_request");

OUTER:
	while(<FH>){
		chomp $_;
		@atemp = split(/\s+/, $_);
		push(@sign_off_obsid, $atemp[0]);
		push(@sign_off_date,  $atemp[1]);
	}
	close(FH);
	
	system("rm $obs_ss/sign_off_request");
}

#
#--- read split obsid list which we do not need to sign-off
#

#split_obsid_list_check();   #---- MAIL DIRECTOY IS NOT UPDATED ANY MORE (MAY 2015)


#
#--- if there are observations not signed off, send a email to USINT  and warn
#


if($cnt_sign_off > 0){
	OUTER:
	foreach $ent (@need_sign_off){
		foreach $comp (@split_obsid_list){
			if($ent =~ /$comp/){
				next OUTER;
			}
		}

#
#--- if email for this obsid already sent in past, skip it.
#

		@atemp = split(/\s+/, $ent);
		$obsid = $atemp[1];

		if($obsid !~ /\d/){					#---- if obsid is not digit, something wrong. get out
			next OUTER;
		}
		$chk = 0;
#
#--- check whether the obsid is in approved list (it may be signed off after the
#--- mp list created)
#
		foreach $comp (@rev_app_obsid){
			if($obsid == $comp){
				next OUTER;
			}
		}
		foreach $comp (@sign_off_obsid){
			if($obsid == $comp){
				$l_time_chk = $sign_off_date[$chk];
				$diff = $today_in_sec - $l_time_chk;

#
#--- if the last sign off request was sent more than 7 days ago, resend the request.
#--- if it is still less than 7 days, keep the same date in the sign_off_request file.
#

				if($diff < 604800){
					open(OUT2, ">>$obs_ss/sign_off_request");
					print OUT2 "$obsid\t$l_time_chk\n";
					close(OUT2);
					next OUTER;
				}
			}
			$chk++;
		}

		open(OUT, "> $temp_dir/temp_email");

		print OUT "The following obsid is in an active OR list, but it is not signed off yet\n\n\n";
		print OUT "Seq #  Obsid     Target                    PI      Inst.  Grat Mode    \n";
		print OUT '-------------------------------------------------------------------------',"\n";

		print OUT "$ent\n\n\n";
		print OUT "If you have any quesitons about this email, please contact swolk\@cfa.harvard.edu.\n";

		close(OUT);

#
#--- if the sign off request is sent out today, add the obsid and the date in sign_off_request file
#
		open(OUT2, ">>$obs_ss/sign_off_request");
		print OUT2 "$obsid\t$today_in_sec\n";
		close(OUT2);
		system("chgrp mtagroup $obs_ss/sign_off_request");

		@btemp = split(/\s+/, $ent);
		$usint = ${mp_person.$btemp[1]}{usint}[0];
				

		if($usint_on =~ /test/){
			system("cat $temp_dir/temp_email | mailx -s \"Subject: Warning: Sign Off Needed for Obsid: $btemp[1] ($usint)\"  $test_email");
		}else{
			system("cat $temp_dir/temp_email | mailx -s \"Subject: Warning: Sign Off Needed for Obsid: $btemp[1]\"  $usint $test_email cus\@head.cfa.harvard.edu");
		}	

		system("rm $temp_dir/temp_email");
	}
}


###################################################################
### conv_month_num_to_chr: change month format to e.g. 1 to Jan ###
###################################################################

sub conv_month_num_to_chr{

        my ($temp_month, $cmonth);
        ($temp_month) = @_;

        if($temp_month == 1){
                $cmonth = "Jan";
        }elsif($temp_month == 2){
                $cmonth = "Feb";
        }elsif($temp_month == 3){
                $cmonth = "Mar";
        }elsif($temp_month == 4){
                $cmonth = "Apr";
        }elsif($temp_month == 5){
                $cmonth = "May";
        }elsif($temp_month == 6){
                $cmonth = "Jun";
        }elsif($temp_month == 7){
                $cmonth = "Jul";
        }elsif($temp_month == 8){
                $cmonth = "Aug";
        }elsif($temp_month == 9){
                $cmonth = "Sep";
        }elsif($temp_month == 10){
                $cmonth = "Oct";
        }elsif($temp_month == 11){
                $cmonth = "Nov";
        }elsif($temp_month == 12){
                $cmonth = "Dec";
        }
        return $cmonth;
}


###############################################################################
### find_usint: find an appropriate usint email address for a given obs.    ###
###############################################################################

sub find_usint {
	if($target =~ /CAL/i){
		$usint  = 'ldavid@cfa.harvard.edu';
	}elsif($grating =~ /LETG/i){
		$usint  = 'jdrake@cfa.harvard.edu bwargelin@cfa.harvard.edu';
	}elsif($grating =~ /HETG/i){
		$usint  = 'nss@space.mit.edu  hermanm@space.mit.edu';
	}elsif($inst    =~ /HRC/i){
		$usint  = 'juda@head.cfa.harvard.edu vkashyap@cfa.harvard.edu';
	}else{
		if($seq < 290000){
			$usint = 'swolk@cfa.harvard.edu';
		}elsif($seq > 300000 && $seq < 490000){
			$usint = 'nadams@cfa.harvard.edu';
		}elsif($seq > 500000 && $seq < 590000){
			$usint = 'plucinsk@head.cfa.harvard.edu';
		}elsif($seq > 600000 && $seq < 690000){
			$usint = 'jdepasquale@cfa.harvard.edu';
		}elsif($seq > 700000 && $seq < 790000){
			$usint = 'emk@head.cfa.harvard.edu';
		}elsif($seq > 800000 && $seq < 890000){
			$usint = 'maxim@head.cfa.harvard.edu';
		}elsif($seq > 900000 && $seq < 990000){
			$usint = 'das@head.cfa.harvard.edu';
		}
	}
}

##################################################################
### cnv_time_to_t1998: change time format to sec from 1998.1.1 ###
##################################################################

sub cnv_time_to_t1998{

#######################################################
#       Input   $year: year
#               $ydate: date from Jan 1
#               $hour:$min:$sec:
#
#       Output  $t1998<--- returned
#######################################################

        my($totyday, $totyday, $ttday, $t1998);
        my($year, $ydate, $hour, $min, $sec);
        ($year, $ydate, $hour, $min, $sec) = @_;

        $totyday = 365*($year - 1998);
        if($year > 2000){
                $totyday++;
        }
        if($year > 2004){
                $totyday++;
        }
        if($year > 2008){
                $totyday++;
        }
        if($year > 2012){
                $totyday++;
        }

        $ttday = $totyday + $ydate - 1;
        $t1998 = 86400 * $ttday  + 3600 * $hour + 60 * $min +  $sec;

        return $t1998;
}

###############################################################################
### split_obsid_list_check: extract split obsid from mail and make a table  ###
###############################################################################

sub split_obsid_list_check{

	$in_list = `ls /data/mta4/CUS/www/MAIL/0*html`;

	@split_obsid_list = ();
	
	@list = split(/\s+/, $in_list);
	
	open(OUT, "> $obs_ss/no_sign_off_list");
	foreach $file (@list){
		$text = `cat $file`;
		if($text =~ /was split into/){
			if($text =~ /No signoff needed/){
				open(FH, "$file");
				@obsid_list = ();
				$cnt        = 0;
				$chk        = 0;
				OUTER:
				while(<FH>){
					chomp $_;
					if($_ =~ /ObsId  SeqNbr  Time/){
						$chk = 1;
					}
					if($chk == 0){
						next OUTER;
					}
					@atemp = split(/\s+/, $_);
					if($atemp[0] =~ /----/){
						next OUTER;
					}
					if($atemp[0] =~ /\d/){
						if($atemp[1] =~ /\d/){
							if($atemp[2] =~ /\d/){
								push(@obsid_list, $atemp[0]);
								$cnt++;
							}
						}
					}
				}
				close(FH);
	
				for($i = 1; $i < $cnt; $i++){
					push(@split_obsid_list, $obsid_list[$i]);
				}
			}
		}
	}
	close(OUT);
	system("chgrp mtagroup $obs_ss/no_sign_off_list");

}

######################################################################################
### is_dir_empty: check whether the directry is empty                              ###
######################################################################################

sub is_dir_empty{

    my ($path) = @_;
    opendir(DIR, $path);

    if(scalar(grep( !/^\.\.?$/, readdir(DIR)) == 0)) {
        closedir DIR;
        return 0;                           #---- yes the directory is empty
    }else{
        closedir DIR;
        return 1;                           #---- no the directory is not empty
    }
}

######################################################################################
### is_file_exist: check whether file with a pattern exist                         ###
######################################################################################

sub is_file_exist{


    my ($path, $pattern) = @_;

    $cout = 0;
    $chk  = is_dir_empty($path);
    if($chk == 1){
        system("ls $path/* > ./ztemp");
        open(FTIN, "./ztemp");

        while(<FTIN>){
            chomp $_;
            if($_ =~ /$pattern/){
                $cout = 1;
                last;
            }
        }
        close(FTIN);
        system("rm ./ztemp");
    }
    return $cout;
}

######################################################################################
### get_file_list: find files with a given pattern in the given directory         ####
######################################################################################

sub get_file_list{


    my ($path, $pattern) = @_;

    @out = ();
    $chk = is_file_exist($path, $pattern);
    if($chk == 1){
        system("ls $path/* > ./ztemp");
        open(FTIN, "./ztemp");
        while(<FTIN>){
            chomp $_;
            if($_ =~ /$pattern/){
                push(@out, $_);
            }
        }
        close(FTIN);
        system("rm ./ztemp");
    }
    return @out;
}
