#!/usr/bin/env python3

# Generates AST code from the configuration file.

import sys
from os import path

scriptPath = path.dirname(path.realpath(__file__))

# Generate RustAst.py
from _ast_gen import ASTCodeGenerator

cfgPath = path.join(scriptPath, "_rust_ast.cfg")
ast_gen = ASTCodeGenerator(cfgPath)

rastPath = path.join(scriptPath, "RustAst.py")

print("GENERATED  %s" % rastPath)

ast_gen.generate(open(rastPath, 'w'))

# Not generating tables as optimize = False
