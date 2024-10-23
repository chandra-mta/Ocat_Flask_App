#!/usr/bin/perl

#
#---- extract poc of past ddt/too observations and make prop no <---> poc table
#
#
open(FH, '/data/mta4/CUS/www/Usint/ocat/approved');
@a_list   = ();
@poc_list = {};
$total    = 0;
while(<FH>){
    chomp $_;
    @atemp = split(/\s+/, $_);
    $poc = $atemp[2];
    if($poc eq 'nss'){$poc = 'hetg';}
    if($poc eq 'hermanm'){$poc = 'hetg';}
    if($poc eq 'jdrake'){$poc = 'letg';}
    if($poc eq 'zhao'){$poc = 'ping';}
    if($poc eq 'swolk'){$poc = 'sjw';}

    $poc_list{$atemp[0]} = $poc;
}
close(FH);

open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/new_obs_list');
#open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/too_list');
#open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/ddt_list');
@prop_list = ();
open(OUT, "> zout");
while(<FH>){
    chomp $_;
    @atemp = split(/\s+/, $_);
    if($atemp[0] eq 'ddt' || $atemp[0] eq 'too'){
        if($atemp[3] eq 'unobserved'){
#        if($atemp[3] eq 'scheduled'){
            print OUT "$_\n";
        }
    }
}
close(FH); 
