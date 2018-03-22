# PyRust
## A tool written in PLY for parsing Rust language.

## Prerequisites:
- PLY 
- Python 2.7.x - 3.x.x

## To run:
- Following runs 14 tests on the Lexer.<br>
	`python3 TestLexerAuto.py`  
- Following runs any manual tests; tests specified inside the file.<br>
	`python3 TestLexerManual.py` 
- Following runs any manual tests; tests specified inside the Rust file `testFile.rs`.<br>
	`python3 TestParserManual.py` 

## Log:
- Lexer is passing tests.
- Grammar has been written and it works.
- Symbol Table generated appropriately.

## TODO:
- Syntax Analysis : Parser
- Semantic Analysis
- Intermediate Code generation.