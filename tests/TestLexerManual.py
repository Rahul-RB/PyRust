#!/usr/bin/env python3

import sys
from os import path
from tabulate import tabulate

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

from RustLexer import RustLexer

def tokenList(clex):
    return list(iter(clex.token, None))

def tokenTypes(clex):
    return [i for i in tokenList(clex)]

def errorFunc(msg, line, column):
    print("ERROR:", msg)

m = RustLexer("test-lex-man", errorFunc)
m.build(optimize=False)

testRustProgram = r"""fn main() {
    //this is a comment
    let y: char = 'k';
    /*
        this is one type of comment
    */
    /* ** */
    /*//*/
    let mut ar: [i64; 10] = [77; 5];
    // This is another comment
    /*
     * This is also a comment
     * This is line 2
     * This is line 3
     * This is line 4
     */
}"""

acr = m.stripComments(testRustProgram)

lines = tuple(zip(testRustProgram.split("\n"), acr.split("\n")))
mx = 0

for line in lines:
    lmx = max(len(line[0]), len(line[1]))
    mx = lmx if lmx > mx else mx

lbcr = len("Before Comment Removal")
mx = lbcr if lbcr > mx else mx

# print(("|{:<%d}|{:<%d}|" % (mx, mx)).format(*line))
print(("╭{:─<%d}┬{:─<%d}╮" % (mx, mx)).format("",""))
print(("│{:^%d}│{:^%d}│" % (mx, mx)).format("Before Comment Removal", "After Comment Removal"))
print(("├{:─<%d}┼{:─<%d}┤" % (mx, mx)).format("",""))
for line in lines:
    print(("│{:<%d}│{:<%d}│" % (mx, mx)).format(*line))
print(("╰{:─<%d}┴{:─<%d}╯" % (mx, mx)).format("",""))

m.input(testRustProgram)

print("Generated Tokens:")
print(tabulate(map(lambda tok: [tok.type,tok.value], tokenTypes(m)), headers=["TYPE", "VALUE"], tablefmt="orgtbl"))
