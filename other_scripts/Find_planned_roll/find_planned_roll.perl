#!/usr/bin/perl
######use LWP::Simple;

#########################################################################################
#											#
# find_planned_roll: this script read MP long term web page and extract obsid and 	#
#		     planned roll angle.						#
#											#
#	Author: T. Isobe (isobe@head.cfa.harvard.edu)					#
#	Last Update: Aug 26, 2014							#
#											#
#########################################################################################


#
#---- set directory paths : updated to read from a file (02/25/2011) --- this is user:mta version
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

find_planned_roll();

###############################################################################
### find_planned_roll: extreact roll angle from the mp web site             ###
###############################################################################

sub find_planned_roll{

#
#--- following two won't work with a secure web site (03/07/2011)
#
#	system("/opt/local/bin/lynx -source http://hea-www.harvard.edu/asclocal/mp/lts/lts-current.html > $temp_dir/ztemp_mp");
#	getstore("https://icxc.harvard.edu/mp/lts/lts-current.html", "$temp_dir/ztemp_mp");
#	open(PFH, "$temp_dir/ztemp_mp");
#
	open(PFH, " /proj/web-icxc/htdocs/mp/lts/lts-current.html");
	open(POUT,">$obs_ss/mp_long_term");
	OUTER:
	while(<PFH>){
		chomp $_;
		if($_ =~ / LTS changes/){
			last OUTER;			# after this line, the table listed a different information
		}
		if($_ =~ /target.cgi/){
			@atemp = split(/target_param\.cgi\?/,$_);
			@btemp = split(/\"/, $atemp[1]);
			@ctemp = split(//, $btemp[0]);
			$cnt   = 0;
			foreach (@ctemp){
				$cnt++;
			}
			$obsid = '';			# adujsting obsid (removing a leading '0')
			if($ctemp[0] == 0){
				for($i = 1; $i < $cnt; $i++){
					$obsid = "$obsid"."$ctemp[$i]";
				}
			}else{
				$obsid = $btemp[0];
			}

			@atemp   = split(/\s+/, $_);
			$ent_cnt = 0;
			OUTER2:
			foreach $ent (@atemp){
				if($ent =~ /ACIS/ || $ent =~/HRC/){
					last OUTER2;
				}else{
					$ent_cnt++;
				}
			}
			$planned_roll_pos = $ent_cnt - 4;   #--- column position change: 08/26/14
			$pl_roll          = $atemp[$planned_roll_pos];

			print POUT "$obsid:$pl_roll\n";
		}
	}
	close(PFH);
	close(POUT);

#	system("rm $temp_dir/ztemp_mp");
}
