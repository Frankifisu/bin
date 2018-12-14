#!/bin/bash
#
#Define new functionals
declare -a funcnam=( 'hf' 'lda' 'tpss' 'pbe' 'bly' 'b97d' 'pbe0' 'm06' 'm062x' 'sogga' 'pw1' 'cam')
declare -a funckey=( 'HF' 'LSDA' 'RevTPSSRevTPSS' 'PBEPBE' 'BLYP' 'B97D' 'PBE1PBE' 'M06' 'M062X' 'SOGGA11X' 'mPW1PW91' 'CAM-B3LYP')
if [[ "${#funcnam[@]}" -ne "${#funckey[@]}" ]]; then echo "ERROR: Array mismatch"; exit 1; fi

function usage {
  echo 'Usage: genfuncs.sh [-h] input_b3l.com'
  echo '  Creates inputs for the following functionals:'
  echo "  ${funckey[@]}"
  return 0
}

#Check number of arguments
if [[ "${#}" -ne 1 ]]; then usage; exit 1; fi

while [[ -n "${1}" ]]; do
  case "${1}" in
    -h          ) usage ;;
    *           ) com="${1}";;
  esac
  shift
done
unset -f usage

#Define input files and check that they be readable
if [[ ! -f "${com}" ]]; then echo "ERROR: file ${com} not found"; exit 1; fi
chk="${com%com}chk"
if [[ ! -f "${chk}" ]]; then echo "ERROR: file ${chk} not found"; exit 1; fi

declare -i len=${#funcnam[@]}

b3l='b3l'
B3L='B3LYP'

for idx in $( seq 0 $[${len}-1] ); do
  #Create new input files
  func="${funcnam[${idx}]}"
  FUNC="${funckey[${idx}]}"
  newcom="${com/${b3l}/${func}}"
  newchk="${chk/${b3l}/${func}}"
  cp -v -- "${com}" "${newcom}"
  cp -v -- "${chk}" "${newchk}"
  #Replace keywords
  sedi -s -v ${b3l} ${func} ${newcom}
  sedi -s -v ${B3L} ${FUNC} ${newcom}
done

for i in "funcnam" "funckey" "len" "com" "chk" "b3l" "B3L" "idx" "func" "FUNC" "newcom" "newchk"; do unset ${i}; done
unset i

