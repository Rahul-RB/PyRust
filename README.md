## PyRust - A tool to parse Rust and produce Intermediate Code.

### Prerequisites:
- [PLY - v3.1.1](http://www.dabeaz.com/ply/)
- [Python - v3.x](https://www.python.org/download/releases/3.0/)

### Testing:
- Generate AST Nodes definitions in `./src/RustAST.py`:<br>
`$ ./src/_build_tables.py`
- Run tests:
    - All tests:<br>
`$ ./tools/test-all.sh`
    - Lexer Unit Tests:<br>
`$ ./tests/TestLexerAuto.py`
    - Lexer Manual Tests:<br>
`$ ./tests/TestLexerManual.py`
    - Parser Manual Tests:<br>
`$ ./tests/TestParserManual.py`
- Clean project directory:<br>
`$ ./tools/clean.sh`

### TODO:
#### Lexical Analysis
- [x] Remove Comments.
- [x] Generate tokens.
- [x] Preload keywords into the symbol table.
- [x] Make an entry for the identifiers into the symbol table(if there exists an identifier with the same name in different scopes then construct symbol table per scope).
- [ ] Symbol table must contain entries for predefined routines like printf, scanf etc
#### Syntax Analysis
- [x] Write CFG for the entire program.
- [ ] ~If implementing parser by hand:~
	- [ ] ~Prefer RDP with backtracking.~
	- [ ] ~Perform translation at required places in the code for each non-terminal.~
- [x] If implementing using tool:
	- [x] Provide appropriate semantic rules.
#### Semantic Analysis
- [ ] Take care of the primitive types and array types.
- [ ] Take care of coersions.
- [ ] Take care of Arithemetic expressions.
- [ ] Concetrate on the looping construct choosen.
- [ ] Update type and storage information into the symbol table.
- [ ] Show Abstract Syntax tree(AST).
#### Intermediate Code Generation
- [ ] Three address code generation
#### Optimizing Intermediate Code
- [ ] Constant folding
- [ ] Constant Propogation
- [ ] ~Common subexpression elimination (optional)~
- [ ] Dead code elimination
- [ ] ~Reducing temporaries (optional)~
- [ ] Loop optimizations 
