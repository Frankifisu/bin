#!/bin/bash
#
# ==================================
# = MY PERSONAL BASHRC ENVIRONMENT =
# ==================================
#
# -----------
# SHELL PATHS
# -----------
# My Run Commands directory
  myrc="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# PATH
  for addpath in "${HOME}/bin" "${HOME}/usr/bin"; do
    if [[ -d "${addpath}" ]]; then
      export PATH="${addpath}:${PATH}"; fi
  done; unset ldpath
# LD_LIBRARY_PATH
  for addpath in "/lib" "/lib64" "/usr/lib" "/usr/lib64"; do
    if [[ -d ${addpath} ]]; then
      export LD_LIBRARY_PATH="${addpath}:${LD_LIBRARY_PATH}"; fi
  done; unset ldpath
#
# -------
# HISTORY
# -------
# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
  export HISTCONTROL=ignoreboth
  export HISTSIZE=10000
  export HISTFILESIZE=20000
# append to the history file, don't overwrite it
  shopt -s histappend
#
# ----------------
# SHELL APPEARENCE
# ----------------
# Colors
  export CLICOLOR=1
  export LSCOLORS=GxFxCxDxBxegedabagaced
# Check window size after commands and update LINES and COLUMNS.
  shopt -s checkwinsize
# enable color support of ls and also add handy aliases
  if [[ -x /usr/bin/dircolors ]]; then
    test -r ${HOME}/.dircolors && eval "$( dircolors -b ~/.dircolors )" || eval "$( dircolors -b )"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
  fi
#
# --------------
# SHELL BEHAVIOR
# --------------
# default permissions
  umask 'u=rwx,g=rx,o='
# Expand $directories removing the annoying behavior of escaping the dollar sign
#  shopt -s direxpand
# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#  shopt -s globstar
# Directory for temporary files
  for trydir in "/tmp" "/var/tmp" "${HOME}/tmp" "${HOME}/usr/tmp" "${HOME}"; do
    if [[ -d ${trydir} ]]; then export TMPDIR="${tmpdir}"; break; fi
  done; unset trydir
#
# -------------
# USER COMMANDS
# -------------
  alias bashrc="vim -- ${myrc}/.bashrc"
  alias rebash="source -- ${myrc}/.bashrc"
  alias vimrc="vim -- .vimrc"
  alias vimvs="vim -O"
  alias cd..="cd .."
  alias la="ls -A"
  alias ll="ls -lh"
  alias ltrh="ls -ltrah"
  alias grepi="grep -i"
  if [[ -x $( command -v rename.ul ) ]]; then alias rename="rename.ul"; fi
  if [[ -x $( command -v qstat ) ]]; then alias qme="qstat -w -u ${USER} -n -1"; fi
  alias mysubs="if [[ -e ${HOME}/.mysubs ]]; then vim '+normal G' ${HOME}/.mysubs; fi"
  if [[ -d "/bigdata/${USER}" ]]; then export BIGDATA="/bigdata/${USER}"; fi
# functions
  prev () {
    if [[ "${#}" -eq 0 ]]; then echo "Usage: prev command"; return 1 ; fi
    history | head -n -1 | grep ${1}
  }
  vimcmp () {
    if [[ "${#}" -ne 2 ]]; then echo "Usage: vimcmp file1 file2 "; return 1 ; fi
    if [[ ! -r "${1}" ]]; then echo "ERROR: Can't read file ${1}"; return 1 ; fi
    if [[ ! -r "${2}" ]]; then echo "ERROR: Can't read file ${2}"; return 1 ; fi
    if [[ ! "$( file -b "${1}" )" == *"text"* ]] && [[ ! "$( file -b "${1}" )" == *"program"* ]]; then echo "File ${1} not a text file"; return 1; fi
    if [[ ! "$( file -b "${2}" )" == *"text"* ]] && [[ ! "$( file -b "${2}" )" == *"program"* ]]; then echo "File ${2} not a text file"; return 1; fi
    cmp -s "${1}" "${2}" && echo "No difference between ${1} and ${2}" || vimdiff "${1}" "${2}"
    return 0
  }
  swap () {
    if [[ "${#}" -ne 2 ]]; then echo 'ERROR: two arguments needed'; return 1; fi
    if [[ "${1}" == "${2}" ]]; then echo 'ERROR: different arguments needed'; return 1; fi
    unset todelete
    if [[ -d "${1}" ]] && [[ -d "${2}" ]]; then todelete="$( mktemp -d )"; fi
    if [[ -f "${1}" ]] && [[ -f "${2}" ]]; then todelete="$( mktemp )"; fi
    if [[ -z "${todelete}" ]]; then echo 'ERROR: file inconsistency'; return 1; fi
    mv -T -- "${1}" "${todelete}" && mv -T -- "${2}" "${1}" && mv -T -- "${todelete}" "${2}"
    return 0
  }
  trova () {
# Use of regular expressions (regex):
# .  == Something (whatever)
# *  == preceding character any number of times (including 0)
# .* == Anything (including nothing)
# \  == take the following literally
    if [ "${#}" -eq 0 ]; then echo 'Usage: trova [directory] object'; return 0; fi
    if [[ "$( uname )" = "Linux" ]]; then
      perm="-path /private -o ! -readable"
    elif  [[ "$( uname )" = "Darwin" ]]; then
      perm="-path /private -o ! -perm -g+r"
    else
      echo "ERROR: Unsopported operating system $( uname ) " ; return 1
    fi
#    dove="${1-${HOME}}"
    if [ "${#}" -eq 1 ]; then
      dove="${HOME}"
    else
      dove="${1}"; shift
    fi
    find "${dove}" \( ${perm} \) -prune -o \( ! -regex '.*/\..*/..*' \) -a -iname "*${1}*" -print
    unset perm; unset dove
#     This matches Anything/.Anything/SomethingAnything
#     so it includes hidden files but does not explore hidden directories
#     -prune is true if the preceding is a directory and does not descend it 
#     and P1 -o P2 is the logical or and does not evaluate P2 if P1 is true
  }
#
# -----
# HOSTS
# -----
# Generic secure connection function
  sconnect () {
    if [[ ${#} -lt 2 ]]; then echo "ERROR: Remote user and host required in sconnect"; return 1; fi
    local remote_user="${1}"; shift
    local remote_host="${1}"; shift
    if [[ "${#}" -eq 0 ]]; then
      ssh ${remote_user}@${remote_host}
    else
      if ssh ${remote_user}@${remote_host} '[ -d ~/tmp ]'; then dest_dir="~/tmp"; else dest_dir="~"; fi
      scp -p "$@" ${remote_user}@${remote_host}:"${dest_dir}"
    fi
  }
# Connect to avocado
  office () {
    if [[ "$( hostname )" = "avocado" ]]; then echo "ERROR: Already on avocado"; return 1; fi
    export officeip=192.168.253.208
    sconnect "franco" "${officeip}" ${@}
  }
# Connect to avogadro
  avogadro () {
#   This function sends the IP into the .bashrc of a remote host
#   before performing a ssh or scp operation.
#   It expects the remote host .bashrc to have a function like:
    if [[ "$( hostname )" = "avogadro"* ]]; then echo "ERROR: Already on avogadro"; return 1; fi
    myIP="$( ip route get 1 | head -n 1 | grab 7 )"
    local remote_user="f.egidi"
    local remote_host="avogadro.sns.it"
    ipwrite="$( echo ssh ${remote_user}@${remote_host} \\"sed -i \'/^\\\s*export\ officeip=*/c\\\ \\\ \\\ \\\ export\ officeip=${myIP}\' /home/${remote_user}/bin/.bashrc\\" )"
    eval ${ipwrite}
    sconnect ${remote_user} ${remote_host} ${@}
  }
  cineca () {
    sconnect "fegidi00" "login.galileo.cineca.it" ${@}
  }
  alias galileo="cineca"
  natta () {
    sconnect "f.egidi" "natta04.sns.it" ${@}
  }
  artemis () {
    sconnect "fegidi" "artemis.chem.washington.edu" ${@}
  }
#
# ------
# DALTON
# ------
# alias Dalton="~/Dalton/jobs/run.sh"
# PATH="/home/j.bloino/software/cmake-2.8.12.1/bin:${PATH}"
# MANPATH="/home/j.bloino/software/cmake-2.8.12.1/man:${MANPATH}"
#
# --------
# GAUSSIAN
# --------
  alias setgau=". setgaussian.sh"
  shopt -s extglob
  convchk () {
    if [[ ${#} -ne 3 ]]; then echo "USAGE: convchk a03 i04p file.chk"; fi
    local uno="${1}"; local due="${2}"
#    if [[ "${uno}" = "fq"  ]]; then uno="-g /home/f.egidi/.gdvfq"; fi
#    if [[ "${due}" = "fq"  ]]; then due="-g /home/f.egidi/.gdvfq"; fi
#    if [[ "${uno}" = "rel" ]]; then uno="-g /home/f.egidi/.gdvi04p"; fi
#    if [[ "${due}" = "rel" ]]; then due="-g /home/f.egidi/.gdvi04p"; fi
    setgau ${uno} || return
    formchk "${3}" temp.fchk
    setgau ${due} || return
    unfchk temp.fchk "${3}"
    rm -- temp.fchk
  }
  compile () {
    if [[ ! -x $( command  -v qsub ) ]]; then echo "ERROR: No qsub command"; return 1; fi
    local jobnam="compiling"
    while [[ -n "${1}" ]]; do
      case "${1}" in
        -q     ) queue="${2}"; shift;;
        -v     ) vrb="-v";;
        -N     ) jobnam="${2}";;
        *      ) echo "ERROR: unrecognized option ${1}"; return 1;;
      esac; shift
    done
    if [[ -z "${queue}" ]]; then queue="q02zewail"; fi
    qsub -I -N "${jobnam}" -q ${queue}
  }
#  subfq () {
#    unset chk ; unset coda ; unset working ; unset subarch
#    if [[ "${#}" -eq 0 ]]; then echo "USAGE: subfq -q q02curie input.com"; return 1; fi
#    grep -sq -i -e '%Chk' -e '%OldChk' -- ${@} && chk="-k chk"
#    if [[ "${@}" = *q*pople* ]]; then echo "ERROR: invalid queue"; return 1; fi
#    if [[ "${@}" = *-giulia* ]]; then gauwrkdir="/home/g.logerfo/tesi/working/lavoro"; else gauwrkdir="/home/f.egidi/working/newgiulia"; fi
#    opts=${@/"-giulia"}
#    subgau ${chk} -w "${gauwrkdir}" -g ${HOME}/.gdvfq/gdv ${opts}
#  }
#  subrel () {
#    unset chk ; unset coda ; unset working ; unset subarch
#    if [[ "${#}" -eq 0 ]]; then echo "USAGE: subrel -q q02curie input.com"; return 1; fi
#    grep -sq -i -e '%Chk' -e '%OldChk' -- ${@} && chk="-k chk"
#    if [[ "${@}" = *q*pople* ]]; then echo "ERROR: invalid queue"; return 1;
#    elif [[ "${@}" = *q*zewail* ]] || [[ "${@}" = *q*kohn* ]]; then subarch="/intel64-nehalem";
#    elif [[ ! "${@}" = *"-q"* ]]; then coda="-q q02curie"; fi
#    working="${HOME}/working/dft${subarch}"
#    if [[ "${@}" = *"-test"* ]]; then working="${HOME}/working/socouplings"; fi
#    if [[ "${@}" = *"-cifre"* ]]; then working="${HOME}/working/cifre${subarch}"; fi
#    opts=${@/"-cifre"}
#    opts=${opts/"-test"}
#    subgau ${chk} -w ${working} -g ${HOME}/.gdvi04p${subarch}/gdv ${coda} ${opts}
#    if [[ "${@}" = *"-v"* ]]; then echo "subgau ${chk} -w ${working} -g ${HOME}/.gdvi04p/gdv ${coda} ${opts} "; fi
#    unset chk ; unset coda ; unset working ; unset subarch
#  }
#  subnri () {
#    unset chk ; unset coda
#    if [[ "${#}" -eq 0 ]]; then echo "USAGE: subnri -q q02curie input.com"; return 1; fi
#    grep -sq -i -e '%Chk' -e '%OldChk' -- ${@} && chk="-k chk"
#    if [[ "${@}" = *q*zewail* ]] || [[ "${@}" = *q*kohn* ]] || [[ "${@}" = *q*pople* ]]; then echo "ERROR: invalid queue"; return 1;
#    elif [[ ! "${@}" = *"-q"* ]]; then coda="-q q02curie"; fi
#    subgau ${chk} -g /home/a.baiardi/Gaussian/gdv.i10p/gdv -w /home/a.baiardi/working_i10p/working_phospho/ ${coda} ${@}
#  }
#  subcur () {
#    unset chk ; unset coda
#    if [[ "${#}" -eq 0 ]]; then echo "USAGE: subcur -q q02curie input.com"; return 1; fi
#    grep -sq -i -e '%Chk' -- ${@} && chk="-k chk"
#    if [[ "${@}" = *q*pople* ]]; then echo "ERROR: invalid queue"; return 1;
#    elif [[ ! "${@}" = *"-q"* ]]; then coda="-q q02zewail"; fi
#    subgau ${chk} -g /home/f.egidi/.gdvh10p/gdv -w /home/f.egidi/working/current/ ${coda} ${@}
#    if [[ "${@}" = *"-v"* ]]; then echo "subgau ${chk} -g /home/f.egidi/.gdvh10p/gdv -w /home/f.egidi/working/current/ ${coda} ${@}"; fi
#  }
#  subalb () {
#    unset chk ; unset coda
#    if [[ "${#}" -eq 0 ]]; then echo "USAGE: subalb -q q02curie input.com"; return 1; fi
#    grep -sq -i -e '%Chk' -- ${@} && chk="-k chk"
#    if [[ "${@}" = *q*zewail* ]] || [[ "${@}" = *q*kohn* ]] || [[ "${@}" = *q*pople* ]]; then echo "ERROR: invalid queue"; return 1;
#    elif [[ ! "${@}" = *"-q"* ]]; then coda="-q q02curie"; fi
#    subgau ${chk} -g /home/a.baiardi/Gaussian/gdv.i09/gdv ${coda} ${@}
#    if [[ "${@}" = *"-v"* ]]; then echo "subgau ${chk} -g /home/a.baiardi/Gaussian/gdv.i09/gdv ${coda} ${@}"; fi
#  }
  rmjunk () {
#    unset revert
#    if [ `shopt -q extglob | echo $?` -eq 1 ]; then revert=1 ; fi
#    shopt -s extglob
    local -a listrm=( '*.o+([0-9])' '*.e+([0-9])' 'Gau-+([0-9]).*' '*.tmp' )
    for targetrm in ${listrm[*]}; do
      if [[ ! -f "${targetrm}" ]]; then continue; fi
      if [[ "${1}" = '-z' ]] && [[ -s ${targetrm} ]]; then continue ; fi
      rm -- "${targetrm}"
    done
    unset targetrm
#    if [ ${revert} -eq 1 ]; then shopt -u extglob; fi
  }
# Clean working compilation
  mkclean () {
    local -a listrm=( '*/*.o' '*/*.exe' )
    for targetrm in ${listrm[*]}; do
      if [ ! -f "${targetrm}" ]; then continue; fi
      rm -- "${targetrm}"
    done
    unset targetrm
  }
# Clean Gaussian Scratch
  cleanscr () {
    if [[ -z "${GAUSS_SCRDIR}" ]]; then echo "GAUSS_SCRDIR not defined"; return 1; fi
    for i in "${GAUSS_SCRDIR}"/* ; do if [[ "$( stat -c %U "${i}" )" = ${USER} ]]; then rm -- "${i}"; fi; done
  }
# Generate cube using cubegen
  cube () {
    usage () {
      echo "USAGE: cube [-o mycub] [-s S] [-n nproc] -f name.fchk NN [MM ...]"
      echo "         -o mycub : sets the output cube base name as mycub"
      echo "         -p npts  : sets the number of points per side of the cube"
      echo "         -n nproc : use nproc processors"
      echo "         -f file  : specifies the .fchk input file"
      echo "         -d type  : does density of specified type (SCF, MP2, ...) instead of MOs"
      echo "         -s {A,B} : sets the orbital spin as either A or B, or requests spin density if -d is set"
      echo "         -v       : verbose mode"
      echo "         NN MM... : lists the orbital numbers"
      unset -f usage
    }
    if [ "${#}" -lt 2 ]; then usage; return 0; fi
    if [[ -z "${gdvroot}" ]] && [[ -z "${g09root}" ]] && [[ -z "${g16root}" ]]; then echo "ERROR: Gaussian environment not defined"; return 1; fi
    local vrb="" outcub="" dens="" spin=""; local -i nproc=0; local -a orbs
    unset npts; unset cubpath
#    shopt -s extglob
    while [ -n "${1}" ]; do
      case "${1}" in
        *.fchk ) file="${1}";;
        -f     ) file="${2}"; shift;;
      +([0-9]) ) orbs=( "${orbs[@]}" "${1}" );;
        -o     ) outcub="${2}"; shift;;
        -p     ) npts="${2}"; shift;;
        -d     ) dens="${2}"; shift;;
        -s     ) spin="${2}"; shift;;
        -n     ) nproc="${2}"; shift;;
        -w     ) cubpath="${2}"; shift;;
        -vcd   ) ;;
        -v     ) vrb="-v";;
        *      ) echo "ERROR: unrecognized option ${1}"; return 1;;
      esac; shift
    done
    file="${file%fchk}"
    if [[ ! -f "${file}fchk" ]]; then echo "ERROR: Cannot find file ${file}fchk"; return 1; fi
    if [[ -z "${outcub}" ]]; then outcub="${file}"; fi
    if [[ -n ${dens} ]]; then
      if [[ -z "${spin}" ]]; then
        comando="$( echo ${cubpath}/cubegen ${nproc} Density="${dens}" "${file}fchk" "${outcub}dens.cube" )"
      else
        comando="$( echo ${cubpath}/cubegen ${nproc}    Spin="${dens}" "${file}fchk" "${outcub}spin.cube" )"
      fi
      if [ "${vrb}" = "-v" ]; then echo " ${comando}"; fi
      eval ${comando}
    elif [[ "${#orbs}" -gt 0 ]]; then
      for orb in ${orbs[@]}; do
        comando="$( echo ${cubpath}/cubegen ${nproc} ${spin}MO="${orb}" "${file}fchk" "${outcub}${spin}${orb}.cube" ${npts} )"
        if [ "${vrb}" = "-v" ]; then echo " ${comando}"; fi
        eval ${comando}
      done
    else
      echo "ERROR: Target orbitals or density not specified"
    fi
#    unset outcub; unset spin; unset dens; unset nproc; unset orbs; unset file; unset outcub; unset comando; unset npts
  }
# GaussView
  GV_DIR="${HOME}/usr/share/GaussView/gv"
  if [[ -d "${GV_DIR}" ]]; then
    alias gview="${GV_DIR}/gview.sh &"
  else
    unset GV_DIR
  fi
#
# ---
# xtb
# ---
  if [[ -d ${HOME}/local/xtb ]]; then
    export XTBHOME="${HOME}/local/xtb"
    if [[ -x "${XTBHOME}/Config_xtb_env.bash" ]]; then
      source "${XTBHOME}/Config_xtb_env.bash"
    else
      echo 'ERROR: Cannot configure xtb'
    fi
  fi
#
# --
# eT
# --
  export LIBINT_DATA_PATH="/usr/local/libint/2.4.2/share/libint/2.4.2/basis"
  export SAD_ET_DIR="${HOME}/usr/local/eT/src/molecular_system/sad"

# ------
# GAMESS
# ------
#  gamess () {
#    alias gms="~/SERS/compsource/seqgms_stef $1 >& $1.log &"
#    export GMS_PATH="~/SERS/compsource/" # compilation config
#    export GMS_TARGET="linux64" # machine type
#    export GMS_FORTRAN="gfortran" # Fortran compiler setup
#    export GMS_MATHLIB=$LD_LIBRARY_PATH # math library setup
#    export GMS_DDI_COMM="sockets" # parallel message passing model setup
#  }
#
# NB: float comparisons may be done like this
# if [ $( echo " ${foo} < ${bar}" | bc ) -eq 1 ]

#
#  getdips () {
#    if [[ "${#}" -ne 1 ]]; then echo "Usage: getdips file.dat"; return 1 ; fi
#    grep 'DEDip' "${1}" > "edip_${1}"
#    grep 'DMDip' "${1}" > "mdip_${1}"
#    for dipfile in "edip_${1}" "mdip_${1}"; do
#      sed -i 's/.$//' ${dipfile}
#      sed -i 's/^........//' ${dipfile}
#    done
#    return 0
#  }
#
  alias pygior='/home/g.mancini/pkg/python27/bin/python2.7'
