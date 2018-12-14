#!/cm/shared/apps/python/3.6.2/bin/python3

import os
import sys
import re
import argparse # commandline argument parsers
import socket # module for the fully qualified named of the headnode
import glob
import math
import numpy as np
from subprocess import Popen, PIPE

PROGNAME = sys.argv[0]

#function to extract data from file
def extractx(inpfile,searchpattern):
    with open(inpfile) as myfile:
        y = np.array([])
        for line in myfile:
            if searchpattern in line:
                real = line.split()
                nextline = next(myfile)
                imag = nextline.split()
                x = (np.array([float(i) for i in real[1:4]]) 
                   + np.array([float(i) for i in imag[1:4]])*1.j)
                y = np.append(y,x)
        y = np.reshape(y, (-1,3))
        return y

#format for output
def myformatter(x):
    if np.isrealobj(x):
        return str('{:+.12E}'.format(x))+' '+str('0.0E0')
    elif np.iscomplexobj(x):
        return str('{:+.12E}'.format(x.real))+' '+str('{:+.12E}'.format(x.imag))

#search patter for parsing
electric = 'Re<0|r|n>'
magnetic = 'Re<0|L|n>'
root = 1
DoModuli = True
dosteps = True

#options parsing
for arg in sys.argv[1:]:
    if arg.startswith('-'):
        opt = arg.split('=')
        if opt[0] == '-root':
            if len(opt) == 1:
                print('ERROR: Option "root" requires a value')
                sys.exit()
            try:
                root = int(opt[1])
            except:
                print('ERROR: Invalid value for root')
                sys.exit()
        elif opt[0] == '-gauge':
            if len(opt) == 1:
                print('ERROR: Option "gauge" requires a value')
                sys.exit()
            if not opt[1] in ['r','p']:
                print('ERROR: Invalid value for gauge')
                sys.exit()
            electric = 'Re<0|' + opt[1] + '|n>'
    else:
        dosteps = False
        logfile = arg

#start with a list of files
filelistM = sorted(glob.glob('./*step*M.log'))
filelistP = sorted(glob.glob('./*step*P.log'))

#step and unit parameters
small = 1.e-12
step = 0.001
unit = 'bohr'
BohrInAng = 0.52917721067
L2Mag = 0.5/137.035999139

#print options
np.set_printoptions(precision=12, linewidth=150, suppress=False, formatter={'all': lambda x: myformatter(x)})
#np.set_printoptions(precision=12, linewidth=150, suppress=False, formatter={'all': myformatter(x) for x = 0})

#loop over minus files
print('Dipole derivatives in AU /',unit)
if not dosteps:
    edip = extractx(logfile,electric)
    mdip = extractx(logfile,magnetic)
    edipang = np.angle(edip,deg=False)
    phases  = np.exp(-1.j*edipang)
    edip = edip * phases
    mdip = mdip * phases
    edip.real[abs(edip.real) < small] = 0.0
    edip.imag[abs(edip.imag) < small] = 0.0
    if root != 0:
        print('EDip:',edip[root-1],sep=' ',flush=True)
    else:
        for ixyz in range(3):
            print('EDip:',edip[ixyz],sep=' ',flush=True)
    mdip = mdip * L2Mag
    mdip.real[abs(mdip.real) < small] = 0.0
    mdip.imag[abs(mdip.imag) < small] = 0.0
    if root != 0:
        print('MDip:',mdip[root-1],sep=' ',flush=True)
    else:
        for ixyz in range(3):
            print('MDip:',mdip[ixyz],sep=' ',flush=True)
    sys.exit()

for ideriv in range(len(filelistM)):
#   Read electric dipoles
    edipm = extractx(filelistM[ideriv],electric)
    edipp = extractx(filelistP[ideriv],electric)
#   Find phases of electric dipoles
    edipmang = np.angle(edipm,deg=False)
    edippang = np.angle(edipp,deg=False)
#   Make electric dipoles real
    phasesm = np.exp(-1.j*edipmang)
    phasesp = np.exp(-1.j*edippang)
    edipm = edipm * phasesm
    edipp = edipp * phasesp
#   Read magnetic dipoles
    mdipm = extractx(filelistM[ideriv],magnetic)
    mdipp = extractx(filelistP[ideriv],magnetic)
#   Apply phase correction to magnetic dipoles too
    mdipm = mdipm * phasesm
    mdipp = mdipp * phasesp
#    print('EDipM:',edipm[root-1],sep=' ',flush=True)
#    print('EDipP:',edipp[root-1],sep=' ',flush=True)
#    print('MDipM:',mdipm[root-1],sep=' ',flush=True)
#    print('MDipP:',mdipp[root-1],sep=' ',flush=True)
#   Compute and print derivatives
    edipder = BohrInAng*(edipp-edipm)/(2.*step)
    edipder.real[abs(edipder.real) < small] = 0.0
    edipder.imag[abs(edipder.imag) < small] = 0.0
    print('DEDip:',edipder[root-1],sep=' ',flush=True)
    mdipder = BohrInAng*(mdipp-mdipm)/(2.*step)*L2Mag
    mdipder.real[abs(mdipder.real) < small] = 0.0
    mdipder.imag[abs(mdipder.imag) < small] = 0.0
    print('DMDip:',mdipder[root-1],sep=' ',flush=True)

