#!/usr/bin/env python3

import sys
from os import path

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

import RustParser
import IntCodeGen as icg

parser = RustParser.RustParser(verbose=0)

ast = parser.parse(path=sys.argv[1])

ic = icg.generate(ast)

print("\n".join(map(str, ic)))
