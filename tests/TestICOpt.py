#!/usr/bin/env python3

import sys
from os import path

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

import RustParser
import IntCodeGen as icg
import IntCodeOpt as ico

parser = RustParser.RustParser(verbose=0)

ast = parser.parse(path=sys.argv[1])

ic = list(icg.generate(ast))

icBefore = "\n".join(map(str, ic))

# for lno, i in enumerate(ic):
#     print("%s: %s" % ("{:>2}".format(lno), i))

ic = ico.optimize(
    ic, 
    passes =  [
        ico.constantFoldingAndPropagation,
        ico.loopInvariantCodeMotion,
        ico.constantFoldingAndPropagation
    ])
# ic = ico.optimize(ic,passes=[ico.constantFolding])

icAfter = "\n".join(map(str, ic))

print(RustParser.multiLineTabulate(rows=[[icBefore, icAfter]], headers=["Before Optimization", "After Optimization"]))