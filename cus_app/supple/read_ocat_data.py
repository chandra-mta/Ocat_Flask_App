"""
**read_ocat_data.py**: Extract parameter values for a given obsid.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 5, 2025

"""
import ska_dbi.sqsh as sqsh
import astropy.table
import astropy.io
import numpy as np
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
#
#--- Set sqsh Parameters
#
_SERV = 'ocatsqlsrv'
_USR = 'mtaops_internal_web'
_AUTHDIR = "/data/mta4/CUS/authorization"
_DB = 'axafocat'

#
# --- Parameter Lists
#
_GENERAL_PARAM_LIST = ['obsid', 'targid', 'seq_nbr', 'targname', 'obj_flag', 'object', 'si_mode', \
      'photometry_flag', 'vmagnitude', 'ra', 'dec', 'est_cnt_rate', 'forder_cnt_rate',\
      'y_det_offset', 'z_det_offset', 'raster_scan', 'dither_flag', 'approved_exposure_time', \
      'pre_min_lead', 'pre_max_lead', 'pre_id', 'seg_max_num', 'aca_mode', \
      'phase_constraint_flag', 'ocat_propid', 'acisid', 'hrcid', 'grating', 'instrument', \
      'rem_exp_time', 'soe_st_sched_date', 'type', 'lts_lt_plan', 'mpcat_star_fidlight_file',\
      'status', 'data_rights', 'tooid', 'description', 'total_fld_cnt_rate', 'extended_src',\
      'uninterrupt', 'multitelescope', 'observatories', 'tooid', 'constr_in_remarks', \
      'group_id', 'obs_ao_str', 'roll_flag', 'window_flag', 'spwindow_flag', \
      'multitelescope_interval', 'pointing_constraint', 'remarks', 'mp_remarks']

_ACIS_PARAM_LIST = ['exp_mode', 'ccdi0_on', 'ccdi1_on', 'ccdi2_on', 'ccdi3_on', 'ccds0_on', 'ccds1_on', \
        'ccds2_on', 'ccds3_on', 'ccds4_on', 'ccds5_on', 'bep_pack', 'onchip_sum', \
        'onchip_row_count', 'onchip_column_count', 'frame_time', 'subarray', 'subarray_start_row', \
        'subarray_row_count', 'duty_cycle', 'secondary_exp_count', 'primary_exp_time',\
        'eventfilter', 'eventfilter_lower', 'eventfilter_higher', 'most_efficient', \
        'dropped_chip_count', 'multiple_spectral_lines', 'spectra_max_count']

_ACISWIN_PARAM_LIST = ['ordr', 'aciswin_id', 'start_row', 'start_column', 'width', 'height',\
              'lower_threshold', 'pha_range', 'sample', 'chip', 'include_flag']

_NULL_LIST = ['NA', 'N/A', 'none','None', 'NONE', 'null', 'Null', 'NULL', ''] #: List of database null string values we intend to be python native None

def get_value_from_sybase(cmd):
    conn = sqsh.Sqsh(dbi='sybase', server=_SERV, database = _DB, user = _USR, authdir = _AUTHDIR)
    row = conn.fetchall(cmd)
    return row

def _convert_astropy_to_native(astropy_object, orient = None):
    """Converts an astropy object into python native objects.

    :param astropy_object: astropy object
    :type astropy_object: Table, Row, Column, ect.
    :param orient: Orientation of data Table conversion(uses pandas convention), defaults to None
    :type orient: str, optional
    """
    def _convert_row_to_dict(row):
        """convert an astropy table row into data formats expected by the application

        :param row: Sybase fetched astropy table row.
        :type row: Astropy.table.row.Row
        :returns: Formatted python dictionary
        :rtype: dict
        """
        row_dict = {col: row[col].tolist() for col in row.colnames}
        return row_dict
    
    if type(astropy_object) == astropy.table.table.Table:
        #
        # --- Multiple possible orientations.
        # --- Similar argument to pandas dataframe for consistency but does not use pandas
        # --- REVISIT:// 
        # --- If single row then return as row in list
        # --- If single column then return as dict with one column entry.
        #
        if (orient == 'records') or (len(astropy_object) == 1 and orient is None):
            result = []
            for row in astropy_object:
                result.append(_convert_row_to_dict(row))
            return result
        elif (orient == 'list') or (len(astropy_object.colnames) == 1 and orient is None):
            result = {}
            for col in astropy_object.colnames:
                result[col] = astropy_object[col].tolist()
            return result
        elif len(astropy_object) == 0:
            raise ValueError("Cannot convert empty astropy table.")
        else:
            raise ValueError(f"Provide object orient [records, list]. Provided orient: {orient}.")
            
    elif type(astropy_object) == astropy.table.row.Row:
        return _convert_row_to_dict(astropy_object)
    
    elif type(astropy_object) == astropy.table.column.Column:
        return astropy_object.tolist()
    
    elif hasattr(astropy_object, 'tolist'):
        return astropy_object.tolist()

def read_ocat_data(obsid):
    """
    extract parameter values for a given obsid
    
    :param obsid: obsid
    :type obsid: int
    :return: p_dict: a dictionary of <param name> <--> <param value>
    :rtype: dict

    :Note: there are severl parameter names  different from those in the database:
                TOO/DDT: 'type','trig','start','stop','followup','remarks']
                        will be with prefix 'too_'
                HRC SI Mode: si_mode will be hrc_si_mode to distingush from ACIS si_mode
                Joint Prop: 'prop_num', 'title', 'joint' will be:
                            'proposal_number', 'proposal_titile', 'proposal_joint'
                            see prop_params for others.
    """
    p_dict = general_params(obsid)
    
    p_dict.update(monitor_params(obsid, p_dict.get('pre_id'), p_dict.get('group_id')))
    #
    #--- Additional parameters dependent on observation type
    #
    if p_dict.get('tooid') is not None:
        p_dict.update(too_ddt_params(p_dict.get('tooid')))
        
    if p_dict.get('hrcid') is not None:
        p_dict.update(hrc_params(p_dict.get('hrcid')))
    
    if p_dict.get('acisid') is not None:
        p_dict.update(acis_params(p_dict.get('acisid')))
    #
    #--- Flag terminology varies across tables, but 'N' and None are consistently Null intended
    #--- Non-null flags range from 'Y', 'P'
    #
    if p_dict.get('roll_flag') not in ('N', None):
        p_dict.update(roll_params(obsid))
        
    if p_dict.get('window_flag') not in ('N', None):
        p_dict.update(time_constraint_params(obsid))
    
    if p_dict.get('spwindow_flag') not in ('N', None):
        p_dict.update(aciswin_params(obsid))
    
    if p_dict.get('phase_constraint_flag') not in ('N', None):
        p_dict.update(phase_params(obsid))
    
    if p_dict.get('dither_flag') not in ('N', None):
        p_dict.update(dither_params(obsid))
    
    #
    #--- Miscellaneous Information
    #
    p_dict.update(sim_params(obsid))
    
    p_dict.update(soe_params(obsid))
    
    p_dict.update(prop_params(p_dict.get('ocat_propid')))
    
    #
    # --- Assign the variety of tables different null values to python native None
    #
    for k,v in p_dict.items():
        if v in _NULL_LIST:
            p_dict[k] = None
    return p_dict

def general_params(obsid):
    """
    extract general parameter data 
    
    :param obsid: obsid
    :type obsid: int
    :return: p_dict: a dictionary of <param name> <--> <param value>
    :rtype: dict
    """
    cmd = f"select {','.join(_GENERAL_PARAM_LIST)} from target where obsid={obsid}"
    result = get_value_from_sybase(cmd)
    #
    # --- We expect a result so through No results found error if missing
    # --- consider using from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
    #
    if len(result) == 0:
        raise NoResultFound(f"No query result for {obsid}")
    elif len(result) >= 2:
        raise MultipleResultsFound(f"Multiple query result for {obsid}")
    else:
        p_dict = _convert_astropy_to_native(result[0])
        p_dict['comments'] = p_dict.pop('mp_remarks')
        return p_dict
    
def monitor_params(obsid, pre_id, group_id):
    """extract monitor flag related parameter data

    :param obsid: observation identifier
    :type obsid: int
    :param pre_id: previous obsid in a series convention
    :type pre_id: int
    :param group_id: name of group of associated observations
    :type group_id: str
    :return: dictionary of parameters
    :rtype: dict
    """

    p_dict = {}
    #
    # If there is a group ID, monitor_flag is N
    #
    p_dict['monitor_flag'] = 'N'
    if group_id is not None:
        #
        # --- Group actions
        #
        full_group = get_value_from_sybase(f"select obsid, status from target where group_id='{group_id}'")
        sel = np.isin(full_group['status'], ['unobserved', 'scheduled', 'untriggered'])
        p_dict['group_obsid'] = sorted(full_group[sel]['obsid'].tolist())
    else:
        #
        # --- Monitor Series Actions, involves overridding monitor_flag
        #
        if pre_id is not None:
            p_dict['monitor_flag'] = 'Y'
        else:
            check_if_start = get_value_from_sybase(f"select distinct pre_id, obsid from target where pre_id={obsid} or (obsid={obsid} and pre_id is not NULL)")
            if len(check_if_start) > 0: #: There are fetch results
                p_dict['monitor_flag'] = 'Y'
        
        if p_dict['monitor_flag'] == 'Y':
            p_dict['monitor_series'] = find_monitoring_series(obsid)
    return p_dict

def find_monitoring_series(obsid):
    """find all obsids associated with this monitoring series and then list the unobserved ones
    """
    def _reverse(obsid):
        cmd = f"select obsid, pre_id, status from target where obsid={obsid}"
        rev = get_value_from_sybase(cmd)
        val = rev[0]['pre_id'].tolist()
        while val is not None:
            cmd = f"select obsid, pre_id, status from target where obsid={val}"
            out = get_value_from_sybase(cmd)
            if len(out) == 0:
                break
            rev = astropy.table.vstack([out,rev])
            val = rev[0]['pre_id'].tolist()
        return rev
    
    def _forward(obsid):
        cmd = f"select obsid, pre_id, status from target where pre_id={obsid}"
        fwd = get_value_from_sybase(cmd)
        if len(fwd) == 0:
            return fwd
        val = fwd[-1]['obsid'].tolist()
        while val is not None:
            cmd = f"select obsid, pre_id, status from target where pre_id={val}"
            out = get_value_from_sybase(cmd)
            if len(out) == 0:
                break
            fwd = astropy.table.vstack([fwd,out])
            val = fwd[-1]['obsid'].tolist()
        return fwd
    #
    # --- Based on checks in the monitor_flag, we know it's part of a series.
    #
    rev = _reverse(obsid)
    fwd = _forward(obsid)
    if len(rev) == 0:
        series = fwd
    elif len(fwd) == 0:
        series = rev
    else:
        series = astropy.table.vstack([rev,fwd])
    sel = np.isin(series['status'], ['unobserved', 'scheduled', 'untriggered'])
    return sorted(series[sel]['obsid'].tolist())

def roll_params(obsid):
    """extract roll related parameter data
    """
    cmd = f"select ordr,roll_constraint,roll_180,roll,roll_tolerance from rollreq where obsid={obsid} order by ordr"
    roll_fetch = get_value_from_sybase(cmd)
    p_dict = _convert_astropy_to_native(roll_fetch, orient = 'list')
    p_dict['roll_ordr'] = max(p_dict.pop('ordr'))
    return p_dict

def time_constraint_params(obsid):
    """extract time constraint related parameter data
    """
    cmd = f"select ordr,window_constraint,tstart,tstop from timereq where obsid={obsid} order by ordr"
    time_fetch = get_value_from_sybase(cmd)
    p_dict = _convert_astropy_to_native(time_fetch, orient = 'list')
    p_dict['time_ordr'] = max(p_dict.pop('ordr'))
    return p_dict

def too_ddt_params(tooid):
    """extract time constraint related parameter data
    """
    cmd = f"select type,start,stop,followup,trig,remarks from too where tooid={tooid}"
    too_fetch = get_value_from_sybase(cmd)
    #: Rename keys to prepend too
    for col in too_fetch.colnames:
        too_fetch.rename_column(col,f"too_{col}")
    p_dict = _convert_astropy_to_native(too_fetch[0])
    return p_dict

def hrc_params(hrcid):
    """extract hrc related parameter data
    """
    cmd = f"select hrc_zero_block,timing_mode,si_mode from hrcparam where hrcid={hrcid}"
    hrc_fetch = get_value_from_sybase(cmd)
    for col in (hrc_fetch.colnames)[1:]:
        hrc_fetch.rename_column(col,f"hrc_{col}") #: Rename keys to prepend too
    p_dict = _convert_astropy_to_native(hrc_fetch[0])
    return p_dict

def acis_params(acisid):
    """extract acis related parameter data
    """
    cmd = f"select {','.join(_ACIS_PARAM_LIST)} from acisparam where acisid={acisid}"
    acis_fetch = get_value_from_sybase(cmd)
    p_dict = _convert_astropy_to_native(acis_fetch[0])
    return p_dict

def aciswin_params(obsid):
    """extract acis window related parameter data
    """
    cmd = f"select {','.join(_ACISWIN_PARAM_LIST)} from aciswin where obsid={obsid} order by ordr"
    aciswin_fetch = get_value_from_sybase(cmd)
    p_dict = _convert_astropy_to_native(aciswin_fetch, orient = 'list')
    p_dict['aciswin_no'] = max(p_dict.pop('ordr'))
    return p_dict

def phase_params(obsid):
    """extract phase related parameter data
    """
    cmd = f"select phase_period,phase_epoch,phase_start,phase_end,phase_start_margin,phase_end_margin from phasereq where obsid={obsid}"
    phase_fetch = get_value_from_sybase(cmd)
    p_dict = _convert_astropy_to_native(phase_fetch[0])
    return p_dict

def dither_params(obsid):
    """extract dither related parameter data
    """
    cmd = f"select y_amp,y_freq,y_phase,z_amp,z_freq,z_phase from dither where obsid={obsid}"
    dither_fetch = get_value_from_sybase(cmd)
    p_dict = _convert_astropy_to_native(dither_fetch[0])
    return p_dict

def sim_params(obsid):
    """extract sim related parameter data
    """
    cmd = f"select trans_offset,focus_offset from sim where obsid={obsid}"
    sim_fetch = get_value_from_sybase(cmd)
    if len(sim_fetch) > 0:
        return _convert_astropy_to_native(sim_fetch[0])
    else:
        return {}
    
def soe_params(obsid):
    """extract soe data
    """
    cmd = f"select soe_roll from soe where obsid={obsid} and unscheduled='N'"
    soe_fetch = get_value_from_sybase(cmd)
    if len(soe_fetch) > 0:
        return _convert_astropy_to_native(soe_fetch[0])
    else:
        return {}

def prop_params(ocat_propid):
    """extract proposal related parameter data
    """
    cmd = f"select ao_str,prop_num,title,joint from prop_info where ocat_propid={ocat_propid}"
    prop_fetch = get_value_from_sybase(cmd)
    prop_fetch.rename_column('prop_num', 'proposal_number')
    prop_fetch.rename_column('title', 'proposal_title')
    prop_fetch.rename_column('joint', 'proposal_joint')
    prop_fetch.rename_column('ao_str', 'obs_ao_str') #: We overwrite the observation ao string with proposer information
    p_dict = _convert_astropy_to_native(prop_fetch[0])
    if p_dict['proposal_joint'] == 'None':
        p_dict['proposal_joint'] = None #: Overwrite string convention of this table with python natives.
    #
    # --- Proposer name
    #
    pi_name = get_value_from_sybase(f"select last from view_pi where ocat_propid={ocat_propid}")
    if len(pi_name) > 0:
        p_dict['pi_name'] = pi_name['last'][0].tolist()
    
    coi_name = get_value_from_sybase(f"select last from view_coi where ocat_propid={ocat_propid}")
    if len(coi_name) > 0:
        p_dict['observer'] = coi_name['last'][0].tolist()
    else:
        p_dict['observer'] = p_dict.get('pi_name')
        
    return p_dict