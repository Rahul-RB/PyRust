#!/bin/bash

SCRIPTDIR=$(dirname "$0")
BASEDIR="$SCRIPTDIR/.."

RED='\033[1;31m'
GREEN='\033[1;32m'
NC='\033[0m'

PASSED="${GREEN}PASSSED$NC"
FAILED="${RED}FAILED$NC"

runTest() {
    TEST=$1
    echo -e "\n$2"
    $TEST
    [[ $? = 0 ]] && RESULT="$PASSED" || RESULT="$FAILED"
    echo -e "$TEST: $RESULT"    
}

runTest "$BASEDIR/tests/TestLexerAuto.py" "Running Lexer Unit Tests"
runTest "$BASEDIR/tests/TestLexerManual.py" "Running Lexer Manual Test"
runTest "$BASEDIR/tests/TestSymbolTable.py $BASEDIR/tests/testFile2.rs 1" "Running Symbol Table Test"
runTest "$BASEDIR/tests/TestAST.py $BASEDIR/tests/testFile1.rs" "Running Abstract Syntax Tree Test"
runTest "$BASEDIR/tests/TestICGen.py $BASEDIR/tests/testFile1.rs" "Running Intermediate Code Generation Test"
