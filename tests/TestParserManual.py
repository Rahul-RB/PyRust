#!/usr/bin/env python3

import sys
from os import path

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

import RustParser

parser = RustParser.RustParser()
fp = open(path.join(scriptPath, "testFile.rs"), "r")
inp = fp.read()
print("Input Rust Program:\n", inp)
result = parser.parse(inp)
