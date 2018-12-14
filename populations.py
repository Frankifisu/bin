#!/cm/shared/apps/python/3.6.2/bin/python3

import os
import sys
import re
import argparse # commandline argument parsers
import math
import numpy as np
import scipy
from scipy import constants

PROGNAME = os.path.basename(sys.argv[0])

##########################
#PHYSICAL CONSTANTS IN CGS
##########################
#Numerical
TwoPi = scipy.constants.pi * 2.0E0 # 2pi
IFSC  = 1.0E0 / scipy.constants.fine_structure # Inverse fine structure constant
#Physical
N_A   = scipy.constants.Avogadro # Avogadro's number
k_B   = scipy.constants.Boltzmann * 1.0E7 # Boltzmann constant
R     = N_A * k_B # Universal gas constant
#Atomic
hbar  = scipy.constants.hbar * 1.0E7 # Reduced Planck constant
c     = scipy.constants.c * 1.0E2 # Speed of light
m_e   = scipy.constants.value('electron mass') * 1.0E3 # Electron mass
q_e   = np.sqrt( c * hbar / IFSC ) # Elementary charge
Bohr  = hbar**2 / m_e / q_e**2 # Bohr radius
Ha    = hbar**2 / m_e / Bohr**2 # Hartree energy


#######
#PARSER
#######
parser = argparse.ArgumentParser(description='Compute populations from energies')
parser.add_argument('-T', default=298.15, type=float, action='store',
                    help='Temperature')
parser.add_argument('source', type=str, action='store', help='Nome da cercare')
args = parser.parse_args()

#Constants
kT     = k_B*args.T

inputfile = open(args.source)

ener = np.array([])
for line in inputfile:
    words = line.split("\n")
    energy = float(words[0])
    ener = np.append(ener,energy)

ener = -(ener - ener[0])*Ha/kT
weights = np.exp(ener)
Z = np.sum(weights)
weights = weights/Z

for weight in np.nditer(weights):
    print("{0:6.2f}".format(weight*100))



