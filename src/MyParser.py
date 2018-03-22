import re

from ply import yacc

import RustAst
from RustLexer import RustLexer
from RustLexer import keywords
from plyparser import PLYParser, Coord, ParseError, parameterized, template

@template
class RustParser(PLYParser):
	def __init__(
			self,
			lex_optimize=True,
			lexer=RustLexer,
			lextab='pycparser.lextab',
			yacc_optimize=True,
			yacctab='pycparser.yacctab',
			yacc_debug=False,
			taboutputdir=''):
		""" Create a new RustParser.

			Some arguments for controlling the debug/optimization
			level of the parser are provided. The defaults are
			tuned for release/performance mode.
			The simple rules for using them are:
			*) When tweaking RustParser/RustLexer, set these to False
			*) When releasing a stable parser, set to True

			lex_optimize:
				Set to False when you're modifying the lexer.
				Otherwise, changes in the lexer won't be used, if
				some lextab.py file exists.
				When releasing with a stable lexer, set to True
				to save the re-generation of the lexer table on
				each run.

			lexer:
				Set this parameter to define the lexer to use if
				you're not using the default RustLexer.

			lextab:
				Points to the lex table that's used for optimized
				mode. Only if you're modifying the lexer and want
				some tests to avoid re-generating the table, make
				this point to a local lex table file (that's been
				earlier generated with lex_optimize=True)

			yacc_optimize:
				Set to False when you're modifying the parser.
				Otherwise, changes in the parser won't be used, if
				some parsetab.py file exists.
				When releasing with a stable parser, set to True
				to save the re-generation of the parser table on
				each run.

			yacctab:
				Points to the yacc table that's used for optimized
				mode. Only if you're modifying the parser, make
				this point to a local yacc table file

			yacc_debug:
				Generate a parser.out file that explains how yacc
				built the parsing table from the grammar.

			taboutputdir:
				Set this parameter to control the location of generated
				lextab and yacctab files.
		"""
		self.clex = lexer(
			errorFunc=self._lexErrorFunc,
			onLbraceFunc=self._lexOnLbraceFunc,
			onRbraceFunc=self._lexOnRbraceFunc,
			typeLookupFunc=self._lexTypeLookupFunc)

		self.clex.build(
			optimize=lex_optimize,
			lextab=lextab,
			outputdir=taboutputdir)

		self.tokens = self.clex.tokens

		self.rustParser = yacc.yacc(
			module=self,
			start='crate',
			debug=yacc_debug,
			optimize=yacc_optimize,
			tabmodule=yacctab,
			outputdir=taboutputdir)

		# Symbol tables for keeping track of symbols. symbolTable[-1] is
		# the current (topmost) scope. Each scope is a dictionary that
		# specifies whether a name is a type. If symbolTable[n][name] is
		# True, 'name' is currently a type in the scope. If it's False,
		# 'name' is used in the scope but not as a type (for instance, if we
		# saw: int name;
		# If 'name' is not a key in symbolTable[n] then 'name' was not defined
		# in this scope at all.
		self.symbolTable = [dict()]

		# Keeps track of the last token given to yacc (the lookahead token)
		self._lastYieldedToken = None

	def parse(self, text, filename='', debuglevel=0):
		""" Parses C code and returns an AST.

			text:
				A string containing the C source code

			filename:
				Name of the file being parsed (for meaningful
				error messages)

			debuglevel:
				Debug level to yacc
		"""
		self.clex.filename = filename
		self.clex.reset_lineno()
		self.symbolTable = [dict()]
		self._lastYieldedToken = None
		return self.rustParser.parse(
				input=text,
				lexer=self.clex,
				debug=debuglevel)

	######################--   PRIVATE   --######################

	def _pushSymbol(self):
		self.symbolTable.append(dict())

	def _popSymbol(self):
		assert len(self.symbolTable) > 1
		self.symbolTable.pop()

	def _addTypedefName(self, name, coord):
		""" Add a new typedef name (ie a TYPEID) to the current scope
		"""
		if not self.symbolTable[-1].get(name, True):
			self._parse_error(
				"Typedef %r previously declared as non-typedef "
				"in this scope" % name, coord)
		self.symbolTable[-1][name] = True

	def _addIdentifier(self, name, coord):
		""" Add a new object, function, or enum member name (ie an ID) to the
			current scope
		"""
		if self.symbolTable[-1].get(name, False):
			self._parse_error(
				"Non-typedef %r previously declared as typedef "
				"in this scope" % name, coord)
		self.symbolTable[-1][name] = False

	def _isTypedefInScope(self, name):
		""" Is *name* a typedef-name in the current scope?
		"""
		for scope in reversed(self.symbolTable):
			# If name is an identifier in this scope it shadows typedefs in
			# higher scopes.
			in_scope = scope.get(name)
			if in_scope is not None: 
				return in_scope
		return False

	def _lexErrorFunc(self, msg, line, column):
		self._parse_error(msg, self._coord(line, column))

	def _lexOnLbraceFunc(self):
		self._pushSymbol()

	def _lexOnRbraceFunc(self):
		self._popSymbol()

	def _lexTypeLookupFunc(self, name):
		""" Looks up types that were previously defined with
			typedef.
			Passed to the lexer for recognizing identifiers that
			are types.
		"""
		is_type = self._isTypedefInScope(name)
		return is_type

	def _getYaccLookaheadToken(self):
		""" We need access to yacc's lookahead token in certain cases.
			This is the last token yacc requested from the lexer, so we
			ask the lexer.
		"""
		return self.clex.last_token
	def _insertSymbol(self,symbolName,symbolType,symbolValue):
		if(lookup(symbolName)==False):
			return False
		self.symbolTable[-1][symbolName] = [symbolType,symbolValue]

	def _lookupSymbolTable(self,symbolName):
		if(symbolName in self.symbolTable[-1]):
			return False
		return True

	def _printSymbolTable(self):
		for scope in list(reversed(self.symbolTable)):
			for symName,attributes in scope:
				print(symName,"\t",attributes)



	precedence = (
		('left', 'LOR'),
		('left', 'LAND'),
		('left', 'OR'),
		('left', 'XOR'),
		('left', 'AND'),
		('left', 'EQ', 'NE'),
		('left', 'GT', 'GE', 'LT', 'LE'),
		('left', 'RSHIFT', 'LSHIFT'),
		('left', 'PLUS', 'MINUS'),
		('left', 'TIMES', 'DIVIDE', 'MOD')
	)

	def p_crate(self,p):
		"""
			crate : FN MAIN LPAREN RPAREN compoundStmt
		"""
		self.symbolTable[-1]['FN']=None
		self.symbolTable[-1]['MAIN']=None
	
	def p_compoundStmt(self,p):
		"""
			compoundStmt : LBRACE declStmt RBRACE
						 | LBRACE stmt RBRACE
		"""	
		self.symbolTable.append({})

	def p_stmt(self,p):
		"""
			stmt : arithExpr SEMI
				 | assignExpr
				 | compoundStmt
				 | selectionStmt
				 | iterationStmt
		"""
		pass
	def p_selectionStmt(self,p):
		"""
			selectionStmt : IF LPAREN conditionStmt RPAREN compoundStmt
						  | IF LPAREN conditionStmt RPAREN compoundStmt ELSE compoundStmt 
		"""
		self.symbolTable[-1]['IF'] = None
		if(len(p)>=3):
			self.symbolTable[-1]['ELSE'] = None
	def p_iterationStmt(self,p):
		"""
			iterationStmt : WHILE LPAREN conditionStmt RPAREN compoundStmt
		"""	
		self.symbolTable[-1]['WHILE'] = None


	def p_conditionStmt(self,p):
		"""
			conditionStmt : expression
						  | expression logicalOp expression
		"""
		pass

	def p_expression(self,p):
		"""
			expression : relationalExpr
					   | logicalExpr
					   | arithExpr
		"""
		pass

	def p_relationalExpr(self,p):
		"""
			relationalExpr : arithExpr relationalOp arithExpr
		"""
		