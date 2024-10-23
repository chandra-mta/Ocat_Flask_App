#!/usr/bin/perl

#########################################################################
# R. Kilgard, Feb 29, 2000
# This is a script to parse the updates log and nag (via email)
# people who haven't signed off changes they requested
#
# Updated Oct 8, 2003 T. Isobe (tisobe@cfa.harvard.edu)
# 	send is changed to mailx
#	added si specific email
# Updated Jul 2, 2008  to adjust to a new directory
#       /data/mta4/CUS/www/Usint
# if you move to the other directory, you need to change the hard
# coded path accordingly.
#
# Updated Sep 29, 2008 si mode notice over the weekend is now
# separated to acis and hrc. A different person gets email.
#
# Changing directry structure Mar 01, 2011
# modify mailx option   Sep 05, 2012
# modify mailx option   Oct 08, 2012 (same as above)
# path to the data changed Mar 26, 2013
# temp path bug fixed
# hrc mail address juda --> kashyap   Jan 03, 2017
# hrc mail dpatnaude added Mar 22, 2017
# hrc mail address changed to hrcdude Sep 13, 2018
# weekly nagging date increased twice (sun/wed) Jun 13, 2019
# http: --> https:  Sep 05, 2019
#
#########################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011)	this is user: cus version
#

#open(IN, '/data/udoc1/ocat/Info_save/dir_list');
#open(IN, '/proj/web-cxc-dmz/htdocs/mta/CUS/Usint/ocat/Info_save/dir_list');
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

#
#--- get the contents of the logfile
#

open (FILE, "<$ocat_dir/updates_table.list");
@revisions = <FILE>;
close (FILE);

#
#---- find who are usint users
#

open(FH, "$pass_dir/usint_users");
@usint_user_list = ();
while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	push(@usint_user_list, $atemp[0]);
}
close(FH);

#
#--- get some useful stuff
#

$na   = "NA";
$date = `/bin/date '+%a'`;
$sun  = "Sun";
$wed  = "Wed";
chop $date;

#
#--- if it's Sunday, run the weekly nag subroutine
#

if (($date eq $sun) || ($date eq $wed)){
    	@revs = @revisions;
    	&nag_updaters (@revs);
}

#
#--- foreach line, find the ones which haven't been verified and load up
#--- some arrays

foreach $line (@revisions){
    	chop $line;
    	@values         = split ("\t", $line);
    	$obsrev         = $values[0];
    	$general_status = $values[1];
    	$acis_status    = $values[2];
    	$si_mode_status = $values[3];
    	$dutysci_status = $values[4];
    	$seqnum         = $values[5];
    	$user           = $values[6];
#
#---- sending email to only obsids signed off less than 72 hrs
#
#	$ttemp = `/bin/date '+%m/%d/%y'`;
#	conv_time();
#	$ctime = $day2000;
#
#	@atemp = split(/\s+/, $general_status);
#	$ttemp = $atemp[1];
#	if($ttemp =~ /N/i){
#		$gdff = 10;
#	}else{
#		conv_time();
#		$gdiff = $ctime - $day2000;
#	}
#	
#	@atemp = split(/\s+/, $acis_status);
#	$ttemp = $atemp[1];
#	if($ttemp =~ /N/i){
#		$adiff = 10;
#	}else{
#		conv_time();
#		$adiff = $ctime - $day2000;
#	}
#	
#	@atemp = split(/\s+/, $si_mode_status);
#	$ttemp = $atemp[1];
#	if($ttemp =~ /N/i){
#		$sdiff = 10;
#	}else{
#		conv_time();
#		$sdiff = $ctime - $day2000;
#	}
#
#		
#	if($gdiff < 3 || $adiff < 3 || $sdiff < 3){

#
#--- only when three fields are all filled, the notificaiton will be sent out
#

    		unless (($general_status eq $na) || ($acis_status eq $na) || ($si_mode_status eq $na) ){
			if ($dutysci_status eq $na){
	    			$updates{$obsrev} = $user;
	    			push(@usernag, $user);
	    			push(@obsnag,  $obsrev);
			}
    		}
#	}
}

#
#---- smush the array of users - sort and remove duplicates
#

@smuser = (sort @usernag);
$k = 0;
foreach $foo (@obsnag){
    	if ($smuser[$k] eq $smuser[($k+1)]){
		splice(@smuser, $k+1, 1);
    	} else {
		$k++;
    	}
}

#
#---- foreach person on the short list
#

foreach $ruser (@smuser){
	$usint_person = 'no';
	OUTER:
	foreach $comp (@usint_user_list){
		if($ruser eq $comp){
			$usint_person = 'yes';
			last OUTER;
		}
	}
	if($usint_person eq 'yes'){
#
#---- reset the tmp array
#
    		@tmp = ();

#
#---- pack the tmp array with the obsid.revs for which they are responsible
#
    		foreach $obsrnag (@obsnag){
			if ($updates{$obsrnag} eq $ruser){
	    			push(@tmp, $obsrnag);
			}
    		}

#
#---- create a tmp mailfile with the list of obsid.revs for that person
#
    		open (MFILE, ">$temp_dir/$ruser.tmp");
    		print MFILE "All requested edits have been made for the following obsid.revs:\n\n";
    		foreach $foo (@tmp){
			print MFILE "$foo\n";
    		}
    		print MFILE "\nPlease sign off these requests at this url:\n\n";
    		print MFILE "https://icxc.harvard.edu/cgi-bin/usg/orupdate.cgi\n";
    		print MFILE "\nThis message is generated by a cron job, so no reply is necessary.\n";
    		close MFILE;
		
#
#--- give the people what they want
#
####		system("cat $temp_dir/$ruser.tmp| mailx -s \"Subject: Verification needed for obsid.revs --- $ruser\" isobe\@head.cfa.harvard.edu");

	system("cat $temp_dir/$ruser.tmp| mailx -s \"Subject: Verification needed for obsid.revs\" -c  cus\@head.cfa.harvard.edu  -b isobe\@head.cfa.harvard.edu  $ruser\@head.cfa.harvard.edu");
		system("rm $temp_dir/$ruser.tmp");
    		`/usr/bin/sleep 5`;
	}
}

exit(0);

######################################################################
#### nag_updaters: run the weekly nag script			######
######################################################################

sub nag_updaters {
    	local (@revs) = @_;

    	$nna      = "NA";
	@nag_gen  = ();
	@nag_acis = ();
	@nag_si   = ();
	@nag_si_a = ();
	@nag_si_h = ();

	$chk_gen  = 0;
	$chk_acis = 0;
	$chk_si   = 0;
	$chk_si_a = 0;
	$chk_si_n = 0;
#
#--- foreach update
#
    	foreach $nline (@revs){
		chop $nline;
		@nvalues         = split ("\t", $nline);
		$nobsrev         = $nvalues[0];
		$ngeneral_status = $nvalues[1];
		$nacis_status    = $nvalues[2];
		$nsi_mode_status = $nvalues[3];
		$ndutysci_status = $nvalues[4];
		$nseqnum         = $nvalues[5];
		$nuser           = $nvalues[6];
#
#---- if there are general/acis changes to be made, load some arrays	
#
		if (($ngeneral_status eq $nna) && ($ndutysci_status eq $nna)){
	    		push(@nag_gen, $nobsrev);
			$chk_gen++;
		}
		if (($nacis_status eq $nna) && ($ndutysci_status eq $nna)){
	    		push(@nag_acis, $nobsrev);
			$chk_aics++;
		}
		if (($nsi_mode_status eq $nna) && ($ndutysci_status eq $nna)){
	    		push(@nag_si, $nobsrev);
			@btemp = split(/\./, $nobsrev);
			$chk_si++;
			$obsid = $btemp[0];
			find_inst();
			if($cinst eq 'acis'){
				push(@nag_si_a, $nobsrev);
				$chk_si_a++;
			}elsif($cinst eq 'hrc'){
				push(@nag_si_h, $nobsrev);
				$chk_si_h++;
			}
		}
    	}
#
#---- compose the general nag email
#
	if($chk_gen > 0){
    		open (NFILE, ">$temp_dir/gennag.tmp");
    		print NFILE "This message is a weekly summary of obsid.revs which\nneed general (non-ACIS) changes:\n\n";
    		foreach $nag (@nag_gen){
			print NFILE "$nag\n";
    		}
    		print NFILE "\nThese updates may be verified at the following URL:\n\n";
    		print NFILE "https://icxc.harvard.edu/cgi-bin/usg/orupdate.cgi\n";
	
    		close NFILE;
#
#--- send the general nag email
#
		system("cat $temp_dir/gennag.tmp|mailx -s \"Subject: Updates needed for obsid.revs\n\" -c cus\@head.cfa.harvard.edu -b isobe\@head.cfa.harvard.edu brad\@head.cfa.harvard.edu  wink\@head.cfa.harvard.edu,arots\@head.cfa.harvard.edu,mccolml\@head.cfa.harvard.edu");
		system("rm $temp_dir/gennag.tmp");
	}

#
#---- compose the acis nag email
#
	if($chk_acis > 0){
    		open (NFILE1, ">$temp_dir/acisnag.tmp");
    		print NFILE1 "This message is a weekly summary of obsid.revs which\nneed ACIS-specific changes:\n\n";
    		foreach $nag1 (@nag_acis){
			print NFILE1 "$nag1\n";
    		}
    		print NFILE1 "\nThese updates may be verified at the following URL:\n\n";
    		print NFILE1 "https://icxc.harvard.edu/cgi-bin/usg/orupdate.cgi\n";
		
    		close NFILE1;
	
#
#--- send the acis nag email
#
		system("cat $temp_dir/acisnag.tmp|mailx -s \"Subject: Updates needed for obsid.revs\n\" -c cus\@head.cfa.harvard.edu -b isobe\@head.cfa.harvard.edu brad\@head.cfa.harvard.edu  arots\@head.cfa.harvard.edu");
		system("rm $temp_dir/acisnag.tmp");
	}

#
#---- compose the si nag email
#

	if($chk_si > 0){
    		open (NFILE1, ">$temp_dir/sinag.tmp");
    		print NFILE1 "This message is a weekly summary of obsid.revs which\nneed SI-specific changes:\n\n";
    		foreach $nag1 (@nag_si){
			print NFILE1 "$nag1\n";
    		}
    		print NFILE1 "\nThese updates may be verified at the following URL:\n\n";
    		print NFILE1 "https://icxc.harvard.edu/cgi-bin/usg/orupdate.cgi\n";
		
    		close NFILE1;
	
#
#--- send the si nag email
#
#		system("cat $temp_dir/sinag.tmp|mailx -s \"Subject: Updates needed for obsid.revs\n\" acisdude\@head.cfa.harvard.edu,juda\@head.cfa.harvard.edu");

		system("rm $temp_dir/sinag.tmp");
	}

#
#---si change for acis
#
	if($chk_si_a > 0){
    		open (NFILE1, ">$temp_dir/sinag.tmp");
    		print NFILE1 "This message is a weekly summary of obsid.revs which\nneed SI-specific changes:\n\n";
    		foreach $nag1 (@nag_si_a){
			print NFILE1 "$nag1\n";
    		}
    		print NFILE1 "\nThese updates may be verified at the following URL:\n\n";
    		print NFILE1 "https://icxc.harvard.edu/cgi-bin/usg/orupdate.cgi\n";
		
    		close NFILE1;
	
#
#--- send the acis si nag email
#
		system("cat $temp_dir/sinag.tmp|mailx -s \"Subject: Updates needed for obsid.revs\n\" -c cus\@head.cfa.harvard.edu -b isobe\@head.cfa.harvard.edu acisdude\@head.cfa.harvard.edu");

		system("rm $temp_dir/sinag.tmp");
	}

#
#---si change for hrc
#
	if($chk_si_h > 0){
    		open (NFILE1, ">$temp_dir/sinag.tmp");
    		print NFILE1 "This message is a weekly summary of obsid.revs which\nneed SI-specific changes:\n\n";
    		foreach $nag1 (@nag_si_h){
			print NFILE1 "$nag1\n";
    		}
    		print NFILE1 "\nThese updates may be verified at the following URL:\n\n";
    		print NFILE1 "https://icxc.harvard.edu/cgi-bin/usg/orupdate.cgi\n";
		
    		close NFILE1;
	
#
#--- send the  hrc si nag email
#
		system("cat $temp_dir/sinag.tmp|mailx -s \"Subject: Updates needed for obsid.revs\n\" -c cus\@head.cfa.harvard.edu -b isobe\@head.cfa.harvard.edu kashyap\@head.cfa.harvard.edu hrcdude\@cfa.harvard.edu");

		system("rm $temp_dir/sinag.tmp");
	}
}


###########################################################################
### conv_time: day from 2000.1.1                                        ###
###########################################################################

sub conv_time{
	@jtemp = split(/\//, $ttemp);
	$year = int ($jtemp[2]);
	if($year > 90){
		$year -= 100;
	}
	$add = 365 * $year;
	if($jtemp[0] == 2){
		$add += 31;
	}elsif($jtemp[0] == 3){
		$add += 59;
	}elsif($jtemp[0] == 4){
		$add += 90;
	}elsif($jtemp[0] == 5){
		$add += 120;
	}elsif($jtemp[0] == 6){
		$add += 151;
	}elsif($jtemp[0] == 7){
		$add += 181;
	}elsif($jtemp[0] == 8){
		$add += 212;
	}elsif($jtemp[0] == 9){
		$add += 243;
	}elsif($jtemp[0] == 10){
		$add += 273;
	}elsif($jtemp[0] == 11){
		$add += 304;
	}elsif($jtemp[0] == 12){
		$add += 334;
	}
        
	$chk == 4 * int(0.25 * $year);
	if($year == $chk){
		if($jtemp[0] > 2){
			$add++;
		}
	}
	$day2000 = $jtemp[1] + $add;
}


####################################################################################
####################################################################################
####################################################################################

sub find_inst {
	open(FH, "$obs_ss/sot_ocat.out");
	OUTER:
	while(<FH>){
        	chomp $_;
        	@atemp = split(/\s+/, $_);
        	if($atemp[1] == $obsid){
                	if($_ =~ /ACIS/){
                        	$cinst = 'acis';
                	}elsif($_ =~ /HRC/){
                        	$cinst = 'hrc';
                	}else{
                        	$cinst = 'others';
                	}
        	last OUTER;
        	}
	}
	close(FH);
}

