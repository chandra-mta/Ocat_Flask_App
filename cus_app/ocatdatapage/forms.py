#################################################################################################
#                                                                                               #
#           forms.py: flask forms for Ocat Data Page                                            #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Sep 01, 2021                                                        #
#                                                                                               #
#################################################################################################

import sys
import os
import time

from flask              import request
from flask_wtf          import FlaskForm
from wtforms            import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length

import cus_app.supple.ocat_common_functions     as ocf

maxno  = 30       #---- max length of acceptable text length of char field
maxsp  = 10       #---- max size of the standard text area of char field 
maxsp1 = 15       #---- max size of the long text area of char field
maxsp2 = 8        #---- max size of the short text area of char field

#-----------------------------------------------------------------------------------------------
#-- pr_chr_field: CharField with variable text area size                                     ---
#-----------------------------------------------------------------------------------------------

def pr_chr_field(label, mxsp=maxsp):
    """
    change the size of CharField
    input:  label   --- the name of the field
    ouput:  CharField
    """
    return  StringField(label)

#-----------------------------------------------------------------------------------------------
#-- OcatParamForm: define form entry of parameters                                            --
#-----------------------------------------------------------------------------------------------

class OcatParamForm(FlaskForm):

#
#---- choices of pulldown fields. 
#
    choice_npy  = (('NA', 'NA'), ('N', 'NO'), ('P','PREFERENCE'), ('Y','YES'),)
    choice_ny   = (('N','NO'), ('Y','YES'),)
    choice_nny  = (('NA', 'NA'), ('N', 'NO'), ('Y', 'YES'),)
    choice_cp   = (('Y','CONSTRAINT'),('P','PREFERENCE'),)
    choice_nncp = (('NA','NA'),('N','NO'), ('P','PREFERENCE'), ('Y', 'CONSTRAINT'),)


#----  general parameters      -----------------------------------------------------------------


    label        = 'obsid'
    obsid        = pr_chr_field(label)

    label        = 'si_mode'
    si_mode      = pr_chr_field(label)

    label        = 'instrument'
    choice       = ('ACIS-I', 'ACIS-S', 'HRC-I', 'HRC-S')
    instrument   = SelectField(label=label, choices=[(x, x) for x in choice], default ="ACIS-I")

    label        = 'grating'
    choice       = ('NONE', 'LETG', 'HETG')
    grating      = SelectField(label=label, choices=[(x, x) for x in choice])

    label        = 'type'
    choice       = ('GO', 'TOO', 'GTO', 'CAL', 'DDT', 'CAL_ER', 'ARCHIVE', 'CDFS', 'CLP')
    type         = SelectField(label=label, choices=[(x, x) for x in choice])

    label        = 'targname'
    targname     = pr_chr_field(label,  mxsp=maxsp1)

    label        = 'ra'
    ra           = pr_chr_field(label,  mxsp=maxsp1)

    label        = 'dec'
    dec          = pr_chr_field(label,  mxsp=maxsp1)

    label        = 'y_det_offset'
    y_det_offset = pr_chr_field(label)

    label        = 'z_det_offset'
    z_det_offset = pr_chr_field(label)

    label        = 'trans_offset'
    trans_offset = pr_chr_field(label)

    label        = 'focus_offset'
    focus_offset = pr_chr_field(label)

    label        = 'uninterrupt'
    uninterrupt  = SelectField(label=label,  choices = choice_npy,)

    label        = 'extended_src'
    extended_src = SelectField(label=label,  choices = choice_ny,)

    label        = 'obj_flag'
    choice       = ('NO', 'MT', 'SS')
    obj_flag     = SelectField(label=label, choices=[(x, x) for x in choice])

    label        = 'object'
    choice       = ('NONE', 'NEW', 'COMET', 'EARTH', 'JUPITER', 'MARS',\
                    'MOON', 'NEPTUNE', 'PLUTO', 'SATURN', 'URANUS', 'VENUS')
    object       = SelectField(label=label, choices=[(x, x) for x in choice])

    label        = 'photometry_flag'
    photometry_flag = SelectField(label=label,  choices = choice_nny,)

    label        = 'vmagnitude'
    vmagnitude   = pr_chr_field(label)

    label        = 'est_cnt_rate'
    est_cnt_rate = pr_chr_field(label)

    label        = 'forder_cnt_rate'
    forder_cnt_rate  = pr_chr_field(label)

#----  Dither Parameters       -----------------------------------------------------------------

    label        = 'dither_flag'
    dither_flag  = SelectField(label=label,  choices = choice_nny,)

    label        = 'y_amp_asec'
    y_amp_asec   = pr_chr_field(label)

    label        = 'y_freq_asec'
    y_freq_asec  = pr_chr_field(label)

    label        = 'z_amp_asec'
    z_amp_asec   = pr_chr_field(label)

    label        = 'z_freq_asec'
    z_freq_asec  = pr_chr_field(label)

    label        = 'y_phase'
    y_phase      = pr_chr_field(label)

    label        = 'z_phase'
    z_phase      = pr_chr_field(label)


#---- Time Constraints         -----------------------------------------------------------------

    label        = 'window_flag'
    window_flag  = SelectField(label=label,  choices = choice_ny,)
#
#--- set lists of yeas, month, and date for pulldown menus
#
    year         = ocf.set_year_list(chk=1)
    month        = ('NUll', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    date         = []
    for i in range(1, 32):
        date.append(ocf.add_leading_zero(i, 2))

    for i in range(1, 10):
        label = 'window_constraint' + str(i)
        exec("%s = SelectField(label='%s',  choices = choice_nncp,)" % (label, label))

        label = 'tstart_month' + str(i)
        exec("%s = SelectField(label='%s', choices=[(x, x) for x in month])"  % (label, label))

        label = 'tstart_date' + str(i)
        exec("%s = SelectField(label='%s', validators=[DataRequired()], choices=[(x, x) for x in date])"   % (label, label))

        label = 'tstart_year' + str(i)
        exec("%s = SelectField(label='%s', choices=[(x, x) for x in year])"   % (label, label))

        label = 'tstart_time' + str(i)
        exec("%s = pr_chr_field('%s')" % (label, label))

    
        label = 'tstop_month' + str(i)
        exec("%s = SelectField(label='%s', choices=[(x, x) for x in month])"  % (label, label))

        label = 'tstop_date' + str(i)
        exec("%s = SelectField(label='%s', validators=[DataRequired()], choices=[(x, x) for x in date])"   % (label, label))

        label = 'tstop_year' + str(i)
        exec("%s = SelectField(label='%s', choices=[(x, x) for x in year])"   % (label, label))

        label = 'tstop_time' + str(i)
        exec("%s = pr_chr_field('%s')" % (label, label))


#---- Roll Constraints        ------------------------------------------------------------------

    label        = 'roll_flag'
    roll_flag  = SelectField(label=label,  choices = choice_ny, )

    for i in range(1, 10):
        label = 'roll_constraint' + str(i)
        exec("%s = SelectField(label='%s',  choices = choice_nncp,)" % (label, label))

        label = 'roll_180' + str(i)
        exec("%s = SelectField(label='%s',  choices = choice_nny,)" % (label, label))

        label = 'roll' + str(i)
        exec("%s = pr_chr_field('%s')" % (label, label))

        label = 'roll_tolerance' + str(i)
        exec("%s = pr_chr_field('%s')" % (label, label))

#---- Other Constraints   ----------------------------------------------------------------------

    label        = 'constr_in_remarks'
    constr_in_remarks = SelectField(label=label, choices = choice_npy,)

    label        = 'phase_constraint_flag'
    phase_constraint_flag = SelectField(label=label,  choices = choice_nncp,)

    label        = 'phase_epoch'
    phase_epoch  = pr_chr_field(label)

    label        = 'phase_period'
    phase_period = pr_chr_field(label)

    label        = 'phase_startd'
    phase_startd = pr_chr_field(label)

    label        = 'phase_start_margin'
    phase_start_margin = pr_chr_field(label)

    label        = 'phase_end'
    phase_end    = pr_chr_field(label)

    label        = 'phase_end_margin'
    phase_end_margin = pr_chr_field(label)

    label        = 'monitor_flag'
    monitor_flag = SelectField(label=label,  choices = choice_ny,)

    label        = 'monitoring_observation'
    monitoring_observation = SelectField(label=label,  choices = choice_nny,)

    label        = 'pre_id'
    pre_id       = pr_chr_field(label)

    label        = 'pre_min_lead'
    pre_min_lead = pr_chr_field(label)

    label        = 'pre_max_lead'
    pre_max_lead = pr_chr_field(label)

    label        = 'multitelescope'
    multitelescope = SelectField(label=label,  choices = choice_npy,)

    label        = 'observatories'
    observatories = pr_chr_field(label)

    label        = 'multitelescope_interval'
    multitelescope_interval = pr_chr_field(label)



#---- HRC Parameters       ----------------------------------------------------------------------

    label           = 'hrc_timing_mode'
    hrc_timing_mode = SelectField(label=label,  choices = choice_ny,)

    label           = 'hrc_zero_block'
    hrc_zero_block  = SelectField(label=label,  choices = choice_ny,)

    label           = 'hrc_si_mode'
    hrc_si_mode     = pr_chr_field(label)

#--- ACIS Parameters       ---------------------------------------------------------------------

    label        = 'exp_mode'
    choice       =  ('NULL', 'TE', 'CC')
    exp_mode     = SelectField(label=label, choices=[(x, x) for x in choice])

    label        = 'bep_pack'
    choice       =  ('NULL', 'F', 'VF', 'F+B', 'G')
    bep_pack     = SelectField(label=label, choices=[(x, x) for x in choice])

    label        = 'frame_time'
    frame_time   = pr_chr_field(label)

    label        = 'most_efficient'
    most_efficient = SelectField(label=label,  choices = choice_nny,)

    choice       =  (('NULL', 'NULL'), ('N','NO'), ('Y','YES'), ('O1','OPT1'),\
                     ('O2','OPT2'), ('O3', 'OPT3'), ('O4','OPT4'), ('O5','OPT5'),)

    label        = 'ccdi0_on'
    ccdi0_on     = SelectField(label=label, choices = choice,)

    label        = 'ccdi1_on'
    ccdi1_on     = SelectField(label=label, choices = choice,)

    label        = 'ccdi2_on'
    ccdi2_on     = SelectField(label=label, choices = choice,)

    label        = 'ccdi3_on'
    ccdi3_on     = SelectField(label=label, choices = choice,)

    label        = 'ccds0_on'
    ccds0_on     = SelectField(label=label, choices = choice,)

    label        = 'ccds1_on'
    ccds1_on     = SelectField(label=label, choices = choice,)

    label        = 'ccds2_on'
    ccds2_on     = SelectField(label=label, choices = choice,)

    label        = 'ccds3_on'
    ccds3_on     = SelectField(label=label, choices = choice,)

    label        = 'ccds4_on'
    ccds4_on     = SelectField(label=label, choices = choice,)

    label        = 'ccds5_on'
    ccds5_on     = SelectField(label=label, choices = choice,)

    choice = (('NONE', 'NONE'), ('N', 'NO'), ('CUSTOM', 'YES'),)
    label        = 'subarray'
    subarray     = SelectField(label=label,  choices = choice,)

    label        = 'subarray_start_row'
    subarray_start_row = pr_chr_field(label)

    label        = 'subarray_row_count'
    subarray_row_count = pr_chr_field(label)

    label        = 'duty_cycle'
    duty_cycle   = SelectField(label=label,  choices = choice_nny,)

    label        = 'secondary_exp_count'
    secondary_exp_count = pr_chr_field(label)

    label        = 'primary_exp_time'
    primary_exp_time = pr_chr_field(label)

    label        = 'onchip_sum'
    onchip_sum   = SelectField(label=label,  choices = choice_nny,)

    label        = 'onchip_row_count'
    onchip_row_count = pr_chr_field(label)

    label        = 'onchip_column_count'
    onchip_column_count = pr_chr_field(label)

    label        = 'eventfilter'
    eventfilter  = SelectField(label=label,  choices = choice_nny,)

    label        = 'eventfilter_lower'
    eventfilter_lower = pr_chr_field(label)

    label        = 'eventfilter_higher'
    eventfilter_higher = pr_chr_field(label)

    label        = 'multiple_spectral_lines'
    multiple_spectral_lines = SelectField(label=label,  choices = choice_nny,)

    label        = 'spectra_max_count'
    spectra_max_count = pr_chr_field(label)

#---- ACIS Window Constraints      --------------------------------------------------------------

    label         = 'spwindow_flag'
    spwindow_flag = SelectField(label=label,  choices = choice_nny,)

    choice   =  ('NULL','I0', 'I1',  'I2', 'I3', 'S0', 'S1', 'S2', 'S3', 'S4', 'S5')

    for i in range(1, 10):
        label    = 'chip' + str(i)
        exec("%s = SelectField(label='%s', choices=[(x, x) for x in choice])"  % (label, label))

        label = 'start_row' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

        label = 'start_column' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

        label = 'height' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

        label = 'width' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

        label = 'lower_threshold' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

        label = 'pha_range' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

        label = 'sample' + str(i)
        exec("%s = pr_chr_field('%s', mxsp=%s)" % (label, label,  maxsp2))

#---- Text Fields     --------------------------------------------------------------------------

    remarks     = TextAreaField('remarks')
    comments    = TextAreaField('comments')
    multi_obsid = TextAreaField('multi_obsid')


#---- Submit Form    ---------------------------------------------------------------------------


    submit = SubmitField('Submit')

