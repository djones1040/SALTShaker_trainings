#!/usr/bin/env python

from saltshaker.util import snana
import pylab as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import glob
from scipy.stats import binned_statistic

libid_map = {}

def chkpars():
	"""make sure simulated SALT2 pars are same as the original data"""

	simlibdir = '/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_subdirs/simlib'
	
	simlibs = ['Hamuy1996.SIMLIB','OTHER_LOWZ.SIMLIB',
			   'Hicken2009.SIMLIB','Riess1999.SIMLIB',
			   'SDSS.SIMLIB','Jha2006.SIMLIB',
			   'SNLS3.SIMLIB']
	for s in simlibs:
		with open(f'{simlibdir}/{s}') as fin:
			for line in fin:
				if line.startswith('LIBID:'):
					snid = line.split('SNID=')[-1].split(' ')[0]
					libid = int(line.split()[1])
					libid_map[f"{s.split('.')[0]}_{libid}"] = snid

	from txtobj import txtobj
	sp = txtobj('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/snpca_training_v6_resids.txt')
	snfiles_sim = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig_sim/JLA_training_sim/*DAT')
	snidlist,x1list = [],[]
	for i,s in enumerate(snfiles_sim):
		sns = snana.SuperNova(s)

		try: snid = libid_map[f"{sns.SURVEY.split('(')[0].replace('_LC','')}_{sns.SIM_LIBID}"]
		except: import pdb; pdb.set_trace()
		if np.abs(sns.SIM_SALT2x1-sp.x1[sp.SNID == snid]) > 0.001:
			print(f'sim x1 doesn\'t agree with data for {snid}')
			import pdb; pdb.set_trace()
		if snid in snidlist:
			print(f'snid {snid} in sim is not unique!')
			import pdb; pdb.set_trace()

		snidlist += [snid]
		x1list += [sns.SIM_SALT2x1]
	import pdb; pdb.set_trace()
		
def main():

	simlibdir = '/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_subdirs/simlib'
	
	simlibs = ['Hamuy96.SIMLIB','OTHER_LOWZ.SIMLIB',
			   'Hicken2009.SIMLIB','Riess1999.SIMLIB',
			   'SDSS.SIMLIB','Jha2006.SIMLIB',
			   'SNLS3.SIMLIB']
	for s in simlibs:
		with open(f'{simlibdir}/{s}') as fin:
			for line in fin:
				if line.startswith('LIBID:'):
					snid = line.split('SNID=')[-1].split(' ')[0]
					libid = int(line.split()[1])
					libid_map[f"{s.split('.')[0]}_{libid}"] = snid
	#import pdb; pdb.set_trace()
	pdf_pages = PdfPages('specsim.pdf')
	fig = plt.figure()
	axcount = 0
	
	snfiles_data = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_origlc/*dat')
	snfiles_sim = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig_sim/JLA_training_sim/*DAT')
	for i,s in enumerate(snfiles_sim):
		if 'SDSS' in s: continue
		
		sns = snana.SuperNova(s)
		if sns.NSPECTRA == 0: continue

		try: snid = libid_map[f"{sns.SURVEY.split('(')[0].replace('_LC','')}_{sns.SIM_LIBID}"]
		except: import pdb; pdb.set_trace()
		snd = snana.SuperNova(glob.glob(f'/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_origlc/*{snid}*dat')[0])
		zd = float(snd.REDSHIFT_HELIO.split()[0])
		zs = float(sns.REDSHIFT_HELIO.split()[0])
		
		for k in snd.SPECTRA.keys():
			if k not in sns.SPECTRA.keys(): continue
			if not axcount % 3 and axcount != 0:
				fig = plt.figure()
			
			ax = plt.subplot(3,1,axcount % 3 + 1)
			dataAvg = np.median(snd.SPECTRA[k]['FLAM'][(snd.SPECTRA[k]['LAMMIN'] > 6000) &
													   (snd.SPECTRA[k]['LAMMIN'] < 8000)])
			simAvg = np.median(sns.SPECTRA[k]['FLAM'][(sns.SPECTRA[k]['LAMMIN'] > 6000) &
													  (sns.SPECTRA[k]['LAMMIN'] < 8000)])
			specdataflux = binned_statistic(snd.SPECTRA[k]['LAMMIN'],snd.SPECTRA[k]['FLAM'],
											bins=(sns.SPECTRA[k]['LAMMIN']+sns.SPECTRA[k]['LAMMAX'])/2.,
											statistic='median').statistic
			ax.plot(sns.SPECTRA[k]['LAMMIN'][:-1]/(1+zd),specdataflux*simAvg/dataAvg,color='C0')
			ax.plot(sns.SPECTRA[k]['LAMMIN']/(1+zs),sns.SPECTRA[k]['FLAM'],color='C1')
			ax.set_xlabel(r'Wavelength ($\mathrm{\AA}$)')
			ax.set_ylabel('flux')
			#import pdb; pdb.set_trace()
			ax.text(0.5,0.9,f"{snd.SNID} x1={sns.SIM_SALT2x1} c={sns.SIM_SALT2c}, phase={sns.SPECTRA[k]['SPECTRUM_MJD']-float(sns.SIM_PEAKMJD.split()[0]):.1f}",ha='center',va='center',transform=ax.transAxes)
			#if axcount == 5:
			#	import pdb; pdb.set_trace()
			
			axcount += 1
			if not axcount % 3:
				pdf_pages.savefig()
			#import pdb; pdb.set_trace()
		#if axcount >= 10:
		#	break

	pdf_pages.savefig()
	pdf_pages.close()

def snr():

	simlibdir = '/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_subdirs/simlib'
	
	simlibs = ['Hamuy96.SIMLIB','OTHER_LOWZ.SIMLIB',
			   'Hicken2009.SIMLIB','Riess1999.SIMLIB',
			   'SDSS.SIMLIB','Jha2006.SIMLIB',
			   'SNLS3.SIMLIB']
	for s in simlibs:
		with open(f'{simlibdir}/{s}') as fin:
			for line in fin:
				if line.startswith('LIBID:'):
					snid = line.split('SNID=')[-1].split(' ')[0]
					libid = int(line.split()[1])
					libid_map[f"{s.split('.')[0]}_{libid}"] = snid
	#import pdb; pdb.set_trace()
	pdf_pages = PdfPages('specsimsnr.pdf')
	fig = plt.figure()
	axcount = 0
	
	snfiles_data = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_origlc/*dat')
	snfiles_sim = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig_sim/JLA_training_sim/*DAT')
	for i,s in enumerate(snfiles_sim):
		if 'SDSS' in s: continue
		
		sns = snana.SuperNova(s)
		if sns.NSPECTRA == 0: continue

		try: snid = libid_map[f"{sns.SURVEY.split('(')[0].replace('_LC','')}_{sns.SIM_LIBID}"]
		except: import pdb; pdb.set_trace()
		#if snid != 'sn1994d': continue
		snd = snana.SuperNova(glob.glob(f'/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_origlc/*{snid}*dat')[0])
		zd = float(snd.REDSHIFT_HELIO.split()[0])
		zs = float(sns.REDSHIFT_HELIO.split()[0])
		
		for k in snd.SPECTRA.keys():
			if k not in sns.SPECTRA.keys(): continue
			if not axcount % 3 and axcount != 0:
				fig = plt.figure()
			
			ax = plt.subplot(3,1,axcount % 3 + 1)
			dataAvg = np.median(snd.SPECTRA[k]['FLAM'][(snd.SPECTRA[k]['LAMMIN'] > 6000) &
													   (snd.SPECTRA[k]['LAMMIN'] < 8000)])
			simAvg = np.median(sns.SPECTRA[k]['FLAM'][(sns.SPECTRA[k]['LAMMIN'] > 6000) &
													  (sns.SPECTRA[k]['LAMMIN'] < 8000)])

			def sum_in_quad(idx):

				fluxerr = np.median(snd.SPECTRA[k]['FLAM'][idx])/(np.sqrt(np.sum(snd.SPECTRA[k]['FLAMERR'][idx]**2.))/len(idx))

				return fluxerr
#				import pdb; pdb.set_trace()			
			specdataflux = binned_statistic(snd.SPECTRA[k]['LAMMIN'],
											range(len(snd.SPECTRA[k]['FLAM'])),
											#snd.SPECTRA[k]['FLAM']/snd.SPECTRA[k]['FLAMERR'],
											bins=(sns.SPECTRA[k]['LAMMIN']+sns.SPECTRA[k]['LAMMAX'])/2.,
											statistic=sum_in_quad).statistic
			ax.plot(sns.SPECTRA[k]['LAMMIN'][:-1]/(1+zd),specdataflux,color='C0')
			ax.plot(sns.SPECTRA[k]['LAMMIN']/(1+zs),
					sns.SPECTRA[k]['FLAM']/sns.SPECTRA[k]['FLAMERR'],color='C1')
			ax.set_xlabel(r'Wavelength ($\mathrm{\AA}$)')
			ax.set_ylabel('SNR')
			#import pdb; pdb.set_trace()
			ax.text(0.5,0.9,f"{snd.SNID} x1={sns.SIM_SALT2x1} c={sns.SIM_SALT2c}, phase={sns.SPECTRA[k]['SPECTRUM_MJD']-float(sns.SIM_PEAKMJD.split()[0]):.1f}",ha='center',va='center',transform=ax.transAxes)
			#if axcount == 5:
			#	import pdb; pdb.set_trace()
			
			axcount += 1
			if not axcount % 3:
				pdf_pages.savefig()
			#import pdb; pdb.set_trace()
		#if axcount >= 10:
		#	break

	pdf_pages.savefig()
	pdf_pages.close()

	
def lc():

	simlibdir = '/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_subdirs/simlib'
	
	simlibs = ['Hamuy1996.SIMLIB','OTHER_LOWZ.SIMLIB',
			   'Hicken2009.SIMLIB','Riess1999.SIMLIB',
			   'SDSS.SIMLIB','Jha2006.SIMLIB',
			   'SNLS3.SIMLIB']
	for s in simlibs:
		with open(f'{simlibdir}/{s}') as fin:
			for line in fin:
				if line.startswith('LIBID:'):
					snid = line.split('SNID=')[-1].split(' ')[0]
					libid = int(line.split()[1])
					libid_map[f"{s.split('.')[0]}_{libid}"] = snid
	#import pdb; pdb.set_trace()
	pdf_pages = PdfPages('lcsim.pdf')
	fig = plt.figure()
	axcount = 0
	import matplotlib.gridspec as gridspec
	gs1 = gridspec.GridSpec(3, 4)
	gs1.update(wspace=0.0)
	
	snfiles_data = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_origlc/*dat')
	snfiles_sim = glob.glob('/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig_sim/JLA_TRAINING_OTHER_LOWZ/*DAT')
	for i,s in enumerate(snfiles_sim):
		
		sns = snana.SuperNova(s)

		try: snid = libid_map[f"{sns.SURVEY.split('(')[0].replace('_LC','')}_{sns.SIM_LIBID}"]
		except: import pdb; pdb.set_trace()
		snd = snana.SuperNova(glob.glob(f'/Users/David/Dropbox/research/SALT3/examples/JLA_training_orig/JLA_training_origlc/*{snid}*dat')[0])
		zd = float(snd.REDSHIFT_HELIO.split()[0])
		zs = float(sns.REDSHIFT_HELIO.split()[0])

		if not axcount % 12:
			fig = plt.figure()

		ax1 = plt.subplot(gs1[axcount % 12]); ax2 = plt.subplot(gs1[(axcount+1) % 12])
		ax3 = plt.subplot(gs1[(axcount+2) % 12]); ax4 = plt.subplot(gs1[(axcount+3) % 12])
		for f,ax in zip(np.unique(sns.FLT),[ax1,ax2,ax3,ax4]):
			ax.errorbar(snd.MJD[snd.FLT == f]-snd.SEARCH_PEAKMJD,snd.FLUXCAL[snd.FLT == f],snd.FLUXCALERR[snd.FLT == f],fmt='o-',color='C0')
			ax.errorbar(sns.MJD[sns.FLT == f]-snd.SEARCH_PEAKMJD,sns.FLUXCAL[sns.FLT == f],sns.FLUXCALERR[sns.FLT == f],fmt='o-',color='C1')
			ax.set_xlabel('Phase')
			ax.set_xlim([-20,50])
			ax.set_title(f'SN {snid}, filter {f}')
		ax1.set_ylabel('Flux')
			
		if axcount % 12 == 8:
			pdf_pages.savefig()
			plt.close('all')
		else:
			for ax in [ax1,ax2,ax3,ax4]:
				ax.xaxis.set_ticklabels([])
				ax.set_xlabel(None)
		axcount += 4

	pdf_pages.savefig()
	pdf_pages.close()

	
if __name__ == "__main__":
	chkpars()
	#main()
	#snr()
	#lc()
