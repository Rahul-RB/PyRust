import sys
sys.path.insert(0, '../src/')

import RustParser
from RustParser import RustParser
# from ply import yacc

parser = RustParser()
fp = open("test.c","r")
inp = fp.readlines()
inp = ''.join(inp)
print(inp)
# while True:
try:
# s = input('> ')
	s = inp
except EOFError:
	exit()
result = parser.parse(s)
print(result)


			# self._parse_error('Error, single expressions only.',self._token_coord(p, 1))
