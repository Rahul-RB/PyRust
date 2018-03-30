import re

from ply import yacc

# import RustAst
from pprint import pprint
from RustLexer import RustLexer
from tabulate import tabulate
# from RustLexer import keywords
from plyparser import PLYParser, Coord, ParseError, parameterized, template

def printTokens(res):
	print("Tokens generated : ")
	finalRes = []
	for token in res:
		finalRes.append([token.type,token.value,token.lineno,token.lexpos])
	print(tabulate(finalRes,headers=["Name","Value","Line Number","Lex Column Position"],tablefmt="fancy_grid"))

@template
class RustParser(PLYParser):
# class RustParser():
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
		
		# After demo, remove the following lines.
		fp = open("testFile.rs","r")
		inp = fp.readlines()
		inp = ''.join(inp)
		s = inp

		self.clex.input(inp)
		res = self.clex.test()
		printTokens(res)
		# End of Demo
		
		# Symbol tables for keeping track of symbols. symbolTable[-1] is
		# the current (topmost) scope. Each scope is a dictionary that
		# specifies whether a name is a type. If symbolTable[n][name] is
		# True, 'name' is currently a type in the scope. If it's False,
		# 'name' is used in the scope but not as a type (for instance, if we
		# saw: int name;
		# If 'name' is not a key in symbolTable[n] then 'name' was not defined
		# in this scope at all.
		# This is a per scope Symbol Table

		# [0] is the global scope
		self.symbolTable = [{ keyword for keyword in self.clex.keywords }]
		self.globalSymbolTable = {'Keywords':{ keyword for keyword in self.clex.keywords }}

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
		# if self.symbolTable == None
		self.scopeNumber = 0
		self._lastYieldedToken = None
		return self.rustParser.parse(
				input=text,
				lexer=self.clex,
				debug=debuglevel)

	######################--   PRIVATE   --######################

	def _pushSymbol(self):
		# self.symbolTable.append(dict())
		pass

	def _popSymbol(self):
		# assert len(self.symbolTable) > 1
		# self.symbolTable.pop()
		pass

	def _addTypedefName(self, name, coord):
		""" Add a new typedef name (ie a TYPEID) to the current scope
		"""
		if not self.symbolTable[-1].get(name, True):
			self._parse_error(
				"Typedef %r previously declared as non-typedef "
				"in this scope" % name, coord)
		# self.symbolTable[-1][name] = True

	def _addIdentifier(self, name, coord):
		""" Add a new object, function, or enum member name (ie an identifier_1) to the
			current scope
		"""
		if self.symbolTable[-1].get(name, False):
			self._parse_error(
				"Non-typedef %r previously declared as typedef "
				"in this scope" % name, coord)
		# self.symbolTable[-1][name] = False

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
		# print("onLbraceFunc")
		# self._pushSymbol()
		pass

	def _lexOnRbraceFunc(self):
		# print("onRbraceFunc")
		# self._popSymbol()
		pass
		
	def _lexTypeLookupFunc(self, name):
		# is_type = self._isTypedefInScope(name)
		return False

	def _getYaccLookaheadToken(self):
		""" We need access to yacc's lookahead token in certain cases.
			This is the last token yacc requested from the lexer, so we
			ask the lexer.
		"""
		return self.clex.last_token

	def _insertSymbol(self,symbolName,symbolType,symbolValue):
		if(self._lookupSymbolTable(symbolName)==False):
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
	"""
	Symbol Table : Dictionary
	- Preload keywords -- key is the keyword and the value is just anything, eg: "FN":"KEYWORD"
	- Preload Macro 
	"""

	def p_crate(self,p):
		"""
			crate : FN MAIN LPAREN RPAREN compoundStmt
		"""
		# self.symbolTable[-1]['FN']=None
		# self.symbolTable[-1]['MAIN']=None
		# pprint(self.symbolTable)
		pprint(self.globalSymbolTable,width=1)
		pass
	
	def p_compoundStmt(self,p):
		"""
			compoundStmt : lbrace stmt_list rbrace 
						 
		""" 
		pass

	def p_lbrace(self, p):
		"""
			lbrace : LBRACE
		"""
		# print("\nNew scope...")
		self.symbolTable.append({})

	def p_rbrace(self, p):
		"""
			rbrace : RBRACE
		"""
		# print("\nPopping:", self.symbolTable[-1])
		self.globalSymbolTable['Block '+str(self.scopeNumber)+':'] = self.symbolTable[-1]
		self.scopeNumber +=1
		# print("Symbol Table: ", self.symbolTable)
		self.symbolTable = self.symbolTable[:-1]

	def p_stmt_list(self, p):
		""" stmt_list : stmt
					  | stmt stmt_list
		"""
		pass

	def p_stmt(self,p):
		"""
			stmt : declaration
				 | assignStmt
				 | selectionStmt
				 | iterationStmt
				 | compoundStmt
				 | predefinedMacroCall
				 | empty
		"""
		pass

	def p_assignStmt(self,p):
		"""
			assignStmt : identifier_1 EQUALS arithExpr SEMI
		"""
		# print("*********************ASSIGNEXPR*********************\n",list(p))
		# print(self.symbolTable)
		# if(p[1] not in self.symbolTable[-1]):
		# 	self._parse_error('Variable not declared before using',self._token_coord(p, 1))
		# elif(self.symbolTable[-1][p[1]].startswith("IMMUTABLE")):
		# 	self._parse_error('Variable not of type Mutable to be modified',self._token_coord(p, 1))
		# print(self.symbolTable[-1][p[1]])
		# print("*********************ASSIGNEXPR*********************\n")
	def p_predefinedMacroCall(self,p):
		"""
			predefinedMacroCall : ID NOT LPAREN RPAREN
		"""
		pass
	def p_selectionStmt(self,p):
		"""
			selectionStmt : IF conditionStmt compoundStmt
						  | IF conditionStmt compoundStmt ELSE compoundStmt 
		"""
		# self.symbolTable[-1]['IF'] = None
		# if(len(p)>=3):
		#   self.symbolTable[-1]['ELSE'] = None
		pass

	def p_iterationStmt(self,p):
		"""
			iterationStmt : WHILE conditionStmt compoundStmt
		""" 
		# self.symbolTable[-1]['WHILE'] = None
		pass

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
		pass

	def p_logicalExpr(self,p):
		"""
			logicalExpr : arithExpr logicalOp arithExpr
		""" 
		pass

	def p_logicalOp(self,p):
		"""
			logicalOp : LAND
					  | LOR
		"""
		pass

	def p_relationalOp(self,p):
		"""
			relationalOp : LT
						 | GT
						 | LE
						 | GE
						 | NE
						 | EQ
		"""
		pass

	def p_declaration_1(self,p):
		"""
			declaration : LET ID COLON dataType EQUALS expression SEMI
		"""
		# print("Adding ", (p[2], "IMMUTABLE;"+p[4]), "to", self.symbolTable[-1])
		# print("Adding ", (p[2], "IMMUTABLE;"+p[4]))
		self.symbolTable[-1][p[2]] = "IMMUTABLE;"+p[4]

	def p_declaration_2(self,p):
		"""
			declaration : LET MUT ID COLON dataType EQUALS expression SEMI
		"""
		# print("Adding ", (p[3], "MUTABLE;"+p[5]), "to", self.symbolTable[-1])
		# print("Adding ", (p[3], "MUTABLE;"+p[5]))
		self.symbolTable[-1][p[3]] = "MUTABLE;"+p[5]
	
	def p_dataType(self,p):
		"""
			dataType : I8
					 | I16
					 | I32
					 | I64
					 | U8
					 | U16
					 | U32
					 | U64
		"""
		p[0] = p[1]
		# print(list(p))
		# self.symbolTable[-1][]
		pass

	def p_identifier_1(self,p):
		"""
			identifier_1 : ID
		"""
		for scope in list(reversed(self.symbolTable)):
			if not isinstance(scope,set):
				if(p[1] in scope):
					if(scope[p[1]].startswith("IMMUTABLE")):
						self._parse_error('Variable not of type Mutable to be modified',self._token_coord(p, 1))
					else:
						p[0] = p[1]
						break
			else:
				self._parse_error('Variable used before declaration',self._token_coord(p, 1))

	def p_identifier_2(self,p):
		"""
			identifier_2 : ID
		"""	
		
		pass
	def p_arithExpr(self,p):
		"""
			arithExpr : arithExpr PLUS arithExpr
					  | arithExpr MINUS arithExpr
					  | arithExpr2
		"""
		pass

	def p_arithExpr2(self,p):
		"""
			arithExpr2 : arithExpr2 TIMES arithExpr2
					   | arithExpr2 DIVIDE arithExpr2
					   | arithExpr3 
		"""
		pass

	def p_arithExpr3(self,p):
		"""
			arithExpr3 : identifier_1
					   | LPAREN arithExpr RPAREN
					   | unaryOperation
					   | arithExpr4
		"""
		pass
	
	def p_arithExpr4(self,p):
		"""
			arithExpr4 : number
		"""
		pass

	def p_number(self,p):
		"""
			number : BYTE_CONST
				   | INT_CONST_DEC
				   | INT_CONST_OCT 
				   | INT_CONST_HEX 
				   | INT_CONST_BIN
				   | FLOAT_CONST
		"""
		pass
	def p_unaryOperation(self,p):
		"""
			unaryOperation : identifier_1 unaryOperator identifier_1
						   | identifier_1 unaryOperator number
						   | identifier_1 unaryOperator LPAREN arithExpr RPAREN
		"""
		pass

	def p_unaryOperator(self,p):
		"""
			unaryOperator : PLUSEQUAL
						  | MINUSEQUAL
						  | TIMESEQUAL
						  | DIVEQUAL
						  | MODULUSEQUAL
						  | LSHIFTEQUAL
						  | RSHIFTEQUAL
						  | ANDEQUAL
						  | OREQUAL
						  | XOREQUAL
		"""
		pass

	def p_empty(self, p):
		'empty : '
		p[0] = None

	def p_error(self, p):
		# If error recovery is added here in the future, make sure
		# _getYaccLookaheadToken still works!
		#
		print(p)
		if p:
			self._parse_error(
				'before: %s' % p.value,
				self._coord(lineno=p.lineno,
							column=self.clex.find_tok_column(p)))
		else:
			self._parse_error('At end of input', self.clex.filename)
