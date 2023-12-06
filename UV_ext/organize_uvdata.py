#!/usr/bin/env python
import sys,glob,os
from astropy.table import Table
import shutil
import numpy as np
import sncosmo
import astropy.units as u
from astropy.io import fits
import matplotlib.pyplot as plt
import warnings
warnings.simplefilter('ignore')
filt_remove = ['CfA-J/J','CfA-J/j','CfA-K/K','CfA-K/k','CfA-H/H','CfA-H/h','CSP-Y_RC/C',
                   'CSP-J_RC1/E','CSP-J_RC2/F','CSP-H_RC/G','WFC3_IR','UKIRT']
global_swap = {'ZTF-G/X':'ZTF-g','ZTF-g/X':'ZTF-g','ZTF-G':'ZTF-g','ZTF-R/Y':'ZTF-r','ZTF-R':'ZTF-r','ZTF-r/Y':'ZTF-r',
                   'ZTF-I':'ZTF-i','cyan-ATLAS':'ATLAS-cyan/c','orange-ATLAS':'ATLAS-orange/o','ATLAS-orange':'ATLAS-orange/o',
                   'ATLAS-o':'ATLAS-orange/o','ATLAS-orange/a':'ATLAS-orange/o'}


def register_sncosmo_bandpass(filtwave,filttrans,filtname,unit=u.angstrom):
        band = sncosmo.Bandpass(filtwave,
                                filttrans,
                                wave_unit=u.angstrom,name=filtname)
        sncosmo.register(band, force=True)
        
def get_filter_info(kcor_filename,lightcurve,n):
        offset_lightcurve = Table(rows=None,names=['mjd','band','flux','fluxerr','zp','zpsys'],
                     dtype=('f8','S1','f8','f8','f8','U5')
                     )
        hdu = fits.open(kcor_filename)
        zpoff_tab = Table.read(kcor_filename,format='fits')
        zpoff = {row['Filter Name'].strip():{col:row[col] for col in [x for x in zpoff_tab.colnames if x!='Filter Name']}\
                     for row in zpoff_tab}
        snsed = hdu[2].data
        temp_filtertrans = hdu[5].data
        filtertrans = {temp_filtertrans.names[i]:np.array([x[i] for x in temp_filtertrans]) for i in range(len(temp_filtertrans.names))}
        primarysed = hdu[6].data
        hdu.close()
        for i in range(len(lightcurve)):
            m = lightcurve['MJD'][i]
            flt = lightcurve['FLT'][i]
            try:
                sys = zpoff[flt]['Primary Name'].strip()
            except:
                continue
            flx = lightcurve['FLUX'][i]
            flxe = lightcurve['FLUXERR'][i]
            offset_lightcurve.add_row((m,flt,flx*10**(0.4*zpoff[flt]['Primary Mag']),
                              flxe*10**(0.4*zpoff[flt]['Primary Mag']),
                              27.5,sys))
        
        filters = np.unique(offset_lightcurve['band'])

        for band in filters:
            register_sncosmo_bandpass(filtertrans['wavelength (A)'],
                                      filtertrans[band],
                                      band)
        return offset_lightcurve
    
def add_spectrum_to_file(fname,spec_name,snname,filt_dict=None):

    with open(fname,'r') as f:
        lines = f.readlines()
    with open(fname,'r') as f:
        dat = f.read()

    if 'SPECTRUM_END:' not in dat:
        lines.append('# =============================================\n')
        lines.append('# =============================================\n')
        lines.append('NSPECTRA: 0\n')
        lines.append('\n')
        lines.append('NVAR_SPEC: 5\n')
        lines.append('VARNAMES_SPEC: LAMMIN LAMMAX  FLAM  FLAMERR SPECFLAG\n')
        lines.append('\n')
        nspec = 0
    
    if True:
        tab = {'MJD':[],'FLT':[],'FLUX':[],'FLUXERR':[]}
        keep = []
        found_survey = False
        found_z = False

        if 'MWEBV:' in dat or ('RA:' in dat and 'DEC:' in dat):
            found_mw_or_RA = True
        else:
            print('NO MWEBV OR RA/DEC IN ',fname)
        lines = list(np.append(['SNID: %s\n'%snname],lines))
        for i,line in enumerate(lines):
            if line.startswith('VARLIST:'):
                varlist = line.split()
                if 'FIELD' not in varlist:
                    lines[i] = lines[i].replace('FLT ','FLT FIELD ')
            if 'SURVEY:' in line:
                lines[i] = lines[i].replace(line.split()[-1],'UVEXT')
                found_survey = True
            if 'REDSHIFT:' in line:
                z = float(line.split(':')[1].split()[0])
                found_z = True
            elif 'REDSHIFT_HELIO:' in line:
                z = float(line.split(':')[1].split()[0])
                found_z = True

            if line.startswith('OBS:'):
                if filt_dict is not None:
                    if line.split()[2] in filt_dict.keys():
                        lines[i] = line.replace(' '+line.split()[2]+' ',' '+filt_dict[line.split()[2]]+' ')
                if lines[i].split()[2] == 'g-ZTF':
                    lines[i] = lines[i].replace('g-ZTF','ZTF-g')
                elif lines[i].split()[2] == 'r-ZTF':
                    lines[i] = lines[i].replace('r-ZTF','ZTF-r')
                elif lines[i].split()[2]=='i-ZTF':
                    lines[i] = lines[i].replace('i-ZTF','ZTF-i')
                if not np.any([x in lines[i].split()[2] for x in filt_remove]):
                    keep.append(i)
                    
                    
                if lines[i].split()[2] in global_swap.keys():
                    lines[i] = lines[i].replace(lines[i].split()[2],global_swap[lines[i].split()[2]])
                if i in keep:
                    
                        
                    tab['MJD'].append(float(lines[i].split()[1]))
                    tab['FLT'].append(lines[i].split()[2])
                    if 'MAG' in varlist and float(lines[i].split()[varlist.index('MAG')])>0:
                        flux = 10**(-.4*(float(lines[i].split()[varlist.index('MAG')])-27.5))
                        fluxerr = 0.92103 * float(lines[i].split()[varlist.index('MAGERR')]) * flux
                        tab['FLUX'].append(flux)
                        tab['FLUXERR'].append(fluxerr)
                        lines[i] = lines[i].replace(lines[i].split()[varlist.index('FLUXCAL')],'%.4f'%flux)
                        lines[i] = lines[i].replace(lines[i].split()[varlist.index('FLUXCALERR')],'%.4f'%fluxerr)
                    elif 'VOID' in line or 'NULL' in line:
                        tab['FLUX'].append(float(lines[i].split()[4]))
                        tab['FLUXERR'].append(float(lines[i].split()[5]))
                    else:
                        
                        tab['FLUX'].append(float(lines[i].split()[3]))
                        tab['FLUXERR'].append(float(lines[i].split()[4]))
                    if 'FIELD' not in varlist:
                        lines[i] = lines[i].replace(lines[i].split()[2],lines[i].split()[2]+' VOID ')
            elif ('SNID' not in line or i==0) or i>0:
                keep.append(i)
            if line.startswith('NSPECTRA:'):
                nspec = int(line.split()[-1])
                lines[i] = line.replace(line.split()[-1],str(int(line.split()[-1])+1))
                #break
        if not found_survey:
            print('NO SURVEY IN ',fname)
        if not found_z:
            print('NO Z IN ',fname)

            
        lines = list(np.array(lines)[np.array(keep)])
        lines.append('\n')
        lines.append('SPECTRUM_ID: %i\n'%(nspec+1))

    #temp = Table.read(spec_name,format='ascii')
    spectrum = Table.read(spec_name,format='ascii',names=['wave','flux','fluxerr'])

    lines.append('SPECTRUM_MJD: %s\n'%spec_name[spec_name.find('_')+1:spec_name.rfind('.')])
    lines.append('SPECTRUM_NLAM: %i\n'%len(spectrum))
    lam_res = spectrum['wave'][1]-spectrum['wave'][0]

    for row in spectrum:
        lines.append('SPEC: %.3f %.3f %.6E %.6E %i\n'%(row['wave']-lam_res/2,row['wave']+lam_res/2,
                                                         row['flux'],row['fluxerr'],1))
    lines.append('SPECTRUM_END:\n')

    
    tab = Table(tab)
    tab['zp'] = 27.5
    tab['zpsys'] = 'ab'
    #if snname in ['2015F','2013dy','2001eh']:
    #    return z,tab
    with open(fname,'w') as f:
        f.write(''.join(lines))

    return z,tab


_snidlist = ['2021J',
             '2000dk',
             'PTF10icb',
             '2009jb',
             '2020uxz',
             '2001ep',
             '2010kg',
             '2021hiz',
             '2021jad',
             '2015F',
             '2017cbv',
             '2012cg',
             'ASASSN14LP',
             '2010cr',
             '2013dy',
             '2021dov',
             '2010gn',
             '2009le',
             '2001eh',
             '2011by',
             '2020yvu',
             '2010hs',
             '2021zfw',
             '2011fe',
             '1998aq',
             '2017erp',
             '2022eyw',
             '2021fxy',
             '2022hrs',
             '2023bee',
             '2023gft']

## columns are
## 1) true if has optical spec in LC file
## 2) 
_snidlist = {'2021J':{'in_saltshaker_format':True,
                      'lc_files':('UVLC/2021J.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('UVspec/at2021j_59234.971873945.flm','UVspec/at2021jad_59332.0950225825.flm'),
                      'filter_dict':{}},
             #'2000dk':{'in_saltshaker_format':True,
             #         'lc_files':('2000dk.dat'),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             #'PTF10icb':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             #'2009jb':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             '2020uxz':{'in_saltshaker_format':True,
                      'lc_files':('2020uxz.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('at2020uxz_59145.581327385.flm',),
                      'filter_dict':{}},
             '2001ep':{'in_saltshaker_format':True,
                      'lc_files':('2001ep.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2001ep_52210.090993155.flm','sn2001ep_52216.87599885.flm'),
                      'filter_dict':{}},
             #'2010kg':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             '2021hiz':{'in_saltshaker_format':False,
                      'lc_files':('2021hiz.snana.dat'),
                      'optical_spec_files':('2021hiz_spectra.zip'),
                      'uv_spec_files':('sn2021hiz_59323.941822395005.flm'),
                      'filter_dict':{'g':'PS1-g','r':'PS1-r','i':'PS1-i','z':'PS1-z','X':'ZTF-G','Y':'ZTF-R'}},
             '2021jad':{'in_saltshaker_format':True,
                      'lc_files':('2021jad.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('at2021jad_59332.0950225825.flm'),
                      'filter_dict':{}},
             #--
             '2015F':{'in_saltshaker_format':False,
                      'lc_files':('SN2015F.dat'),#,'SN2015F_csp_dr3.dat'),
                      #'lc_files':('SN2015F_csp_dr3.dat'),
                      'optical_spec_files':('2015F_spectra.zip'),
                      'uv_spec_files':('2015F_57097.19845327.flm','2015F_57098.74907818.flm','2015F_57100.871648315.flm','2015F_57103.651092755.flm','2015F_57107.026405345.flm',
                                       '2015F_57108.70207646.flm','2015F_57111.928477205.flm','2015F_57114.585270905.flm','2015F_57117.582528130006.flm','2015F_57124.55984294.flm'),
                      'filter_dict':{'X','N','W','U','B','V','B','g','i','r','u','n'}},
             '2017cbv':{'in_saltshaker_format':False,
                      'lc_files':('SN2017cbv_csp_siblings.dat'),
                      'optical_spec_files':('2017cbv_spectra.zip'),
                      'uv_spec_files':('sn2017cbv_57842.550611285.flm'),
                      'filter_dict':{'X','N','W','U','B','V','B','g','i','r','u','n'}},
             #'2012cg':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             #### formatting is totally different for this LC ####
             'ASASSN14LP':{'in_saltshaker_format':False,
                      'lc_files':('ASASSN-14lp.shappee.txt'),
                      'optical_spec_files':('ASASSN-14lp_spectra.zip'),
                      'uv_spec_files':('asassn14lp_57006.131616662504.flm','asassn14lp_57008.88168032.flm','asassn14lp_57010.805592175006.flm',
                                       'asassn14lp_57013.85702157.flm','asassn14lp_57015.6479012.flm','asassn14lp_57017.63762415.flm',
                                       'asassn14lp_57020.42292526.flm','asassn14lp_57023.40710341.flm','asassn14lp_57026.32499711.flm',
                                       'asassn14lp_57033.326163059995.flm'),
                      'filter_dict':{}},
             #'2010cr':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             '2013dy':{'in_saltshaker_format':False,
                      'lc_files':('LOSS_2013dy.dat'),
                      #'lc_files':('SWIFT_2013dy.dat'),#'LOSS_2013dy.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2013dy_56494.5138120125.flm','sn2013dy_56498.606057245.flm','sn2013dy_56500.329344285.flm','sn2013dy_56502.316740205.flm',
                                       'sn2013dy_56505.578881315.flm','sn2013dy_56509.498418355.flm','sn2013dy_56513.097331234996.flm','sn2013dy_56515.144877535.flm',
                                       'sn2013dy_56518.999067165.flm','sn2013dy_56521.954674895.flm'),
                      'filter_dict':{}},
             '2021dov':{'in_saltshaker_format':False,
                      'lc_files':('2021dov.snana.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('at2021dov_59286.898702277496.flm'),
                      'filter_dict':{}},
             #'2010gn':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             #'2009le':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             '2001eh':{'in_saltshaker_format':False,
                      #'lc_files':('SN_2001eh.dat'),
                      'lc_files':('CFA3_4SHOOTER2_2001eh.DAT'),#'SN_2001eh.dat'),#),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2001eh_52177.759297552504.flm','sn2001eh_52186.42509034666.flm','sn2001eh_52186.42509034667.flm'),
                      'filter_dict':{}},
             '2011by':{'in_saltshaker_format':True,
                      'lc_files':('2011by.BayeSN.txt'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2011by_55681.558770135.flm','sn2011by_55690.383092915.flm'),
                      'filter_dict':{}},
             '2020yvu':{'in_saltshaker_format':True,
                      'lc_files':('2020yvu_data.snana.txt'),
                      'optical_spec_files':(),
                      'uv_spec_files':('at2020yvu_59182.057022955.flm'),
                      'filter_dict':{}},
             #'2010hs':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             '2021zfw':{'in_saltshaker_format':False,
                      'lc_files':('2021zfw_data.snana.txt'),
                      'optical_spec_files':(),
                      'uv_spec_files':('at2021zfw_59498.56909605.flm'),
                      'filter_dict':{}},
             '2011fe':{'in_saltshaker_format':False,
                      'lc_files':('SWIFT_2011fe.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('2011fe_55801.211675135.flm','2011fe_55804.30364847.flm','2011fe_55835.29861821.flm','2011fe_55841.349578855.flm',
                                       '2011fe_55855.209197004995.flm','sn2011fe_56191.1212618.flm','sn2011fe_56191.371550165.flm','sn2011fe_56191.70181059834.flm',
                                       'sn2011fe_56191.9355152275.flm'),
                      'filter_dict':{}},
             #'1998aq':{'in_saltshaker_format':True,
             #         'lc_files':(),
             #         'optical_spec_files':(),
             #         'uv_spec_files':(),
             #         'filter_dict':{}},
             '2017erp':{'in_saltshaker_format':False,
                      'lc_files':('2017erp.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2017erp_57933.53693521834.flm','sn2017erp_57936.47789972334.flm','sn2017erp_57941.31155370667.flm','sn2017erp_57946.21164310099.flm'),
                      'filter_dict':{}},
             '2022eyw':{'in_saltshaker_format':True,
                      'lc_files':('2022eyw_data.snana.txt'),
                      'optical_spec_files':(),
                      'uv_spec_files':('at2022eyw_59681.669229965.flm'),
                      'filter_dict':{}},
             '2021fxy':{'in_saltshaker_format':True,
                      'lc_files':('HSF_21fxy.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2021fxy_59302.370762625.flm','sn2021fxy_59303.3289744125.flm','sn2021fxy_59305.55413052499.flm','sn2021fxy_59312.43009767333.flm'),
                      'filter_dict':{}},
             '2022hrs':{'in_saltshaker_format':True,
                      'lc_files':('2022hrs_data.snana.txt'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2022hrs-hv_59691.4225344775.flm','sn2022hrs-hv_59691.422534477504.flm','sn2022hrs-hv_59695.09384241833.flm','sn2022hrs-hv_59696.350586153334.flm',
                                       'sn2022hrs-hv_59706.86979236.flm','sn2022hrs-hv_59714.80789415.flm','sn2022hrs-hv_59722.48238865667.flm','sn2022hrs_59701.10969302.flm'),
                      'filter_dict':{}},
             '2023bee':{'in_saltshaker_format':False,
                      'lc_files':('GPC1v3_2023bee.snana.dat'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2023bee_59997.984240352496.flm','sn2023bee_59997.984240352496.flm.txt'),
                      'filter_dict':{}},
             '2023gft':{'in_saltshaker_format':True,
                      'lc_files':('2023gft_data.snana.txt'),
                      'optical_spec_files':(),
                      'uv_spec_files':('sn2023gft_60078.21623377.flm'),
                      'filter_dict':{}}}


filelist = []
par_file = []
mjd_file = []
for n,sn in enumerate(_snidlist):
    #if sn!='ASASSN14LP':
    #    continue
    if sn not in ['2015F','2013dy','2001eh']:
        continue
    if sn in ['2021jad','2022eyw']:
        continue
    #print(sn)
    #print(_snidlist[sn])
    try:
    
        new_fname = os.path.join('final_lcs',os.path.basename(_snidlist[sn]['lc_files']))
    except RuntimeError:
        continue
    if _snidlist[sn]['in_saltshaker_format'] or (sn in ['2015F','2013dy','2001eh'] and True):
        filt_dict = None
        try:
            shutil.copyfile(_snidlist[sn]['lc_files'],new_fname)
        except:
            try:
                _snidlist[sn]['lc_files'] = os.path.join('UVLC',_snidlist[sn]['lc_files'])
                if isinstance(_snidlist[sn]['uv_spec_files'],str):
                    _snidlist[sn]['uv_spec_files'] = [_snidlist[sn]['uv_spec_files']]
                if isinstance(_snidlist[sn]['optical_spec_files'],str):
                    _snidlist[sn]['optical_spec_files'] = [_snidlist[sn]['optical_spec_files']]
                _snidlist[sn]['uv_spec_files'] = [os.path.join('UVspec',x) for x in _snidlist[sn]['uv_spec_files']]
                _snidlist[sn]['optical_spec_files'] = [os.path.join('OptSpec',x) for x in _snidlist[sn]['optical_spec_files']]
                
                if sn not in ['2015F','2013dy','2001eh']:
                    shutil.copyfile(_snidlist[sn]['lc_files'],new_fname)
            except:
                continue
            

    else:
        if sn == '2021hiz':
            filt_dict = {'g':'PS1-g','r':'PS1-r','i':'PS1-i','z':'PS1-z','Y':'ZTF-r','X':'ZTF-g'}
        elif sn=='2017cbv':
            filt_dict = {'u':'CSP-u/t','g':'CSP-g/A','r':'CSP-r/L','i':'CSP-i/C','B':'CSP-B/u','n':'CSP-n/x','o':'CSP-o/v','m':'CSP-m/w'}
        elif sn=='2015F':
            
            filt_dict = {'u':'CSP-u/t','g':'CSP-g/A','r':'CSP-r/L','i':'CSP-i/C','B':'CSP-B/u','n':'CSP-n/x','o':'CSP-o/v','m':'CSP-m/w'}
            #filt_dict = {'U':'UVOT-U','B':'UVOT-B','V':'UVOT-V','X':'UVOT-X','N':'UVOT-N','W':'UVOT-W'}
        elif sn=='2017erp':

            filt_dict = {'E':'KAIT4-E','M':'nickel2-M','F':'KAIT4-F','N':'nickel2-N','H':'KAIT4-H','P':'nickel2-P','G':'KAIT4-G','O':'nickel2-O'}
        elif sn=='2013dy':
            #filt_dict = {'E':'KAIT4-E','M':'nickel2-M','F':'KAIT4-F','N':'nickel2-N','H':'KAIT4-H','P':'nickel2-P','G':'KAIT4-G','O':'nickel2-O'}
            filt_dict = {'U':'UVOT-U','B':'UVOT-B','V':'UVOT-V','X':'UVOT-X','N':'UVOT-N','W':'UVOT-W'}
        elif sn=='2001eh':
            #filt_dict = {'A':'KAIT3-A','B':'KAIT3-B','C':'KAIT3-C','D':'KAIT3-D'}
            filt_dict = {'a':'CFA3S-U/a','b':'CFA3S-B/b','c':'CFA3S-V/c','d':'CFA3S-R/d','e':'CFA3S-I/e'}
        elif sn=='2021zfw' or sn=='2021dov' or sn=='2023bee':
            filt_dict = {'g':'PS1-g','r':'PS1-r','i':'PS1-i','z':'PS1-z','y':'PS1-y','Y':'ZTF-r','X':'ZTF-g'}
        elif sn=='2011fe':
            filt_dict = {'E':'KAIT4-E','M':'nickel2-M','F':'KAIT4-F','N':'nickel2-N','H':'KAIT4-H','P':'nickel2-P','G':'KAIT4-G','O':'nickel2-O','U':'UVOT-U','B':'UVOT-B','V':'UVOT-V','X':'UVOT-X','N':'UVOT-N','W':'UVOT-W'}
        elif sn=='ASASSN14LP':
            temp = Table.read('UVLC/'+_snidlist[sn]['lc_files'],format='ascii')
            temp=temp[temp['Tel']=='CSP']
            #temp['Band'] = ['sdss::'+x for x in temp['Band']]
            temp['flux'] = 10**(-.4*(temp['mag']-27.5))
            temp['fluxerr'] = 0.92103 * temp['dmag'] * temp['flux']
            temp['time'] = temp['JD']+49999.5
            temp.remove_column('JD')
            #temp['zp'] = 27.5
            #temp['zpsys'] = 'ab'
            #sncosmo.plot_lc(temp)
            #plt.show()
            with open('UVLC/'+_snidlist[sn]['lc_files'],'r') as f:
                init = f.readlines()
                          
            with open(new_fname,'w') as f:
                for line in init:
                    if line.startswith('#'):
                        f.write(line)
                    elif line.startswith('JD'):
                        break
                f.write('VARLIST:  MJD        FLT  FLUXCAL   FLUXCALERR    MAG     MAGERR     MAGSYS   TELESCOPE    INSTRUMENT   DQ\n')
                for row in temp:
                    f.write('OBS: %f %s %.3f %.3f %.3f %.3f ab CSP CSP None\n'%(row['time'],row['Band'],row['flux'],row['fluxerr'],row['mag'],row['dmag']))
                f.write('# END:\n')
            filt_dict = {'u':'CSP-u/t','g':'CSP-g/A','r':'CSP-r/L','i':'CSP-i/C','B':'CSP-B/u','n':'CSP-n/x','o':'CSP-o/v','m':'CSP-m/w'}
                
        else:
            print(sn)
            print(_snidlist[sn])
            sys.exit()
        if False:
            pass
        else:
            try:
                if  sn=='ASASSN14LP':
                    fail
                shutil.copyfile(_snidlist[sn]['lc_files'],new_fname)
            except:
                _snidlist[sn]['lc_files'] = os.path.join('UVLC',_snidlist[sn]['lc_files'])
                if isinstance(_snidlist[sn]['uv_spec_files'],str):
                    _snidlist[sn]['uv_spec_files'] = [_snidlist[sn]['uv_spec_files']]
                if isinstance(_snidlist[sn]['optical_spec_files'],str):
                    _snidlist[sn]['optical_spec_files'] = [_snidlist[sn]['optical_spec_files']]
                _snidlist[sn]['uv_spec_files'] = [os.path.join('UVspec',x) for x in _snidlist[sn]['uv_spec_files']]
                _snidlist[sn]['optical_spec_files'] = [os.path.join('OptSpec',x) for x in _snidlist[sn]['optical_spec_files']]
                #new_fname = shutil.copyfile(_snidlist[sn]['lc_files'],new_fname)
                if sn!='ASASSN14LP':
                    
                    shutil.copyfile(_snidlist[sn]['lc_files'],new_fname)
    
    #else:
    #    print(sn)
    #    print(_snidlist[sn])
    #    sys.exit()
    #    continue
    
    for spec in _snidlist[sn]['uv_spec_files']:
        try:
           z,tab = add_spectrum_to_file(new_fname,spec,sn,filt_dict)
        except RuntimeError:
            continue
    print(sn)
    continue
    mod = sncosmo.Model('salt3')
    mod.set(z=z)
    lc = get_filter_info('kcor_uvext.fits',tab,n)
    print(len(lc),len(tab))
    
    for filt in np.unique(lc['band']):
        b = sncosmo.get_bandpass(filt)
        if b.wave_eff<3600 or b.wave_eff>7500 or ('ztf' not in filt.lower() and sn in ['2022eyw']):
            lc = lc[lc['band']!=filt]
    maxtime = lc['mjd'][np.array(lc['flux']).argmax()]
    if sn in ['2011fe','2022eyw']:
        lc = lc[np.where(np.logical_and(lc['mjd']-maxtime>-25,lc['mjd']-maxtime<20))[0]]
    else:
        lc = lc[np.where(np.logical_and(lc['mjd']-maxtime>-25,lc['mjd']-maxtime<40))[0]]
    print(lc)
    try:
        
        res,fit = sncosmo.fit_lc(lc,mod,['x0','x1','t0','c'],bounds = {'c':(-1,1),'x1':(-3,3),'x0':(0,10),'t0':np.array([-30,30])+maxtime})
        
        #res,fit = sncosmo.nest_lc(lc,mod,['x0','x1','t0','c'],bounds = {'c':(-1,1),'x1':(-3,3),'x0':(0,1),'t0':np.array([-30,30])+maxtime},maxiter=1000)
        sncosmo.plot_lc(lc,fit)
        plt.savefig(sn+'.png')
        plt.close()
    except:
        sncosmo.plot_lc(lc)
        plt.savefig(sn+'_fail.png')
        plt.close()
        print ('FITTING %s FAILED'%sn)
        continue
    filelist.append(os.path.basename(new_fname)+'\n')
    par_file.append('%s %f %.8f %.8f %.8f 1\n'%(sn,z,fit.get('x0'),fit.get('x1'),fit.get('c')))
    mjd_file.append('%s %.3f\n'%(sn,fit.get('t0')))
with open('SALT3TRAIN_UVEXT.LIST','w') as list_file:
    list_file.write(''.join(filelist))
with open('fitpars.txt','w') as f:
    f.write(''.join(par_file))
with open('mjds.txt','w') as f:
    f.write(''.join(mjd_file))
    
        
        
