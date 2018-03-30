#!/bin/bash

SCRIPTDIR=$(dirname "$0")
BASEDIR="$SCRIPTDIR/.."

RED='\033[1;31m'
GREEN='\033[1;32m'
NC='\033[0m'

PASSED="${GREEN}PASSSED$NC"
FAILED="${RED}FAILED$NC"

TEST="$BASEDIR/tests/TestLexerAuto.py"
echo -e "\nRunning Lexer Unit Tests"
$TEST
[[ $? = 0 ]] && RESULT="$PASSED" || RESULT="$FAILED"
echo -e "$TEST: $RESULT"

TEST="$BASEDIR/tests/TestLexerManual.py"
echo -e "\nRunning Lexer Manual Tests"
$TEST
[[ $? = 0 ]] && RESULT="$PASSED" || RESULT="$FAILED"
echo -e "$TEST: $RESULT"

TEST="$BASEDIR/tests/TestParserManual.py"
echo -e "\nRunning Parser Manual Tests"
$TEST
[[ $? = 0 ]] && RESULT="$PASSED" || RESULT="$FAILED"
echo -e "$TEST: $RESULT"