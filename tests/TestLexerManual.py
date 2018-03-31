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

m.input(r"""
fn main()
{
    //this is a comment
    let y: char = 'k';
    /*
        this is one type of commetn
    */
    /* ** */
    /**/ 
    /*//*/ 
    ////
    /// This is a doc comment type 1    
    //! This is a doc comment type 2

}""")

print("Generated Tokens:")
print(tabulate(map(lambda tok: [tok.type,tok.value], tokenTypes(m)), headers=["TYPE", "VALUE"], tablefmt="orgtbl"))
