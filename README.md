# PyRust
# SOME BASIC GRAMMAR IS WORKING, SYM TABLE NOTCOMPLETED.
# COMEPLTED TILL AKHIL IN LAB YSETREDAY
## A tool written in PLY for parsing Rust language.

## Prerequisites:
- PLY 
- Python 3.x.x

## To run:
- Following runs 14 tests on the Lexer.<br>
	`python3 TestLexerAuto.py`  
- Following runs any manual tests; tests specified inside the file.<br>
	`python3 TestLexerManual.py` 

## Log:
- Lexer is passing tests.
- Grammar has been written, but has not been tested yet.

## TODO:
- Some grammatcial aspects of the language have not been implemented on purpose:
	a. Typedefs <br>
		-- yet to be decided.
	b. # includes<br>
		--since it's not a necessity in Rust<br> 
		--also since our aim is to develop stuff for two tags and not everything.

- Syntax Analysis : Parser
- Semantic Analysis
- Intermediate Code generation.