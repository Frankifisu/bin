#!/bin/bash
#
# * SET AMS ENVIRONMENT *
#
# This script must be sourced to export environment variables
# so we must return instead of exit
if [[ "$(basename -- "$0")" == "setams.sh" ]]; then
  echo "Don't run $0, source it" >&2; exit 1
fi
#
  function usage {
    echo "Usage: . setams.sh [version, e.g. trunk]"
    echo '       -a ams : use AMS directory in path ams'
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
# check whether AMS is already set
  if [[ -n "${AMSHOME}" || -n "${AMSHOME}" ]] ; then
    if [[ "${PATH}" = *'#'* ]] || [[ "${LD_LIBRARY_PATH}" = *'#'* ]]; then
      echo 'ERROR: Unable to remove previous AMS setup'; return 1
    else
      op='#'
    fi
#   epurate environment variables from the previous AMS settings
    if [[ -n "${AMSBIN}" ]]; then
      PATH="$( echo "${PATH}" | sed s${op}:${AMSBIN}${op}${op}g )"
      LD_LIBRARY_PATH="$( echo "${LD_LIBRARY_PATH}" | sed "s${op}${AMSBIN}:${op}${op}" )"
    fi
    if [[ -n "${AMSBIN}" ]]; then
      PATH="$( echo "${PATH}" | sed s${op}:${AMSBIN}${op}${op}g )"
      LD_LIBRARY_PATH="$( echo "${LD_LIBRARY_PATH}" | sed "s${op}${AMSBIN}:${op}${op}" )"
    fi
    unset op; unset AMSHOME ; unset AMSBIN ; unset AMSVER ; unset AMSRESOURCES ; unset SCM_TMPDIR ; unset AMSVER ; unset AMSBIN ; unset AMSHOME
  fi
#
# -------------
# PARSE OPTIONS
# -------------
  unset AMSHOME vrb tags prc
  ver="None"
# check for architecture type via hostname
  while [[ -n "${1}" ]]; do
    case "${1}" in
      -a | --ams  ) AMSHOME="${2}"; shift;;
      -t | --tags ) tags="tags"; usage ;;
      -p | --ppn  ) ppn='-p';;
      -v | --vrb  ) vrb='-v';;
      -h          ) usage ; return 0 ;;
      *           ) ver="${1}";;
    esac
    shift
  done
  if [[ "${ver}" == 'None' && -z "${AMSHOME}" ]] ; then usage ; return 0 ; fi
  unset -f usage
#
# --------------------
# DEFINE AMS DIRECTORY
# --------------------
# check whether a specific version has been requested
  if [[ -n "${AMSHOME}" ]]; then
    if [[ "$( uname )" = "Linux" ]]; then
      AMSHOME="$( readlink ${vrb} -e "${AMSHOME}" )"
    fi
    if [[ ! -d ${AMSHOME} ]]; then echo "ERROR: AMSHOME directory not found"; return 1; fi
    found="${AMSHOME}"
  else
#   crawl through the system searching for the desired AMS directory
    if [[ -z "${ver}" ]]; then echo "ERROR: AMS version not specified"; return 1; fi
    declare findme=""; declare -i depth=0 ; declare -i mxdpt=4
    for trydir in "/home/egidi/usr/local/ams" "/home/fegidi/usr/local/ams" "/home/franco/usr/local/ams" "${HOME}/usr/local/ams" "${HOME}"; do
      if [[ -d ${trydir} ]]; then downfrom="${trydir}"; break; fi
    done; unset trydir
    while [[ -z "${findme}" && "${depth}" -le "${mxdpt}" ]]; do
#     Start from / and work your way down by increasing depth
#     -prune is used to select which files or directories to skip
#     -print prints only the matching results and -quit prints only the first one
#     -o is the logical or and everything else has an implicit logical -a and
      exclude="-path /mnt -o -path /proc -o -path /private -o -path /bigdata -o -path /test_ocean -o -path /home -o -path /beegfs"
      amsname="-iname ams20*.*${ver} -o -iname ams*${ver}"
      if [[ "$( uname )" = "Linux" ]]; then
        findme="$( find "${downfrom}" -maxdepth "${depth}" -a \( ${exclude} -o ! -readable -o ! -executable \) -prune -o -type d -a \( ${amsname} \) -print -quit )"
      elif  [[ "$( uname )" = "Darwin" ]]; then
        findme="$( find "${downfrom}" -maxdepth "${depth}" -a \( ${exclude} -o ! -perm -g+rx                \) -prune -o -type d -a \( ${amsname} \) -print -quit )"
      else
        echo "ERROR: Unsupported operating system $( uname )" ; return 0
      fi
      depth=$[${depth}+1]
    done
    unset depth; unset mxdpt; unset ver
    if [[ -z "${findme}" ]]; then echo "${findme}" "ERROR: Could not find AMS directory"; return 1; fi
    if [ "${vrb}" = '-v' ]; then echo "Found directory ${findme}"; fi
    found="${findme}"
  fi
# Source AMS shell file
  export AMSVER="${found##*ams}"
  . ${found}/amsbashrc.sh
# check whether the AMS executable is there
  if [[ ! -x "${AMSBIN}/ams" ]]; then echo "WARNING: ams executable not found!"; fi
  if [ "${vrb}" = '-v' ]; then echo "Using AMS tree in ${AMSHOME}"; fi
  #AMSPYTHONVER='python3.8'
  #if [[ -d ${AMSHOME}/bin/${AMSPYTHONVER} ]]; then
  #  export SCM_PYTHONPATH="${AMSHOME}/bin/python3.8/"
  #else
  #  echo "WARNING: ${AMSPYTHONVER} not found in ${AMSHOME}/bin"
  #fi
  if [[ -d ${HOME}/.local/lib/python3.9/site-packages/lammps ]]; then
    #export SCM_PYTHONPATH="${HOME}/.local/lib/python3.9/site-packages/lammps"
    export SCM_PYTHONPATH=${SCM_PYTHONPATH}:"${HOME}/.local/lib/python3.9/site-packages/lammps/":"${HOME}/.local/lib/python3.9/":"${HOME}/usr/local/lammps/lammps-23Jun2022/python/"
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:"${HOME}/.local/lib/python3.9/site-packages/lammps":"${HOME}/usr/local/lammps/lammps-23Jun2022/src/"
  else
    echo "WARNING: LAMMPS not found"
  fi
  #export PYTHONPATH="${AMSHOME}/scripting":"${SCM_PYTHONPATH}":"${AMSHOME}/bin/${AMSPYTHONVER}":${PYTHONPATH}
#
# ------------------------
# DEFINE SCRATCH DIRECTORY
# ------------------------
  for trydir in "/scratch" "/tmp" "${HOME}/tmp" "${HOME}"; do
    if [[ -d "${trydir}" ]]; then
      if [[ -d "${trydir}/${USER}" && -w "${trydir}/${USER}" ]]; then
        :
      elif [[ -w "${trydir}" ]]; then
        :
      else
        continue
      fi
      trydir="${trydir}/${USER}/ams"
      if [[ ! -d "${trydir}" ]]; then mkdir -p -- "${trydir}" || continue ; fi
      export SCM_TMPDIR="${trydir}"
      break
    fi
  done; unset trydir
#
# -----------------------------
# BUILD THE COMPILATION COMMAND
# -----------------------------
  ncpuavail=$( nproc )
  if [[ "${ncpuavail}" > 8 ]]; then ncpuavail="8"; fi
  partone='cd "$AMSHOME" && "$AMSBIN"/foray'
  parttwo="-j ${ncpuavail} 2>&1 | tee mkams.out ; cd -"
  alias mkams="${partone} ${parttwo}"
  alias runtest="${AMSHOME}/Utils/run_test"
  alias runwhere="${AMSHOME}/Utils/run_where"
  unset ncpuavail partone parttwo
  if [[ -f "${AMSHOME}/toskip.dat" ]]; then
    export FORAY_SKIP_TARGET_LIST="$( cat "${AMSHOME}/toskip.dat" )"
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
      ctags -V -R -f "${HOME}/.tags" ${AMSHOME}
    else
      ctags    -R -f "${HOME}/.tags" ${AMSHOME}
    fi
    if ! grep -q tags ${HOME}/.vimrc; then echo "WARNING: remember to reference ${HOME}/.tags file in .vimrc"; fi
  fi
#
# unset all intermediate variables
  unset vrb ; unset tags
  return 0
