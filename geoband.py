#!/cm/shared/apps/python/3.6.2/bin/python3

################################################################################
#                                                                              #
#                GGGG  EEEEE   OOO   BBBB    AAA   N   N  DDDD                 #
#               G      E      O   O  B   B  A   A  NN  N  D   D                #
#               G GGG  EEE    O   O  BBBB   AAAAA  N N N  D   D                #
#               G   G  E      O   O  B   B  A   A  N  NN  D   D                #
#                GGG   EEEEE   OOO   BBBB   A   A  N   N  DDDD                 #
#                                                                              #
#  Geo.B.A.N.D. : Geometry Builder for Accelerated Numerical Differentiation   #
#------------------------------------------------------------------------------#
#                                                                              #
#   Author:          Julien Bloino                                             #
#   Email:           julien.bloino@pi.iccom.cnr.it                             #
#   First version:   2012.11.23                                                #
#   Current version: 2014.01.21                                                #
#   Note:            Requires Python 3                                         #
#                                                                              #
################################################################################

import os, sys
import re
import numpy as np
from math import *

PROGNAME = sys.argv[0]

USAGE = '''\
Usage : {} [options] <inp> <fchk> [<fchk2>]
    where <inp>:  Gaussian input file
          <fchk>: Gaussian formatted checkpoint file
    Available options are:
    -mode=K : Displacement mode. Available keywords are:
              "vib" : (default) Displacement done along the normal modes
              "cart": Displacement done along the cartesian coordinates
    -step=F : Length of the displacement (real number).
    -unit=K : Length unit for the displacement. Available keywords are:
              "au" : Length given in bohr (accepted keyword: bohr)
              "ang": (default) Length given in angstroms
    -geom=K : Data source for reference geometry. Available keywords are:
              "main": (default) Main data file
              "fchk": New formatted checkpoint file (fchk2)
'''.format(PROGNAME)

HELP = '''
The Gaussian input file should be the whole input to use at each step, except
for the geometry and checkpoint file, provided by this script.
The "%Chk" command should not be included and the block where the geometry
should be inserted indicated with the keyword "[GEOMETRY]".
If present, keyword "[TITLESTEP]" will be replace by information about the
step.
2 template files have  been created as examples of input files:
- "template_frq.com": Example of frequency calculations
- "template_frc.com": Example of force calculations

For displacement along the normal coordinates, it is necessary that the normal
coordinates have been saved in the checkpoint file.
To do so, the checkpoint file should be generated using FREQ=SAVENM in input to
ensure that the normal modes are directly saved and the formatted checkpoint
file must be generated with option "-3":
    formchk -3 file.chk file.fchk
'''

TEMPLATE_FORCE = '''\
%NProcShared=1
%Mem=1GB
#P B3LYP/6-31G SCF=VeryTight Int=UltraFine
 Force
 NoSymm

Job title - [TITLESTEP]

0 1
[GEOMETRY]


'''

TEMPLATE_FREQ = '''\
%NProcShared=1
%Mem=1GB
#P B3LYP/6-31G SCF=VeryTight Int=UltraFine
 Freq=(HPModes,SaveNM)
 NoSymm

Job title - [TITLESTEP]

0 1
[GEOMETRY]


'''

ELEMENTS = ['',
    'H' ,                                                                                'He',
    'Li','Be'                                                  ,'B' ,'C' ,'N' ,'O' ,'F' ,'Ne',
    'Na','Mg'                                                  ,'Al','Si','P' ,'S' ,'Cl','Ar',
    'K' ,'Ca','Sc','Ti','V' ,'Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Kr',
    'Rb','Sr','Y' ,'Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I' ,'Xe',
    'Cs','Ba','La','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu',
         'Hf','Ta',' W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn',
    'Fr','Ra','Ac','Th','Pa','U' ,'Np','Pu','Am','Cm','Bk','Cf','Es','Fm','Md','No','Lr',
        'Rf','Db','Sg','Bh','Hs','Mt','Ds']

AU2ANG = 0.52917721092

DEF_STEP_UNIT  = 'Ang'
DEF_STEP_MODES = 0.01
DEF_STEP_CART  = 0.001

DEBUG = True

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

##################################################
#          CHECKPOINT-RELATED VARIABLES          #
##################################################

# -- Keywords and number of columns may change depending on the version of
# -- Gaussian. This may need to be corrected.
CHK_KEY_NATOMS = 'Number of atoms'
CHK_KEY_NVIB   = 'Number of Normal Modes'
CHK_KEY_IAN    = 'Atomic numbers'
CHK_KEY_ATMASS = 'Real atomic weights'
CHK_KEY_GEOM   = 'Current cartesian coordinates'
CHK_KEY_E2     = 'Vib-E2'
CHK_KEY_MODES  = 'Vib-Modes'
CHK_NUM_COLS   = { 'R': 5, 'I': 6 }


##################################################
#                    FUNCTIONS                   #
##################################################

def superpose(ref_coord, coord, atmass):
    """
    Superpose new_coord over ref_coord
    See G.R. Kneller, Mol. Sim. 7, 113-119 (1991)
              "       J. Chim. Phys. 88,2709-2715 (1991)
    """
    COM0 = [0., 0., 0.]
    COM1 = [0., 0., 0.]
    natoms = len(atmass)
    new_coord = np.zeros((natoms,3))
    rotmat = np.identity(3)
    qmat   = np.zeros((4,4))
    qmvec  = np.zeros((4,4))
    qmval  = np.zeros(4)
    totwt  = 0.0
    # SUPERPOSE CENTER OF MASSES
    for ia in range(natoms):
        totwt += atmass[ia]
        for ix in range(3):
            COM0[ix] += atmass[ia]*ref_coord[ia*3+ix]
            COM1[ix] += atmass[ia]*coord[ia*3+ix]
    for ix in range(3):
        dx = (COM0[ix] - COM1[ix])/totwt
        for ia in range(natoms):
            new_coord[ia,ix] = coord[ia*3+ix] + dx
    # COMPUTE ROTATION MATRX
    for ia in range(natoms):
        x0  = ref_coord[ia*3]
        y0  = ref_coord[ia*3+1]
        z0  = ref_coord[ia*3+2]
        x   = ref_coord[ia*3]
        y   = ref_coord[ia*3+1]
        z   = ref_coord[ia*3+2]
        xy0 = x*y0
        xz0 = x*z0
        yx0 = y*x0
        yz0 = y*z0
        zx0 = z*x0
        zy0 = z*y0
        diag0 = x*x + y*y + z*z + x0*x0 + y0*y0 +z0*z0
        diag1 = 2.0*x*x0
        diag2 = 2.0*y*y0
        diag3 = 2.0*z*z0
        q1    = diag0 - diag1 - diag2 - diag3
        q3    = diag0 - diag1 + diag2 + diag3
        q6    = diag0 + diag1 - diag2 + diag3
        q10   = diag0 + diag1 + diag2 - diag3
        q2    = yz0 - zy0
        q4    = zx0 - xz0
        q7    = xy0 - yx0
        q5    = -(xy0 + yx0)
        q8    = -(xz0 + zx0)
        q9    = -(yz0 + zy0)
        qmat[0,0] += q1 * atmass[ia]
        qmat[1,1] += q3 * atmass[ia]
        qmat[2,2] += q6 * atmass[ia]
        qmat[3,3] += q10* atmass[ia]
        qmat[1,0] += q2 * atmass[ia] * 2.0
        qmat[2,0] += q4 * atmass[ia] * 2.0
        qmat[3,0] += q7 * atmass[ia] * 2.0
        qmat[2,1] += q5 * atmass[ia] * 2.0
        qmat[3,1] += q8 * atmass[ia] * 2.0
        qmat[3,2] += q9 * atmass[ia] * 2.0
    qmval, qmvec = np.linalg.eigh(qmat,UPLO='L')
    q0q0 = qmvec[0,0] * qmvec[0,0]
    q1q1 = qmvec[1,0] * qmvec[1,0]
    q2q2 = qmvec[2,0] * qmvec[2,0]
    q3q3 = qmvec[3,0] * qmvec[3,0]
    rotmat[0,0] = q0q0 + q1q1 - q2q2 - q3q3
    rotmat[1,1] = q0q0 - q1q1 + q2q2 - q3q3
    rotmat[2,2] = q0q0 - q1q1 - q2q2 + q3q3
    q0q1 = qmvec[0,0] * qmvec[1,0]
    q0q2 = qmvec[0,0] * qmvec[2,0]
    q0q3 = qmvec[0,0] * qmvec[3,0]
    q1q2 = qmvec[1,0] * qmvec[2,0]
    q1q3 = qmvec[1,0] * qmvec[3,0]
    q2q3 = qmvec[2,0] * qmvec[3,0]
    rotmat[0,1] = 2.0 * (q1q2 - q0q3)
    rotmat[1,0] = 2.0 * (q1q2 + q0q3)
    rotmat[0,2] = 2.0 * (q1q3 + q0q2)
    rotmat[2,0] = 2.0 * (q1q3 - q0q2)
    rotmat[1,2] = 2.0 * (q2q3 - q0q1)
    rotmat[2,1] = 2.0 * (q2q3 + q0q1)
    if DEBUG:
        print('ROTATION MATRIX')
        for i in range(3):
            print('{0[0]:8.5f}{0[1]:8.5f}{0[2]:8.5f}'.format(rotmat[i,:]))

    new_coord = np.dot(new_coord,rotmat)
    return new_coord

def ref_geom(ftype, dfile):
    """
    Read file "dfile" and extract the reference geometry and associated atomic
    numbers
    """
    natoms = 0
    coord = []
    atnum = []
    found_keys = { 'Geom': False, 'NAtoms': False, 'IAN': False }

    buf = open(dfile, 'r')
    if ftype == 'fchk':
        # READ FORMATTED CHECKPOINT FILE AND EXTRACT GEOMETRY
        for l in buf:
            if l.find(CHK_KEY_NATOMS) != -1:
                found_keys['NAtoms'] = True
                dtype = 'I'
                try:
                    natoms = int(l.split()[-1])
                except:
                    print('ERROR: Cannot read the number of atoms')
                    buf.close()
                    sys.exit()
            elif l.find(CHK_KEY_IAN) != -1:
                found_keys['IAN'] = True
                dtype = 'I'
                if not found_keys['NAtoms']:
                    print('ERROR: Atomic number found before number of atoms.')
                    buf.close()
                    sys.exit()
                ntot  = natoms
                ncols = CHK_NUM_COLS[dtype]
                nrows = ceil(ntot/ncols)
                for i in range(nrows):
                    l = next(buf)
                    if not l:
                        print('ERROR: End-of-file reached while reading geometry ')
                        buf.close()
                        sys.exit()
                    cols = l.split()
                    N = min(ncols,ntot-i*ncols)
                    atnum.extend([int(c) for c in cols[:N]])
            elif l.find(CHK_KEY_GEOM) != -1:
                found_keys['Geom'] = True
                dtype = 'R'
                if not found_keys['NAtoms']:
                    print('ERROR: Geomtry found before number of atoms.')
                    buf.close()
                    sys.exit()
                ntot  = 3*natoms
                ncols = CHK_NUM_COLS[dtype]
                nrows = ceil(ntot/ncols)
                for i in range(nrows):
                    l = next(buf)
                    if not l:
                        print('ERROR: End-of-file reached while reading geometry ')
                        buf.close()
                        sys.exit()
                    cols = l.split()
                    N = min(ncols,ntot-i*ncols)
                    coord.extend([float(c) for c in cols[:N]])
        buf.close()

        if not found_keys['IAN']:
            print('ERROR: Atomic numbers section not found.')
            sys.exit()
        if not found_keys['Geom']:
            print('ERROR: Geometry section not found.')
            sys.exit()
    buf.close()

    return (coord, atnum)

def build_step_modes(template, formchk, step, ref_coord, ref_atnum, new_geom):
    """
    Read normal coordinates from the formatted checkpoint file and build the
    displaced geometries
    """
    buf_chk = open(formchk, 'r')
    # READ FORMATTED CHECKPOINT FILE AND EXTRACT NORMAL MODES
    natoms = 0
    nvib  = 0
    coord = []
    E2    = []
    vib   = []
    atnum = []
    atmass = []
    found_keys = {
        'Geom': False, 'NAtoms': False, 'NVib': False, 'E2': False,
        'Modes': False, 'IAN': False, 'atmass': False
    }

    for l in buf_chk:
        if l.find(CHK_KEY_NATOMS) != -1:
            found_keys['NAtoms'] = True
            dtype = 'I'
            try:
                natoms = int(l.split()[-1])
            except:
                print('ERROR: Cannot read the number of atoms')
                buf_chk.close()
                sys.exit()
        elif l.find(CHK_KEY_NVIB) != -1:
            found_keys['NVib'] = True
            dtype = 'I'
            try:
                nvib = int(l.split()[-1])
            except:
                print('ERROR: Cannot read the number of modes')
                buf_chk.close()
                sys.exit()
        elif l.find(CHK_KEY_IAN) != -1:
            found_keys['IAN'] = True
            dtype = 'I'
            if not found_keys['NAtoms']:
                print('ERROR: Atomic number found before number of atoms.')
                buf_chk.close()
                sys.exit()
            ntot  = natoms
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading geometry ')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                atnum.extend([int(c) for c in cols[:N]])
        elif l.find(CHK_KEY_ATMASS) != -1:
            found_keys['atmass'] = True
            dtype = 'R'
            if not found_keys['NAtoms']:
                print('ERROR: Atomic masses found before number of atoms.')
                buf_chk.close()
                sys.exit()
            ntot  = natoms
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading geometry ')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                atmass.extend([float(c) for c in cols[:N]])
        elif l.find(CHK_KEY_GEOM) != -1:
            found_keys['Geom'] = True
            dtype = 'R'
            if not found_keys['NAtoms']:
                print('ERROR: Geomtry found before number of atoms.')
                buf_chk.close()
                sys.exit()
            ntot  = 3*natoms
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading geometry ')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                coord.extend([float(c) for c in cols[:N]])
        elif l.find(CHK_KEY_E2) != -1:
            found_keys['E2'] = True
            dtype = 'R'
            if not found_keys['NVib']:
                print('ERROR: "Vib-E2" found before number of normal modes.')
                buf_chk.close()
                sys.exit()
            ntot  = 2*nvib
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading "Vib-E2" '
                        + 'section.')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                E2.extend([float(c) for c in cols[:N]])
        elif l.find(CHK_KEY_MODES) != -1:
            found_keys['Modes'] = True
            dtype = 'R'
            if not found_keys['NAtoms']:
                print('ERROR: "Vib-Modes" found before number of atoms.')
                buf_chk.close()
                sys.exit()
            if not found_keys['NVib']:
                print('ERROR: "Vib-Modes" found before number of normal modes.')
                buf_chk.close()
                sys.exit()
            ntot  = nvib*3*natoms
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                #l = buf_chk.next()
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading "Vib-Modes" '
                        + 'section.')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                vib.extend([float(c) for c in cols[:N]])
    buf_chk.close()

    if not found_keys['IAN']:
        print('ERROR: Atomic numbers section not found.')
        sys.exit()
    if not found_keys['Geom']:
        print('ERROR: Geometry section not found.')
        sys.exit()
    if not found_keys['E2']:
        print('ERROR: "Vib-E2" section not found.')
        sys.exit()
    if not found_keys['Modes']:
        print('ERROR: "Vib-Modes" section not found.')
        sys.exit()

    if new_geom:
        if len(ref_atnum) != natoms:
            print('ERROR: Different number of atoms between data files')
        else:
            for i in range(natoms):
                if atnum[i] != ref_atnum[i]:
                    print('ERROR: Different sequence of atoms between '
                            + 'reference geometry and fchk')
        geom = superpose(ref_coord, coord, atmass)
    else:
        geom = np.reshape(np.array(ref_coord), (natoms,3), order='C')

    freq     = E2[:nvib]
    red_mass = E2[nvib:]
    modes = np.reshape(np.array(vib), (nvib,3*natoms), order='C')

    if DEBUG:
        print('INFORMATION READ FROM CHECKPOINT FILE')
        print(' -- Reference Geometry (Bohr) --')
        print(' Atom        X            Y            Z')
        for ia in range(natoms):
            print(' {0:4s}{1[0]:12.6f} {1[1]:12.6f} {1[2]:12.6f}'.
                    format(ELEMENTS[atnum[ia]], geom[ia,:]*AU2ANG))
        print(' -- Frequencies (cm^-1) --')
        for i in range(nvib):
            print(' Mode {:5d}: {:15.6f}'.format(i+1, freq[i]))
        print(' -- Reduced mass --')
        for i in range(nvib):
            print(' Mode {:5d}: {:15.6f}'.format(i+1, red_mass[i]))

    #print(vib)
    for i in range(nvib):
        modes[i,:] /= sqrt(red_mass[i])
    if DEBUG:
        ncols = 5
        n = ceil(nvib/ncols)
        for i in range(n):
            i0 = i*ncols
            i1 = min(i0+ncols,nvib)
            fmt = 6*' '+'{:4d}'+(i1-i0-1)*(12*' '+'{:4d}')
            print(fmt.format(*[j+1 for j in range(i0,i1)]))
            for j in range(3*natoms):
                fmt = (i1-i0)*'{:16.8e}'
                print(fmt.format(*[modes[k,j] for k in range(i0,i1)]))

        print(' --------------------------------------------------')

    print('STEP: {:8.5f} Ang <-> {:8.5f} bohr'.format(step, step/AU2ANG))
    step_au = step/AU2ANG
    file_blocks = os.path.splitext(template)
    fmt_fname = '{base}_step{istep:0'+str(len(str(nvib)))+'d}{sign}{ext}'
#Franco
    nscan = 3
    if nscan>13:
        print('ERROR: 13 points supported at most')
        sys.exit()
#   Zero point
    print('ORIGINAL GEOMETRY')
    new_file = fmt_fname.format(base=file_blocks[0], istep=0,
            sign='0', ext=file_blocks[1])
    new_chk = os.path.splitext(new_file)[0]+'.chk'
    print('File: {}'.format(new_file))
    new_geom = geom
    build_input(template, new_file, new_chk, atnum, new_geom, 0, nvib,
        '0')
    sys.exit()
    for i in range(nvib):
        for iscan in range(nscan):
            # +DELTA
            sign = 'P'
            if nscan == 1:
                symbol = sign
            else:
                symbol = ALPHABET[iscan-nscan:iscan-nscan-1:-1]
            vec = np.reshape(modes[i], (natoms,3))
            print('DISPLACED GEOMETRY: Step {:3d}, +Delta'.format(i+1))
            new_file = fmt_fname.format(base=file_blocks[0], istep=i+1,
                    sign=symbol, ext=file_blocks[1])
            new_chk = os.path.splitext(new_file)[0]+'.chk'
            print('File: {}'.format(new_file))
            new_geom = geom + vec*step_au*(iscan+1)
            build_input(template, new_file, new_chk, atnum, new_geom, i+1, nvib,
                sign)
            # -DELTA
            sign = 'M'
            if nscan == 1:
                symbol = sign
            else:
                symbol = ALPHABET[nscan-iscan-1:nscan-iscan:1]
            vec = np.reshape(modes[i], (natoms,3))
            print('DISPLACED GEOMETRY: Step {:3d}, -Delta'.format(i+1))
            new_file = fmt_fname.format(base=file_blocks[0], istep=i+1,
                    sign=symbol, ext=file_blocks[1])
            new_chk = os.path.splitext(new_file)[0]+'.chk'
            print('File: {}'.format(new_file))
            new_geom = geom - vec*step_au*(iscan+1)
            build_input(template, new_file, new_chk, atnum, new_geom, i+1, nvib,
                sign)

def build_step_cart(template, formchk, step, ref_coord, ref_atnum, new_geom):
    """
    Build displaced geometries moving one atom at a time along one cartesian
    coordinate (same as frequency calculations of TD)
    """
    buf_chk = open(formchk, 'r')
    # READ FORMATTED CHECKPOINT FILE AND EXTRACT NORMAL MODES
    natoms = 0
    coord = []
    atnum = []
    found_keys = { 'Geom': False, 'NAtoms': False, 'IAN': False }

    for l in buf_chk:
        if l.find(CHK_KEY_NATOMS) != -1:
            found_keys['NAtoms'] = True
            dtype = 'I'
            try:
                natoms = int(l.split()[-1])
            except:
                print('ERROR: Cannot read the number of atoms')
                buf_chk.close()
                sys.exit()
        elif l.find(CHK_KEY_IAN) != -1:
            found_keys['IAN'] = True
            dtype = 'I'
            if not found_keys['NAtoms']:
                print('ERROR: Atomic number found before number of atoms.')
                buf_chk.close()
                sys.exit()
            ntot  = natoms
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading geometry ')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                atnum.extend([int(c) for c in cols[:N]])
        elif l.find(CHK_KEY_GEOM) != -1:
            found_keys['Geom'] = True
            dtype = 'R'
            if not found_keys['NAtoms']:
                print('ERROR: Geomtry found before number of atoms.')
                buf_chk.close()
                sys.exit()
            ntot  = 3*natoms
            ncols = CHK_NUM_COLS[dtype]
            nrows = ceil(ntot/ncols)
            for i in range(nrows):
                l = next(buf_chk)
                if not l:
                    print('ERROR: End-of-file reached while reading geometry ')
                    buf_chk.close()
                    sys.exit()
                cols = l.split()
                N = min(ncols,ntot-i*ncols)
                coord.extend([float(c) for c in cols[:N]])
    buf_chk.close()

    if not found_keys['IAN']:
        print('ERROR: Atomic numbers section not found.')
        sys.exit()
    if not found_keys['Geom']:
        print('ERROR: Geometry section not found.')
        sys.exit()

    geom = np.reshape(np.array(coord), (natoms,3), order='C')

    if False:
        print('INFORMATION READ FROM CHECKPOINT FILE')
        print(' -- Reference Geometry (Bohr) --')
        print(geom)


    nat3 = 3*natoms

    print('STEP: {:8.5f} Ang <-> {:8.5f} bohr'.format(step, step/AU2ANG))
    step_au = step/AU2ANG
    file_blocks = os.path.splitext(template)
    fmt_fname = '{base}_step{istep:0'+str(len(str(3*natoms)))+'d}{sign}{ext}'
    ii = 0
    for ia in range(natoms):
        for jx in range(3):
            ii += 1
            vec = np.zeros((natoms,3))
            vec[ia,jx] = step_au
            # +DELTA
            sign = 'P'
            print('DISPLACED GEOMETRY: Step {:3d}, +Delta'.format(ii))
            new_file = fmt_fname.format(base=file_blocks[0], istep=ii, sign=sign,
                    ext=file_blocks[1])
            new_chk = os.path.splitext(new_file)[0]+'.chk'
            print('File: {}'.format(new_file))
            new_geom = geom + vec
            build_input(template, new_file, new_chk, atnum, new_geom, ii,
                3*natoms, sign)
            # -DELTA
            sign = 'M'
            print('DISPLACED GEOMETRY: Step {:3d}, -Delta'.format(ii))
            new_file = fmt_fname.format(base=file_blocks[0], istep=ii, sign=sign,
                    ext=file_blocks[1])
            new_chk = os.path.splitext(new_file)[0]+'.chk'
            print('File: {}'.format(new_file))
            new_geom = geom - vec
            build_input(template, new_file, new_chk, atnum, new_geom, ii,
                3*natoms, sign)

def build_input(template, in_file, chk_file, atnum, geom, step, tot_step,
    sign):
    """
    Write input file (in_file) based on template with new geometry
    """
    len_step = int(len(str(tot_step)))
    fmt_step = 'step {}{:'+str(len_step)+'d} on {:'+str(len_step)+'d}'
    fmt_geom = '{at:2s} {xyz[0]:20.14f} {xyz[1]:20.14f} {xyz[2]:20.14f}\n'
    if sign == 'P':
        symb = '+'
    elif sign == 'M':
        symb = '-'
    else:
        symb = '0'
    buf = open(in_file, 'w')
    tpl = open(template, 'r')
    for l in tpl:
        l2 = l.lower()
        if l2.find('#') != -1:
            buf.write('%Chk={}\n'.format(chk_file))
            buf.write(l)
        elif l2.find('[titlestep]') != -1:
            s = re.sub('\[titlestep\]',fmt_step.format(symb,step,tot_step), l,
                flags=re.I)
            buf.write(s)
        elif l2.find('[geometry]') != -1:
            for ia in range(len(geom)):
                buf.write(fmt_geom.format(at=ELEMENTS[atnum[ia]],
                        xyz=geom[ia]*AU2ANG))
        elif l2.find('%chk') == -1:
            buf.write(l)

    buf.close()
    tpl.close()

##################################################
#                  MAIN PROGRAM                  #
##################################################

if __name__ == '__main__':
    if set(['-h', '--help']) & set(sys.argv):
        print(USAGE)
        print(HELP)
        buf = open('template_frq.com', 'w')
        buf.write(TEMPLATE_FREQ)
        buf.close()
        buf = open('template_frc.com', 'w')
        buf.write(TEMPLATE_FORCE)
        buf.close()
        sys.exit()
    elif len(sys.argv) < 3:
        print(USAGE)
        print('Use "{} -h" to display the help'.format(PROGNAME))
        sys.exit()

    iopt = 0
    step = None
    mode = None
    unit = None
    geom = None
    files = []
    for arg in sys.argv[1:]:
        if arg.startswith('-'):
            opt = arg.split('=')
            if opt[0] == '-step':
                if len(opt) == 1:
                    print('ERROR: Option "step" requires a value')
                    sys.exit()
                try:
                    step = float(opt[1])
                except:
                    print('ERROR: Invalid value for the step')
                    sys.exit()
            elif opt[0] == '-mode':
                if len(opt) == 1:
                    print('ERROR: Option "mode" requires a keyword: vib, cart')
                    sys.exit()
                if not opt[1].lower() in ['vib', 'cart']:
                    print('ERROR: Unsupported keyword: "{}"'.format(opt[1]))
                    sys.exit()
                else:
                    mode = opt[1].lower()
            elif opt[0] == '-unit':
                if len(opt) == 1:
                    print('ERROR: Option "unit" requires a keyword: au, ang, '
                        + 'bohr')
                    sys.exit()
                if not opt[1].lower() in ['au', 'ang', 'bohr']:
                    print('ERROR: Unsupported keyword: "{}"'.format(opt[1]))
                    sys.exit()
                else:
                    if opt[1].lower() in ['au', 'bohr']:
                        mode = 'au'
                    else:
                        mode = 'ang'
            elif opt[0] == '-geom':
                if len(opt) == 1:
                    print('ERROR: Option "geom" requires a keyword: main, fchk')
                    sys.exit()
                if not opt[1].lower() in ['main', 'fchk']:
                    print('ERROR: Unsupported keyword: "{}"'.format(opt[1]))
                    sys.exit()
                else:
                    if opt[1].lower() == 'fchk':
                        geom = 'fchk'
                    else:
                        geom = 'main'
        else:
            iopt += 1
            if iopt == 1:
                file_gin = arg
            elif iopt == 2:
                file_fchk = arg
            else:
                files.append(arg)
    if len(files)>0 and geom != 'fchk':
        print('ERROR: Too many data files given')
        sys.exit()

    # CHECK FILE EXISTENCE
    if not os.path.exists(file_gin):
        print('ERROR: Input file "{}" does not exist.'.format(file_gin))
        sys.exit()
    if not os.path.exists(file_fchk):
        print('ERROR: Formatted checkpoint file "{}" does not exist.'\
            .format(file_fchk))
        sys.exit()
    for f in files:
        if not os.path.exists(f):
            print('ERROR: Data file "{}" does not exist.'.format(f))
            sys.exit()
    # SET DEFAULT VALUES FOR UNSET VARIABLES
    if not mode:
        mode = 'vib'
    if not step:
        if mode == 'vib':
            step = DEF_STEP_MODES
        else:
            step = DEF_STEP_CART
    if not unit:
        unit = 'ang'

    if unit == 'au':
        new_step = step*AU2ANG
    else:
        new_step = step

    if geom == 'fchk':
        coord, atnum = ref_geom('fchk', files[0])
        new_geom = True
    else:
        coord, atnum = ref_geom('fchk', file_fchk)
        new_geom = False

    if mode == 'vib':
        build_step_modes(file_gin, file_fchk, new_step, coord, atnum, new_geom)
    else:
        build_step_cart(file_gin, file_fchk, new_step, coord, atnum, new_geom)

