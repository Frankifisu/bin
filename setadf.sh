#!/bin/bash
#
# * SET ADF ENVIRONMENT *
#
# This script must be sourced to export environment variables
# so we must return instead of exit
if [[ "$(basename -- "$0")" == "setadf.sh" ]]; then
  echo "Don't run $0, source it" >&2; exit 1
fi
#
  function usage {
    echo "Usage: . setadf.sh [version, e.g. 301]"
    echo '       -a adf : use ADF directory in path adf'
    echo '       -t     : generate ctags file $HOME/.tags (NYI)'
    echo '       -p PRC : use PRC processors'
    echo '       -v     : verbose mode'
    echo '       -h     : print this help and return'
    unset -f usage
    return 0
  }
#
# --------------------------
# CLEAN PREVIOUS ENVIRONMENT
# --------------------------
# check whether ADF is already set
  if [[ -n "${ADFHOME}" ]] ; then
    if [[ "${PATH}" = *'#'* ]] || [[ "${LD_LIBRARY_PATH}" = *'#'* ]]; then
      echo 'ERROR: Unable to remove previous ADF setup'; return 1
    else
      op='#'
    fi
#   epurate environment variables from the previous ADF settings
    if [[ -n "${ADFBIN}" ]]; then
      PATH="$( echo "${PATH}" | sed s${op}:${ADFBIN}${op}${op}g )"
      LD_LIBRARY_PATH="$( echo "${LD_LIBRARY_PATH}" | sed "s${op}${ADFBIN}:${op}${op}" )"
    fi
    unset op; unset ADFHOME ; unset ADFBIN ; unset ADFVER ; unset ADFRESOURCES ; unset SCMLICENSE ; unset SCM_TMPDIR 
  fi
#
# -------------
# PARSE OPTIONS
# -------------
  unset ADFHOME vrb tags prc
  ver="301"
# check for architecture type via hostname
  while [[ -n "${1}" ]]; do
    case "${1}" in
      -a | --adf  ) ADFHOME="${2}"; shift;;
      -t | --tags ) tags="tags"; usage ;;
      -p | --ppn  ) ppn='-p';;
      -v | --vrb  ) vrb='-v';;
      -h          ) usage ;;
      *           ) ver="${1}";;
    esac
    shift
  done
  unset -f usage
#
# --------------------
# DEFINE ADF DIRECTORY
# --------------------
# check whether a specific version has been requested
  if [[ -n "${ADFHOME}" ]]; then
    if [[ "$( uname )" = "Linux" ]]; then ADFHOME="$( readlink ${vrb} -e "${ADFHOME}" )"; fi
    if [[ ! -d ${ADFHOME} ]]; then echo "ERROR: ${ADFHOME} directory not found"; return 1; fi
    found="${ADFHOME}"
  else
#   crawl through the system searching for the desired ADF directory
    if [[ -z "${ver}" ]]; then echo "ERROR: ADF version not specified"; return 1; fi
    declare findme=""; declare -i depth=0 ; declare -i mxdpt=4
    downfrom="${HOME}/usr/local/adf"
    while [[ -z "${findme}" && "${depth}" -le "${mxdpt}" ]]; do
#     Start from / and work your way down by increasing depth
#     -prune is used to select which files or directories to skip
#     -print prints only the matching results and -quit prints only the first one
#     -o is the logical or and everything else has an implicit logical -a and
      exclude="-path /mnt -o -path /proc -o -path /private -o -path /bigdata -o -path /test_ocean -o -path /home -o -path /beegfs"
      gauname="-iname adf2019.*${ver} -o -iname adf*${ver}"
      if [[ "$( uname )" = "Linux" ]]; then
        findme="$( find "${downfrom}" -maxdepth "${depth}" -a \( ${exclude} -o ! -readable -o ! -executable \) -prune -o -type d -a \( ${gauname} \) -print -quit )"
      elif  [[ "$( uname )" = "Darwin" ]]; then
        findme="$( find "${downfrom}" -maxdepth "${depth}" -a \( ${exclude} -o ! -perm -g+rx                \) -prune -o -type d -a \( ${gauname} \) -print -quit )"
      else
        echo "ERROR: Unsupported operating system $( uname )" ; return 0
      fi
      depth=$[${depth}+1]
    done
    unset depth; unset mxdpt; unset ver
    if [[ -z "${findme}" ]]; then echo "${findme}" "ERROR: Could not find ADF directory"; return 1; fi
    if [ "${vrb}" = '-v' ]; then echo "Found directory ${findme}"; fi
    found="${findme}"
  fi
# Source ADF shell file
  export ADFVER="${found##*adf}"
  . ${found}/adfbashrc.sh
# check whether the ADF executable is there
  if [[ ! -x "${ADFBIN}/adf" ]]; then echo "WARNING: adf executable not found!"; fi
  if [ "${vrb}" = '-v' ]; then echo "Using ADF tree in ${ADFHOME}"; fi
#
# ------------------------
# DEFINE SCRATCH DIRECTORY
# ------------------------
  for trydir in "/tmp" "/scratch" "${HOME}/tmp" "${HOME}"; do
    if [[ -d "${trydir}" && -w "${trydir}" ]]; then
      trydir="${trydir}/${USER}/adf"
      if [[ ! -d "${trydir}" ]]; then mkdir -p -- "${trydir}" || continue; fi
      export SCM_TMPDIR="${trydir}"
      break
    fi
  done; unset trydir
#
# -----------------------------
# BUILD THE COMPILATION COMMAND
# -----------------------------
  ncpuavail=$( nproc )
  partone='cd "$ADFHOME" && "$ADFBIN"/foray'
  parttwo="-j ${ncpuavail} 2>&1 | tee mkadf.out ; cd -"
  alias mkadf="${partone} ${parttwo}"
  unset ncpuavail partone parttwo
  if [[ -f "${ADFHOME}/toskip.dat" ]]; then
    export FORAY_SKIP_TARGET_LIST="$( cat "${ADFHOME}/toskip.dat" )"
  fi
  if [[ -n "${ppn}" ]]; then
    export NSCM="${ppn}"
    if [ "${vrb}" = '-v' ]; then echo "Will use ${NSCM} processors"; fi
  fi
#
# ---------------
# SETUP TAGS FILE
# ---------------
  if [[ "${tags}" == "tags" ]]; then
    if [[ ! -x "$( command -v ctags )" ]]; then echo "ERROR: ctags command not found"; return 1; fi
    if [[ -f "${HOME}/.tags" ]]; then echo "WARNING: overwriting ${HOME}/.tags file"; fi
    if [[ "${vrb}" == '-v' ]]; then
      ctags -V -R -f "${HOME}/.tags" ${ADFHOME}
    else
      ctags    -R -f "${HOME}/.tags" ${ADFHOME}
    fi
    if ! grep -q tags ${HOME}/.vimrc; then echo "WARNING: remember to reference ${HOME}/.tags file in .vimrc"; fi
  fi
#
# unset all intermediate variables
  unset vrb ; unset tags
  return 0
