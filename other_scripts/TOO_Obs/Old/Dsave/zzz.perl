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

#open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/new_obs_list');
#open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/too_list');
#open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/ddt_list');
open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/obs_in_30days');
@prop_list = ();
open(OUT, "> zout");
while(<FH>){
    chomp $_;
    @atemp = split(/\s+/, $_);
    if($atemp[0] eq 'ddt' || $atemp[0] eq 'too'){
        $obsid = $atemp[2];
        $apoc  = $poc_list{$obsid};
        print "$apoc <--->$atemp[4]\n";
        if($apoc eq ''){
            print OUT "$_";
            print OUT "\n";
            next;
        }
        $poc   = $atemp[4];
        if($poc eq $apoc){
            print OUT "$_";
            print OUT "\n";
        }else{
            $line = $_;
            $line =~ s/$poc/$apoc/g;
            print OUT "$line\n";    
        }
    }else{
        print OUT "$_";
        print OUT "\n";
    }
}
close(FH); 
