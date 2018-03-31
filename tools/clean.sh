#!/bin/bash

SCRIPTDIR=$(dirname "$0")
BASEDIR="$SCRIPTDIR/.."

echo "Removing any files named parsetab.py ..."
find $BASEDIR -name \parsetab.py -type f -delete
echo "Removing any directories named __pycache__ ..."
find $BASEDIR -name "__pycache__" -type d -exec rm -r "{}" \;
echo "Removing $BASEDIR/src/RustAST.py ..."
rm "$BASEDIR/src/RustAST.py"
echo "CLEANED"