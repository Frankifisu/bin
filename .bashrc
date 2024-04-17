#!/bin/bash
#
# ==================================
# = MY PERSONAL BASHRC ENVIRONMENT =
# ==================================
# This file should be sourced from ~/.bashrc which can be kept
# almost as the default found in /etc/skel/.bashrc
#
# -----------
# SHELL PATHS
# -----------
# My Run Commands directory
  myrc="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# PATH
  for addpath in "${HOME}/bin" "${HOME}/usr/bin"; do
    if [[ -d "${addpath}" ]]; then
      export PATH="${addpath}:${PATH}"; export PYTHONPATH="${addpath}:${PYTHONPATH}"; fi
  done; unset addpath
# LD_LIBRARY_PATH
  for addpath in "/lib" "/lib64" "/usr/lib" "/usr/lib64" "/usr/lib/x86_64-linux-gnu"; do
    if [[ -d "${addpath}" || -L "${addpath}" ]]; then
      export LD_LIBRARY_PATH="${addpath}:${LD_LIBRARY_PATH}"; fi
  done; unset addpath
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
  shopt -s direxpand
# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#  shopt -s globstar
# Directory for temporary files
  for trydir in "/tmp" "/var/tmp" "${HOME}/tmp" "${HOME}/usr/tmp" "${HOME}"; do
    if [[ -d ${trydir} ]]; then export TMPDIR="${trydir}"; break; fi
  done; unset trydir
#
# -------------
# USER COMMANDS
# -------------
  alias bashrc="vim -- ${myrc}/.bashrc"
  alias rebash="source -- ${myrc}/.bashrc"
  alias vimrc="vim -- ${myrc}/.vimrc"
  alias vimvs="vim -O"
  alias cd..="cd .."
  alias la="ls -A"
  alias ll="ls -lh"
  alias ltrh="ls -ltrah"
  alias grepi="grep -i"
  alias myip="ip route get 1 | head -n 1 | grab 7"
  if [[ -x $( command -v python3 ) ]]; then alias python="python3"; fi
  if [[ -x $( command -v helpy.py ) ]]; then alias helpy="helpy.py"; fi
  if [[ -x $( command -v rename.ul ) ]]; then alias rename="rename.ul"; fi
  apri () {
    if [[ ${#} -eq 0 ]]; then
       xdg-open .
    else
      for fil in ${@}; do
        if [[ -r "${fil}" ]]; then
          xdg-open "${fil}"
        else
          echo "ERROR: ${1} not readable"
        fi
      done; unset fil
    fi
  }
  svndiff () {
    svn diff ${@} | colordiff
  }
  qme () {
    if [[ -x $( command -v squeue ) ]]; then
      squeue -u "${USER}"
    elif [[ -x $( command -v qstat ) ]]; then
      qstat -w -u ${USER} -n -1
    else
      top -b -u ${USER} -E g -n 1 -s -w | head -n $(($(nproc)+7)) | tail -n $(($(nproc)+1))
    fi
  }
  #if   [[ -x $( command -v squeue ) ]]; then alias qme="squeue -u egidi";
  #elif [[ -x $( command -v qstat ) ]]; then alias qme="qstat -w -u ${USER} -n -1"; fi
  alias mysubs="if [[ -e ${HOME}/.mysubs ]]; then vim '+normal G' ${HOME}/.mysubs; fi"
  if [[ -d "/bigdata/${USER}" ]]; then export BIGDATA="/bigdata/${USER}"; fi
# functions
  dropbox () {
   local dropboxdir="${HOME}/.dropbox-dist"
   local dropboxd="${dropboxdir}/dropboxd"
   if [[ -x ${dropboxd} ]]; then
     nohup ${dropboxd} 2>&1 > ${dropboxdir}/dropbox.out &
   else
     echo "Cannot find excecutable ${dropboxd}"
   fi
  }
#
  prev () {
    if [[ "${#}" -eq 0 ]]; then echo "Usage: prev command"; return 1 ; fi
    history | head -n -1 | grep -i ${1}
  }
#
  getline () {
    if [[ ${#} -lt 1 ]]; then echo "Usage: getline 3 file "; return 1 ; fi
    local -i linenum
    linenum=${1}; shift
    if [[ ${#} -ge 1 ]]; then
      for file in ${@}; do
        head -n ${linenum} "${file}" | tail -n 1
      done
    else
      local -i count=0
      while read -t 0.1 -e var; do # -t aborts read after specified number of seconds
        count=$(( count+1 ))
        if [[ ${count} -eq ${linenum} ]]; then echo ${var}; break; fi
      done
    fi
  }
#
  vimcmp () {
    if [[ "${#}" -ne 2 ]]; then echo "Usage: vimcmp file1 file2 "; return 1 ; fi
    for arg in ${@}; do
      if [[ ! -r "${arg}" ]]; then echo "ERROR: Can't read file ${arg}"; return 1 ; fi
      if [[ ! "$( file -b "${arg}" )" == *"text"* ]] && [[ ! "$( file -b "${arg}" )" == *"program"* ]]; then echo "File ${arg} not a text file"; return 1; fi
    done
    cmp -s "${1}" "${2}" && echo "No difference between ${1} and ${2}" || vimdiff "${1}" "${2}"
    return 0
  }
#
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
#
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
  esplora () {
    ext=''
    case ${#} in
      0 ) echo "USAGE: esplora . fqqm .run"; return 0 ;;
      2 ) sotto="${1}" ; cosa="${2}";;
      3 ) sotto="${1}" ; cosa="${2}"; ext="${3}";;
      * ) echo "ERROR: wrong number of arguments"; return 1;;
    esac
    
    tmpfile="$( mktemp /tmp/trovams.XXXXXX )"
    trova "${sotto}" "." > $tmpfile
    for file in $( cat "${tmpfile}" ); do
      if [[ "$( file -b "${file}" )" == *"directory"* ]] ; then continue; fi
      if [[ "${file}" == *kf ]] ; then continue; fi
      if [[ "${file}" == *.t21 ]] ; then continue; fi
      if [[ "${file}" == *.ams ]] ; then continue; fi
      if [[ "${file}" == *.pyc ]] ; then continue; fi
      if [[ "${file}" == *.svg ]] ; then continue; fi
      if [[ "${file}" == *.png ]] ; then continue; fi
      if [[ "${file}" == *.gz  ]] ; then continue; fi
      if [[ "${file}" == *.js  ]] ; then continue; fi
      if [[ "${file}" == *.ipynb  ]] ; then continue; fi
      if [[ "${file}" == *.drawio ]] ; then continue; fi
      if [[ "${file}" != *${ext} ]] ; then continue ; fi
      grepi "${cosa}" "${file}" && echo -e '>>>' "${file}" "\n"
    done
    rm -- "${tmpfile}"

    unset cosa; unset sotto; unset tmpfile; unset file
 }
#
  trovams () {
    if [[ -z ${AMSHOME} ]]; then echo "AMS environment undefined"; return 1; fi

    ext=''
    case ${#} in
      0   ) echo "USAGE: trovams src fqqm .run"; return 0 ;;
      1   ) sotto="${AMSHOME}/src" ; cosa="${1}" ;; 
      2|3 ) sotto="${AMSHOME}/${1}" ; shift ;;
      * ) echo "ERROR: wrong number of arguments"; return 1;;
    esac

    esplora "${sotto}" ${@}

    unset sotto
 }
#
#  trovams () {
#    if [[ -z ${AMSHOME} ]]; then echo "AMS environment undefined"; return 1; fi
#    
#    ext=''
#    case ${#} in
#      0 ) echo "USAGE: trovams src fqqm .run"; return 0 ;;
#      1 ) sotto="src" ; cosa="${1}" ;; 
#      2 ) sotto="${1}" ; cosa="${2}";;
#      3 ) sotto="${1}" ; cosa="${2}"; ext="${3}";;
#      * ) echo "ERROR: too many arguments"; return 1;;
#    esac
#    
#    if [[ ! -d "$AMSHOME/${sotto}" ]]; then
#      echo "$AMSHOME/${sotto} is not a valid directory"; return 1
#    fi
#    
#    tmpfile="$( mktemp /tmp/trovams.XXXXXX )"
#    trova "$AMSHOME/${sotto}" "." > $tmpfile
#    for file in $( cat "${tmpfile}" ); do
#      if [[ "$( file -b "${file}" )" == *"directory"* ]] ; then continue; fi
#      if [[ "${file}" == *kf ]] ; then continue; fi
#      if [[ "${file}" == *.t21 ]] ; then continue; fi
#      if [[ "${file}" == *.ams ]] ; then continue; fi
#      if [[ "${file}" == *.pyc ]] ; then continue; fi
#      if [[ "${file}" == *.svg ]] ; then continue; fi
#      if [[ "${file}" == *.png ]] ; then continue; fi
#      if [[ "${file}" == *.gz  ]] ; then continue; fi
#      if [[ "${file}" == *.js  ]] ; then continue; fi
#      if [[ "${file}" == *.ipynb  ]] ; then continue; fi
#      if [[ "${file}" == *.drawio ]] ; then continue; fi
#      if [[ "${file}" != *${ext} ]] ; then continue ; fi
#      grepi "${cosa}" "${file}" && echo -e '>>>' "${file}" "\n"
#    done
#    rm -- "${tmpfile}"
#
#    unset cosa; unset sotto; unset tmpfile; unset file
# }
#
# -----
# HOSTS
# -----
# Generic secure connection function
  sconnect () {
    if [[ ${#} -lt 2 ]]; then echo "ERROR: Remote user and host required in sconnect"; return 1; fi
    local -i ruser=0 ; local -i rhost=1
    local -a remote
    while [[ -n "${1}" ]]; do
      case "${1}" in
        -IP ) IPcopy="true";;
        *   ) remote=( "${remote[@]}" "${1}" );;
      esac; shift
    done
    local remote_user="${remote[${ruser}]}"
    local remote_host="${remote[${rhost}]}"
    if [[ "${IPcopy}" == "true" ]] && [[ "$( hostname )" == "banana" || "$( hostname )" == "Desktop11v2" ]]; then
#     This function sends the IP into the .bashrc of a remote host
#     before performing a ssh or scp operation.
#     It expects the remote host .bashrc to have an office function
      myIP="$( myip )"
      local dest_fil=""
      for test_dir in "usr/bin" "bin"; do
        test_fil="${test_dir}/.bashrc"
        if ssh ${remote_user}@${remote_host} "[ -f ${test_fil} ]"; then dest_fil="${test_fil}"; break; fi
        if ssh ${remote_user}@${remote_host} "[ -f ${test_fil} ]"; then echo si; else echo no; fi
      done
      if [[ -n "${dest_fil}" ]]; then
        ipwrite="$( echo ssh ${remote_user}@${remote_host} \\"sed -i \'/^\\\s*export\ officeip=*/c\\\ \\\ \\\ \\\ export\ officeip=${myIP}\' \${dest_fil}" )"
        #)" #to fix mistake in coloring
        eval ${ipwrite}
      fi
    fi
    if [[ ${#remote[@]} -eq 2 ]]; then
      ssh ${remote_user}@${remote_host}
    else
      if ssh ${remote_user}@${remote_host} '[ -d ~/tmp ]'; then dest_dir="~/tmp"; else dest_dir="~"; fi
      scp -p -r "${remote[@]:2}" ${remote_user}@${remote_host}:"${dest_dir}"
    fi
  }
# Connect to banana
  office () {
    if [[ "$( hostname )" == "banana" ]]; then echo "ERROR: Already on banana"; return 1; fi
    export officeip=192.168.26.177
    if [[ "${1}" == "-u" ]]; then
      remote_user="${2}"; shift; shift
    else
      remote_user="franco"
    fi
    if [[ -x $( command -v ncat ) ]]; then
      if ncat -w 0.1 -i 0.1 ${officeip} 22 2>&1 | grep -iq "Idle"; then
        :
      else
        echo 'I need to find some server whence to hop to the office' ; return 1
      fi
    fi
    sconnect "${remote_user}" "${officeip}" ${@}
  }
# Connect to office
  erik () {
    if [[ "$( hostname )" == "egidi@Desktop11v2" ]]; then echo "ERROR: Already on master"; return 1; fi
    sconnect -IP "egidi" "erik.scm.com" ${@}
  }
# Connect to master
  master () {
    if [[ "$( hostname )" == "master.scm.com" ]]; then echo "ERROR: Already on master"; return 1; fi
    sconnect -IP "egidi" "master.scm.com" ${@}
  }
# Connect to uz
  unizone () {
    if ncat -w 0.1 -i 0.1 ssh2.uz.sns.it 22 2>&1 | grep -iq "Idle"; then
      sconnect -IP "franco" "ssh2.uz.sns.it" ${@}
    else
      sconnect -IP "franco" "uz.sns.it" ${@}
    fi
  }
#
# ---
# AMS
# ---
  alias setams=". setams.sh"
#
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
  rmall () {
    local -a listrm=( 'TAPE13' '*ams.rkf' '*adf.rkf' 't21.*' 't12.rel' '*ams.log' 'SOLVATION' )
    for targetrm in ${listrm[*]}; do
      if [[ ! -f "${targetrm}" ]]; then continue; fi
      if [[ "${1}" = '-z' ]] && [[ -s ${targetrm} ]]; then continue ; fi
      rm -- "${targetrm}"
    done
    rmjunk
  }
  rmjunk () {
#    unset revert
#    if [ `shopt -q extglob | echo $?` -eq 1 ]; then revert=1 ; fi
#    shopt -s extglob
    local -a listrm=( '*.o+([0-9])' '*.e+([0-9])' 'Gau-+([0-9]).*' '*.tmp' 'fort.7' 't21.*.[A-Z]*' 'TAPE21' 'TAPE12' 't12.rel' 'CreateAtoms.out' 'ams.kid[0-9]*.out' 'KidOutput_*' 'ams.log' )
    for targetrm in ${listrm[*]}; do
      if [[ ! -f "${targetrm}" ]]; then continue; fi
      if [[ "${1}" = '-z' ]] && [[ -s ${targetrm} ]]; then continue ; fi
      rm -- "${targetrm}"
    done
    if [[ -d 'ams.results' ]]; then rm -r -- 'ams.results' ; fi
    unset targetrm
#    if [ ${revert} -eq 1 ]; then shopt -u extglob; fi
  }
## Generate cube using cubegen
#  cube () {
#    usage () {
#      echo "USAGE: cube [-o mycub] [-s S] [-n nproc] -f name.fchk NN [MM ...]"
#      echo "         -o mycub : sets the output cube base name as mycub"
#      echo "         -p npts  : sets the number of points per side of the cube"
#      echo "         -n nproc : use nproc processors"
#      echo "         -f file  : specifies the .fchk input file"
#      echo "         -d type  : does density of specified type (SCF, MP2, ...) instead of MOs"
#      echo "         -s {A,B} : sets the orbital spin as either A or B, or requests spin density if -d is set"
#      echo "         -v       : verbose mode"
#      echo "         NN MM... : lists the orbital numbers"
#      unset -f usage
#    }
#    if [ "${#}" -lt 2 ]; then usage; return 0; fi
#    if [[ -z "${gdvroot}" ]] && [[ -z "${g09root}" ]] && [[ -z "${g16root}" ]]; then echo "ERROR: Gaussian environment not defined"; return 1; fi
#    local vrb="" outcub="" dens="" spin=""; local -i nproc=0; local -a orbs
#    unset npts; unset cubpath
##    shopt -s extglob
#    while [ -n "${1}" ]; do
#      case "${1}" in
#        *.fchk ) file="${1}";;
#        -f     ) file="${2}"; shift;;
#      +([0-9]) ) orbs=( "${orbs[@]}" "${1}" );;
#        -o     ) outcub="${2}"; shift;;
#        -p     ) npts="${2}"; shift;;
#        -d     ) dens="${2}"; shift;;
#        -s     ) spin="${2}"; shift;;
#        -n     ) nproc="${2}"; shift;;
#        -w     ) cubpath="${2}"; shift;;
#        -vcd   ) ;;
#        -v     ) vrb="-v";;
#        *      ) echo "ERROR: unrecognized option ${1}"; return 1;;
#      esac; shift
#    done
#    file="${file%fchk}"
#    if [[ ! -f "${file}fchk" ]]; then echo "ERROR: Cannot find file ${file}fchk"; return 1; fi
#    if [[ -z "${outcub}" ]]; then outcub="${file}"; fi
#    if [[ -n ${dens} ]]; then
#      if [[ -z "${spin}" ]]; then
#        comando="$( echo ${cubpath}/cubegen ${nproc} Density="${dens}" "${file}fchk" "${outcub}dens.cube" )"
#      else
#        comando="$( echo ${cubpath}/cubegen ${nproc}    Spin="${dens}" "${file}fchk" "${outcub}spin.cube" )"
#      fi
#      if [ "${vrb}" = "-v" ]; then echo " ${comando}"; fi
#      eval ${comando}
#    elif [[ "${#orbs}" -gt 0 ]]; then
#      for orb in ${orbs[@]}; do
#        comando="$( echo ${cubpath}/cubegen ${nproc} ${spin}MO="${orb}" "${file}fchk" "${outcub}${spin}${orb}.cube" ${npts} )"
#        if [ "${vrb}" = "-v" ]; then echo " ${comando}"; fi
#        eval ${comando}
#      done
#    else
#      echo "ERROR: Target orbitals or density not specified"
#    fi
##    unset outcub; unset spin; unset dens; unset nproc; unset orbs; unset file; unset outcub; unset comando; unset npts
#  }
#
# ---
# xtb
# ---
  for trydir in "${HOME}/local/xtb" "${HOME}/usr/local/xtb"; do
    if [[ -d "${trydir}" ]]; then
      export XTBHOME="${trydir}"
      if [[ -x "${XTBHOME}/Config_xtb_env.bash" ]]; then
        source "${XTBHOME}/Config_xtb_env.bash"
      else
        echo 'ERROR: Cannot configure xtb'
      fi
      break
    fi
  done; unset trydir
#
# -----
# INTEL
# -----
  for INTELDIR in "/opt/intel"; do
    if [[ -d ${INTELDIR} ]]; then
      tosource="$( find ${INTELDIR} -name mklvars.sh )"
      if [[ -x "${tosource}" ]]; then
        source ${tosource} "intel64"
      fi; unset mpivars
      tosource="$( find ${INTELDIR} -name mpivars.sh )"
      if [[ -x "${tosource}" ]]; then
        source ${tosource}
      fi; unset mpivars
    fi
  done
#
# -------
# LibInt2
# -------
  libint2 () {
    local -a versions=( "2.4.2" "2.2.0" "libint-2.7.0-beta.1" )
    if [[ -z "${LIBINT2_HOME}" ]]; then 
      for tryver in ${versions[@]}; do
        for trydir in "/usr/local/libint/${tryver}" "$HOME/Downloads/libint/${tryver}"; do
          if [[ -d "${trydir}" ]]; then
            export LIBINT2_VER="${tryver}"
            export LIBINT2_HOME="${trydir}"
            break 2
          fi
        done; unset trydir
      done; unset tryver
    elif [[ -z "${LIBINT2_VER}" ]]; then
      for tryver in ${versions[@]}; do
        if [[ "${LIBINT22_HOME}" == *"/libint/${tryver}"* ]]; then
          export LIBINT2_VER="${tryver}"
          break
        fi
      done; unset tryver
    fi
    if [[ -d "${LIBINT2_HOME}" ]] && [[ -n "${LIBINT2_VER}" ]]; then 
      export LIBINT2_DATA_PATH="${LIBINT2_HOME}/share/libint/${LIBINT2_VER}/basis"
    fi
  }
#
# --
# eT
# --
  for trydir in "${HOME}/local/eT" "${HOME}/usr/local/eT"; do
    if [[ -d "${trydir}" ]]; then
      export ET_DIR="${trydir}"
      export SAD_ET_DIR="${ET_DIR}/src/molecule/sad"
      libint2
      break
    fi
  done; unset trydir
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
