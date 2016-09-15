#!/bin/bash
#
# Installation of PGI by Ciro
#   0) check that everything is in order in the folder /opt/pgi/
#        it is best to not have any other pgi installed
#   1) extract the files in ~/pgi/:
#        tar -xzvf pgilinux-13.10.tar.gz ~/pgi/
#   2) go in the directory and execute the command "install":
#        cd ~/pgi/; sudo ./install
#   3) answer all the questions:
#        single system; yes to ACML, CUDA; no to AMD GPU;
#        yes to 2013 directory, MPICHI, read-only
#   4) update the .tcshrc or .bashrc as shown below
#   5) check with "which pgf77"
#
# From .tcshrc by Ciro
# setenv PGI_VER 13.10
# setenv PGI /opt/pgi
# setenv LM_LICENSE_FILE 27000@argozero.dcci.unipi.it
# set path=($PGI/linux86-64/$PGI_VER/bin $path)
#
# This script must be sourced to export environment variables
# so we must return instead of exit
  if [[ $_ = $0 ]]; then echo "ERROR: script setpgi.sh must be sourced" ; exit 1; fi
#
# --------------------------
# CLEAN PREVIOUS ENVIRONMENT
# --------------------------
# check whether PGI is already set
  if [[ -n "${PGIDIR}" ]]; then
    if [[ "${PATH}" = *'#'* ]] || [[ "${LD_LIBRARY_PATH}" = *'#'* ]]; then
      echo 'ERROR: Unable to remove previous PGI setup'; return 1
    else
      op='#'
    fi
#   purge environment variables from the previous settings
    if [[ -n "${PGIDIR}" ]]; then
      PATH="$( echo "${PATH}" | sed s${op}${PGIDIR}/bin/:${op}${op}g )"
      LD_LIBRARY_PATH="$( echo "${LD_LIBRARY_PATH}" | sed "s${op}${PGIDIR}/lib/:${op}${op}" )"
      MANPATH="$( echo "${MANPATH}" | sed s${op}${PGIDIR}/man/:${op}${op} )"
    fi
    unset op
  fi
#
# -------
# SET PGI
# -------
  unset PGI; unset PGIDIR; unset PGI_VER; unset PGI_ARCH
  unset pgv; unset vrb
# Parse options
  while [[ -n "${1}" ]]; do
    case "${1}" in
      -p | --pgv ) pgv="${2}"; shift;;
      -v | --vrb ) vrb='-v';;
      *          ) echo "ERROR: unrecognized setpgi.sh option ${1}"; return 1;;
    esac
    shift
  done
# Set PGI directory
  for trypgi in "/opt" "/usr" "/cm/shared/apps"; do
    if [[ -d "${trypgi}/pgi" ]]; then export PGI="${trypgi}/pgi"; break; fi
  done
  if [[ -z "${PGI}" ]]; then echo "ERROR: PGI directory not found"; return 1; fi
# Set PGI directory
  for arc in "linux86-64" "linux86"; do
#   case where a specific version was requested
    if [[ -n "${pgv}" ]]; then
      if [[ -d "${PGI}/${arc}/${pgv}" ]]; then
        export PGIDIR="${PGI}/${arc}/${pgv}"
        export PGI_ARCH="${arc}"
        export PGI_VER="${pgv}"
        break
      else
        echo "WARNING: PGI version ${pgv} not found, will try other ones"
      fi
      continue
    fi
#   try a bunch of possible versions
    for pgv in 2016 2015 16.1 15.5 15.4 15.3 14.10 13.6 12.10 12.8 12.5 12.4 11.10 11.8 11.6 11.5 11.4 10.8 10.5; do
      if [[ -d "${PGI}/${arc}/${pgv}" ]]; then
        export PGIDIR="${PGI}/${arc}/${pgv}"
        export PGI_ARCH="${arc}"
        export PGI_VER="${pgv}"
        break 2
      fi
    done
  done
  if [[ -z "${PGIDIR}" ]]; then echo "ERROR: Could not find valid PGI"; return 1; fi
  if [[ "${vrb}" = '-v' ]]; then echo "Using PGI directory ${PGIDIR}"; fi
# Set PGI environment
  export PATH="$PGIDIR/bin/:${PATH}"
  export LD_LIBRARY_PATH="$PGIDIR/lib/:${LD_LIBRARY_PATH}"
  export MANPATH="$PGIDIR/man/:${MANPATH}"
# Set PGI license
  if [[ -f "${PGI}/license.dat" ]]; then
    export LM_LICENSE_FILE="${PGI}/license.dat"
  else
    echo "ERROR: PGI licence not found"; return 1
  fi
  return 0
