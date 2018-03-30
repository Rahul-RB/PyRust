#!/usr/bin/env python3

import MyParser
from MyParser import RustParser

parser = RustParser()
fp = open("testFile.rs","r")
inp = fp.readlines()
inp = ''.join(inp)
s = inp
result = parser.parse(s)
