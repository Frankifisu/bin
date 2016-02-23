#!/bin/bash
#
# * SET GAUSSIAN ENVIRONMENT *
#
# Note: This script must be sourced to export environment variables
#       so we must return instead of exit
#
  function usage {
    echo 'Usage: . setgaussian.sh [version, e.g. d01]'
    echo '       -g gau : use gaussian directory in path gau'
    echo '       -p pgi : use compiler version pgi'
    echo '       -m mac : use architecture mac (on avogadro)'
    echo '       -v     : verbose mode'
    echo '       -h     : print this help and return'
    unset -f usage
    return 0
  }
#
  if [ "${#}" -eq 0 ]; then usage ; fi
#
# --------------------------
# CLEAN PREVIOUS ENVIRONMENT
# --------------------------
# check whether Gaussian is already set
  if [[ -n "${gdvroot}" ]] || [[ -n "${g09root}" ]]; then
    if [[ "${PATH}" = *'#'* ]] || [[ "${LD_LIBRARY_PATH}" = *'#'* ]]; then
      echo 'ERROR: Unable to remove previous Gaussian setup'; return 1
    else
      op='#'
    fi
#   epurate environment variables from the previous Gaussian settings
    TOREMOVE="${GAUSS_EXEDIR}:"
    PATH=$( echo "${PATH}" | sed s${op}${TOREMOVE}${op}${op} )
    LD_LIBRARY_PATH="$( echo "${LD_LIBRARY_PATH}" | sed "s${op}${TOREMOVE}${op}${op}" )"
    unset TOREMOVE ; unset op
    unset GAUSS_EXEDIR ; unset gdvroot ; unset g09root ; unset jblroot ; unset GAUSS_SCRDIR
  fi
#
# -------------
# PARSE OPTIONS
# -------------
  unset gauroot ; unset ver ; unset vrb
  pgv='14.1' ; mac='intel64-nehalem'
  while [[ -n "${1}" ]]; do
    case "${1}" in
      -g | --gau ) gauroot="${2}"; shift;;
      -m | --mac ) mac="${2}"; shift;;
      -p | --pgi ) pgv="${2}"; shift;;
      -v | --vrb ) vrb='-v';;
      -h         ) usage ;;
      *          ) ver="${1}";;
    esac
    shift
  done
  unset -f usage
#
# -------------------------
# DEFINE GAUSSIAN DIRECTORY
# -------------------------
# check whether a specific gdv or g09 has been requested
  if [[ -n "${gauroot}" ]]; then
    if [[ ! -d ${gauroot} ]]; then echo "ERROR: ${gauroot} directory not found"; return 1; fi
    if [ -x "${gauroot}/gdv" ]; then
      gau='gdv'
    elif [ -x "${gauroot}/g09" ]; then
      gau='g09'
    else
      echo "ERROR: Invalid Gaussian tree ${gauroot}"; return 1
    fi
  else
#   crawl through the system searching for the desired Gaussian directory
    if [[ -z "${ver}" ]]; then echo "ERROR: Gaussian version not specified"; return 1; fi
    findgau="" ; declare -i depth=0 ; declare -i mxdpt=5
    while [[ -z "${findgau}" && "${depth}" -le "${mxdpt}" ]]; do
#     Start from / and work your way down by increasing depth
#     -prune is used to select which files or directories to skip
#     -print prints only the matching results and -quit prints only the first one
#     -o is the logical or and everything else has an implicit logical -a and
      if [[ "$( uname )" = "Linux" ]]; then
        findgau="$( find / -maxdepth "${depth}" -a \( -path "/mnt" -o -path "/proc" -o -path "/private" -o ! -readable -o ! -executable \) -prune -o -type d -a \( -iname "gdv*${ver}" -o -iname "g09*${ver}" -o -iname "${ver}" \) -print -quit )"
      elif  [[ "$( uname )" = "Darwin" ]]; then
        findgau="$( find / -maxdepth "${depth}" -a \( -path "/mnt" -o -path "/proc" -o -path "/private" -o ! -perm -g+rx                \) -prune -o -type d -a \( -iname "gdv*${ver}" -o -iname "g09*${ver}" -o -iname "${ver}" \) -print -quit )"
      else
        echo "ERROR: Unsupported operating system $( uname )" ; return 1
      fi
      depth=$[${depth}+1]
    done
    unset depth; unset mxdpt
    if [[ -z "${findgau}" ]]; then echo "ERROR: Could not find Gaussian directory"; return 1; fi
    if [ "${vrb}" = '-v' ]; then echo "Found folder ${findgau}"; fi
#   check whether the Gaussian executable is there
    for gau in {"gdv","g09"}; do
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
  elif [[ "${gau}" = "g09" ]]; then export g09root="${gauroot}"; fi
# load Gaussian bash environment but change the ulimit so we can debug
  if [[ ! -f "${gauroot}/${gau}/bsd/${gau}.profile" ]]; then echo "ERROR: File ${gau}.profile not found"; return 1; fi
  cp "${gauroot}/${gau}/bsd/${gau}.profile" ./"${gau}.profile.tmp"
  if   [[ "$( uname )" = "Linux"  ]]; then sed -i    's/ulimit\ -c\ 0/ulimit\ -S\ -c\ 0/' ./"${gau}.profile.tmp"
  elif [[ "$( uname )" = "Darwin" ]]; then sed -i '' 's/ulimit\ -c\ 0/ulimit\ -S\ -c\ 0/' ./"${gau}.profile.tmp"
  else echo "ERROR: Unsupported operating system $( uname )" ; return 1; fi
  source "${gau}.profile.tmp"
  rm -- "${gau}.profile.tmp"
# this works on medusa
  if [[ -d "/home/GauScr/" ]]; then export GAUSS_SCRDIR="/home/GauScr/"; fi
#
# -----------------------------
# BUILD THE COMPILATION COMMAND
# -----------------------------
# Define the compiler
  if [ -z "${PGI}" ]; then
    if [ "${vrb}" = '-v' ]; then echo "Loading PGI version ${pgv}"; fi
    setpgi "${pgv}"
#    module add pgi/14.7
  fi
# Build the mk command
  if [ -x "$( which mkcommand )" ]; then
    mkcommand # "${gauroot}"
    if [ $? -ne 0 ] || [ ! -f mkgau.tmp ]; then echo "ERROR: mkcommand failed"; return 1; fi
#   I change: FCN='${pgi} -Bstatic_pgi' into: FCN='${pgi} -Bstatic_pgi -Wl,-z,muldefs' 
#   to fix errors like "multiple definition of `ftn_allocated'" because the Internet told me to
    if   [[ "$( uname )" = "Linux"  ]]; then sed -i    's/-Bstatic_pgi/-Bstatic_pgi\ -Wl,-z,muldefs/' mkgau.tmp
    elif [[ "$( uname )" = "Darwin" ]]; then sed -i '' 's/-Bstatic_pgi/-Bstatic_pgi\ -Wl,-z,muldefs/' mkgau.tmp; fi
    alias mk="$( cat mkgau.tmp ); chmod o-rwx */*.o */*.exe"
    alias makec="$( cat mkgau.tmp )"
    rm -- mkgau.tmp
    if [ "${vrb}" = '-v' ]; then alias "mk"; fi
  else
    echo "WARNING: mkcommand utility not found, could not build mk command"
  fi
#
# unset all intermediate variables
  unset gau ; unset gauroot ; unset ver ; unset mac ; unset vrb ; unset pgv
  return 0
