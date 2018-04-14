#!/usr/bin/env python3

import sys
from os import path

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

import RustParser
import IntCodeGen as icg

parser = RustParser.RustParser()

rustFilePath = path.join(scriptPath, "testFile.rs")

ast = parser.parse(path=rustFilePath)
print("\n\t~~AST~~")
ast.show()

ic = icg.generate(ast)

print("\n\t~~IC~~")
print(ic)