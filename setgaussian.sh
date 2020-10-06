#!/bin/bash
#
# * SET GAUSSIAN ENVIRONMENT *
#
# This script must be sourced to export environment variables
# so we must return instead of exit
  if [[ $_ = $0 ]]; then echo "ERROR: script setgaussian.sh must be sourced" ; exit 1; fi
#
  function usage {
    echo 'Usage: . setgaussian.sh [version, e.g. d01]'
    echo '       -g gau : use gaussian directory in path gau'
    echo '       -p pgi : use compiler version pgi'
    echo '       -m mac : use architecture mac (on avogadro)'
    echo '       -t     : generate ctags file $HOME/.tags'
    echo '       -v     : verbose mode'
    echo '       -h     : print this help and return'
    unset -f usage
    return 0
  }
#
  if [ "${#}" -eq 0 ]; then usage; return 0; fi
#
# --------------------------
# CLEAN PREVIOUS ENVIRONMENT
# --------------------------
# check whether Gaussian is already set
  if [[ -n "${gdvroot}" ]] || [[ -n "${g09root}" ]] || [[ -n "${g16root}" ]]; then
    if [[ "${PATH}" = *'#'* ]] || [[ "${LD_LIBRARY_PATH}" = *'#'* ]]; then
      echo 'ERROR: Unable to remove previous Gaussian setup'; return 1
    else
      op='#'
    fi
#   epurate environment variables from the previous Gaussian settings
    if [[ -n "${GAUSS_EXEDIR}" ]]; then
      PATH="$( echo "${PATH}" | sed s${op}:${GAUSS_EXEDIR}${op}${op}g )"
      LD_LIBRARY_PATH="$( echo "${LD_LIBRARY_PATH}" | sed "s${op}${GAUSS_EXEDIR}:${op}${op}" )"
    fi
    unset op; unset GAUSS_EXEDIR ; unset GAUSS_SCRDIR ; unset gdvroot ; unset g09root ; unset g16root ; unset jblroot
  fi
#
# -------------
# PARSE OPTIONS
# -------------
  unset gauroot ; unset ver ; unset vrb ; unset tags
# check for architecture type via hostname
  mac='intel64-nehalem'
  while [[ -n "${1}" ]]; do
    case "${1}" in
      -g | --gau  ) gauroot="${2}"; shift;;
      -m | --mac  ) mac="${2}"; shift;;
      -p | --pgi  ) pgv="${2}"; shift;;
      -t | --tags ) tags="tags";;
      -v | --vrb  ) vrb='-v';;
      -h          ) usage ;;
      *           ) ver="${1}";;
    esac
    shift
  done
  unset -f usage
#
# -------------------------
# DEFINE GAUSSIAN DIRECTORY
# -------------------------
# check whether a specific version has been requested
  if [[ -n "${gauroot}" ]]; then
    if [[ "$( uname )" = "Linux" ]]; then gauroot="$( readlink ${vrb} -e "${gauroot}" )"; fi
    if [[ ! -d ${gauroot} ]]; then echo "ERROR: ${gauroot} directory not found"; return 1; fi
    if [ -x "${gauroot}/gdv" ]; then
      gau='gdv'
    elif [ -x "${gauroot}/g09" ]; then
      gau='g09'
    elif [ -x "${gauroot}/g16" ]; then
      gau='g16'
    else
      echo "ERROR: Invalid Gaussian tree ${gauroot}"; return 1
    fi
  else
#   crawl through the system searching for the desired Gaussian directory
    if [[ -z "${ver}" ]]; then echo "ERROR: Gaussian version not specified"; return 1; fi
    declare findgau=""; declare -i depth=0 ; declare -i mxdpt=4
    while [[ -z "${findgau}" && "${depth}" -le "${mxdpt}" ]]; do
#     Start from / and work your way down by increasing depth
#     -prune is used to select which files or directories to skip
#     -print prints only the matching results and -quit prints only the first one
#     -o is the logical or and everything else has an implicit logical -a and
      exclude="-path /mnt -o -path /proc -o -path /private -o -path /bigdata -o -path /test_ocean -o -path /home -o -path /beegfs"
      gauname="-iname gdv*${ver} -o -iname g16*${ver} -o -iname ${ver}"
      if [[ "$( uname )" = "Linux" ]]; then
        findgau="$( find / -maxdepth "${depth}" -a \( ${exclude} -o ! -readable -o ! -executable \) -prune -o -type d -a \( ${gauname} \) -print -quit )"
      elif  [[ "$( uname )" = "Darwin" ]]; then
        findgau="$( find / -maxdepth "${depth}" -a \( ${exclude} -o ! -perm -g+rx                \) -prune -o -type d -a \( ${gauname} \) -print -quit )"
      else
        echo "ERROR: Unsupported operating system $( uname )" ; return 0
      fi
      depth=$[${depth}+1]
    done
    unset depth; unset mxdpt
    if [[ -z "${findgau}" ]]; then echo "${findgau}" "ERROR: Could not find Gaussian directory"; return 1; fi
    if [ "${vrb}" = '-v' ]; then echo "Found folder ${findgau}"; fi
#   check whether the Gaussian executable is there
    for gau in {"gdv","g09","g16"}; do
      if [[ -x "${findgau}/${gau}" && ! -d "${findgau}/${gau}" ]]; then
        gauroot="${findgau}/.."; break
      elif [[ -x "${findgau}/${gau}/${gau}" && ! -d "${findgau}/${gau}/${gau}" ]]; then
        gauroot="${findgau}"; break
      elif [[ -x "${findgau}/${mac}/${gau}/${gau}" && ! -d "${findgau}/${mac}/${gau}/${gau}" ]]; then
        gauroot="${findgau}/${mac}"; break
      fi
    done
    unset findgau
    if [[ -z "${gauroot}" ]]; then echo "ERROR: Could not find Gaussian executable"; return 1; fi
  fi
  if [ "${vrb}" = '-v' ]; then echo "Using Gaussian tree in ${gauroot}"; fi
# check whether there is a Julien Bloino version
  if [ -d "/home/j.bloino/dev/${gau}.${ver}/${mac}" ]; then
    export jblroot="/home/j.bloino/dev/${gau}.${ver}/${mac}"
    if [ "${vrb}" = '-v' ]; then echo "Defining jblroot as ${jblroot}"; fi
  fi
#
# ----------------------------
# EXPORT ENVIRONMENT VARIABLES
# ----------------------------
# export the relevant environment variables
  if   [[ "${gau}" = "gdv" ]]; then export gdvroot="${gauroot}"
  elif [[ "${gau}" = "g09" ]]; then export g09root="${gauroot}"
  elif [[ "${gau}" = "g16" ]]; then export g16root="${gauroot}"; fi
# load Gaussian bash environment but change the ulimit so we can debug
  if [[ ! -f "${gauroot}/${gau}/bsd/${gau}.profile" ]]; then echo "ERROR: File ${gau}.profile not found"; return 1; fi
  profile="$( mktemp )"
  cp "${gauroot}/${gau}/bsd/${gau}.profile" "${profile}"
  if   [[ "$( uname )" = "Linux"  ]]; then sed -i    's/ulimit\ -c\ 0/ulimit\ -S\ -c\ 0/' "${profile}"
  elif [[ "$( uname )" = "Darwin" ]]; then sed -i '' 's/ulimit\ -c\ 0/ulimit\ -S\ -c\ 0/' "${profile}"
  else echo "ERROR: Unsupported operating system $( uname )" ; return 1; fi
  source "${profile}"
  rm -- "${profile}"
# Set scratch directory
  if [[ -z "${GAUSS_SCRDIR}" ]]; then
    # this works on medusa
    if [[ -d "/home/GauScr/" ]]; then export GAUSS_SCRDIR="/home/GauScr/"; fi
    if [[ -n "${TMPDIR}" ]]; then
      trydir="${TMPDIR}/${USER}/gaussian"
      if [[ ! -d "${trydir}" ]]; then
        mkdir -p -- "${trydir}" || return 1
      fi
      export GAUSS_SCRDIR="${trydir}"; fi
  fi
#
# -----------------------------
# BUILD THE COMPILATION COMMAND
# -----------------------------
# Define the compiler
  if [[ ! -x $( command -v setpgi.sh ) ]]; then
    echo "WARNING: script setpgi.sh not found, might not be able to compile"
  else
   . setpgi.sh ${vrb} -p "${pgv}"
  fi
#  module add pgi/14.7
# Build the mk command
if [[ ! -x $( command -v pgf77 ) ]]; then
    echo "WARNING: PGI compiler not defined"
  elif [[ -x "$( command -v mkcommand )" ]]; then
    mkcommand # "${gauroot}"
    if [ $? -ne 0 ] || [ ! -f mkgau.tmp ]; then echo "ERROR: mkcommand failed"; return 1; fi
#   I change: FCN='${pgi} -Bstatic_pgi' into: FCN='${pgi} -Bstatic_pgi -Wl,-z,muldefs' 
#   to fix errors like "multiple definition of `ftn_allocated'" because the Internet told me to
#   I also fix the location search for include files
    if   [[ "$( uname )" = "Linux"  ]]; then
      sed -i    "s/-Bstatic_pgi/-Bstatic_pgi\ -Wl,-z,muldefs/" mkgau.tmp
      sed -i    "s/make/make\ INCDIR='-I. -I..'/" mkgau.tmp
    elif [[ "$( uname )" = "Darwin" ]]; then
      sed -i '' "s/-Bstatic_pgi/-Bstatic_pgi\ -Wl,-z,muldefs/" mkgau.tmp
      sed -i '' "s/make/make\ INCDIR='-I. -I..'/" mkgau.tmp
    fi
    alias mk="$( cat mkgau.tmp ) |& tee mk.log; chmod o-rwx */*.o */*.exe; chgrp gaussian */*.o */*.exe; date +'%a %d %b %Y %R' &>> mk.log"
    alias makec="$( cat mkgau.tmp )"
    rm -- mkgau.tmp
    if [ "${vrb}" = '-v' ]; then alias "mk"; fi
  else
    echo "WARNING: could not build mk command"
  fi
#
# ---------------
# SETUP TAGS FILE
# ---------------
  if [[ "${tags}" == "tags" ]]; then
    if [[ ! -x "$( command -v ctags )" ]]; then echo "ERROR: ctags command not found"; return 1; fi
    if [[ -f "${HOME}/.tags" ]]; then echo "WARNING: overwriting ${HOME}/.tags file"; fi
    if [[ "${vrb}" == '-v' ]]; then
      ctags -V -R -f "${HOME}/.tags" ${gauroot}
    else
      ctags    -R -f "${HOME}/.tags" ${gauroot}
    fi
    if ! grep -q tags ${HOME}/.vimrc; then echo "WARNING: remember to reference ${HOME}/.tags file in .vimrc"; fi
  fi
#
# unset all intermediate variables
  unset gau ; unset gauroot ; unset ver ; unset mac ; unset vrb ; unset pgv ; unset userd ; unset stats ; unset gauname ; unset tags
  return 0
