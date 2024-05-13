#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
 
pyinstaller --onefile ${SCRIPT_DIR}/src/chattorumu.py
rm -r  ${SCRIPT_DIR}/build
rm ${SCRIPT_DIR}/chattorumu.spec