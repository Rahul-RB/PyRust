#!/usr/bin/env python3

import sys
from os import path

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

import RustParser

parser = RustParser.RustParser()

rustFilePath = path.join(scriptPath, "testFile.rs")

result = parser.parse(path=rustFilePath)
