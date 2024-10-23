#!/usr/bin/perl

#
#---- extract poc of past ddt/too observations and make prop no <---> poc table
#
#
open(FH, '/data/mta4/CUS/www/Usint/ocat/approved');
@a_list   = ();
@poc_list = ();
$total    = 0;
while(<FH>){
    chomp $_;
    @atemp = split(/\s+/, $_);
    push(@a_list, $atemp[0]);
    push(@poc_list, $atemp[2]);
    $total++;
}
close(FH);

open(FH, '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/tooddt_prop_obsid_list');
@prop_list = ();
while(<FH>){
    chomp $_;
    @atemp = split('<>', $_);
    $prop_no = $atemp[0];
    push(@prop_list, $prop_no);
    $prop_dict{$prop_no} = 'TBD';
    @btemp = split(':', $atemp[1]);
    $chk = 0;
    foreach $ent (@btemp){
        for($k = 0; $k< $total;$k++){
            if($a_list[$k] eq $ent){
                $prop_dict{$prop_no} = $poc_list[$k];
            }
        }
    }
}
close(FH); 

foreach $ent (@prop_list){
    print "$ent<>$prop_dict{$ent}\n";
}
