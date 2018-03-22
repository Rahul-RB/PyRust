#!/usr/bin/env python3

# import sys
# sys.path.insert(0, '../src/')

import MyParser
from MyParser import RustParser
# from ply import yacc

parser = RustParser()
fp = open("testFile.rs","r")
inp = fp.readlines()
inp = ''.join(inp)
# print(inp)
# while True:
try:
# s = input('> ')
	s = inp
except EOFError:
	exit()
result = parser.parse(s)
# print(result)
