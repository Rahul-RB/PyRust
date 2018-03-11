#------------------------------------------------------------------------------
# PyRust: lexer.py
# Names : Amber Viper
#
# RustLexer class: lexer for Rust language
#------------------------------------------------------------------------------
import re
import sys

from ply import lex
from ply.lex import TOKEN


class RustLexer(object):
	""" A lexer for the Rust language. After building it, set the
		input text with input(), and call token() to get new
		tokens.

		The public attribute filename can be set to an initial
		filaneme, but the lexer will update it upon #line
		directives.
	"""
	def __init__(self, errorFunc, onLbraceFunc, onRbraceFunc, typeLookupFunc):
		""" Create a new Lexer.

			errorFunc:
				An error function. Will be called with an error message, line and column as arguments, in case of
				an error during lexing.

			onLbraceFunc, onRbraceFunc:
				Called when an LBRACE or RBRACE is encountered (likely to push/pop typeLookupFunc's scope)

			typeLookupFunc:
				A type lookup function. Given a string, it must return True IFF this string is a name of a type
				that was defined with a typedef earlier.
		"""

		self.errorFunc = errorFunc
		self.onLbraceFunc = onLbraceFunc
		self.onRbraceFunc = onRbraceFunc
		self.typeLookupFunc = typeLookupFunc
		self.fileName = ''

		# Counter for Statistics
		# self.commentCount = Statistics(counterName='commentCounter')
		# self.newlineCount = Statistics(counterName='newlineCounter')
		# self.identifierCount = Statistics(counterName='identifierCounter')
		# self.keywordCount = Statistics(counterName='keywordCounter')



		# Keeps track of the last token returned from self.token()
		self.lastToken = None

		# self.linePattern = re.compile(r'([ \t]*line\W)|([ \t]*\d+)')
		# self.pragmaPattern = re.compile(r'[ \t]*pragma\W')

	def build(self, **kwargs):
		""" Builds the lexer from the specification. Must be
			called after the lexer object is created.

			This method exists separately, because the PLY
			manual warns against calling lex.lex inside
			__init__
		"""
		self.lexer = lex.lex(object=self, **kwargs)

	def reset_lineno(self):
		""" Resets the internal line number counter of the lexer.
		"""
		self.lexer.lineno = 1

	def stripComments(self,text):
		return re.sub('//.*?(\r\n?|\n)|/\*.*?\*/', '', text, flags=re.S)

	def input(self, text):
		self.lexer.input(self.stripComments(text))

	def token(self):
		self.lastToken = self.lexer.token()
		return self.lastToken

	def find_tok_column(self, token):
		""" Find the column of the token in its line.
		"""
		lastCr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
		return token.lexpos - lastCr

	def test(self):
		# self.lexer.input(stripComments(data))
		while True:
			tok = self.lexer.token()
			if not tok: 
				break
			print(tok)

	######################--   PRIVATE   --######################

	##
	## Internal auxiliary methods
	##
	def _error(self, msg, token):
		location = self._make_tok_location(token)
		self.errorFunc(msg, location[0], location[1])
		self.lexer.skip(1)

	def _make_tok_location(self, token):
		return (token.lineno, self.find_tok_column(token))

	##
	## Reserved keywords
	##
	keywords = (
		"SELF","STATIC",  "ABSTRACT",  "ALIGNOF",  "AS",  "BECOME",  
		"BREAK",  "CATCH",  "CRATE",  "DEFAULT",  "DO",  "ELSE",  
		"ENUM",  "EXTERN",  "FALSE",  "FINAL",  "FN",  "FOR",  "IF",  
		"IMPL",  "IN",  "LET",  "LOOP",  "MACRO",  "MATCH",  "MOD",  
		"MOVE",  "MUT",  "OFFSETOF",  "OVERRIDE",  "PRIV",  "PUB",  
		"PURE",  "REF",  "RETURN",  "SIZEOF",  "STRUCT",  "SUPER",  
		"UNION",  "TRUE",  "TRAIT",  "TYPE",  "UNSAFE",  "UNSIZED",  
		"USE",  "VIRTUAL",  "WHILE",  "YIELD",  "CONTINUE",  "PROC",  
		"BOX",  "CONST",  "WHERE",  "TYPEOF",  "INNER_DOC_COMMENT",  
		"OUTER_DOC_COMMENT", "SHEBANG",  "SHEBANG_LINE",  "STATIC_LIFETIME"	
		)

	keywordMap = {}
	for keyword in keywords:
		keywordMap[keyword.lower()] = keyword

	##
	## All the tokens recognized by the lexer
	##
	tokens = keywords + (
		# Identifiers
		'ID',

		# Type identifiers (identifiers previously defined as
		# types with typedef)
		'TYPEID',

		# constants
		'BYTE_CONST',
		'INT_CONST_DEC', 'INT_CONST_OCT', 'INT_CONST_HEX', 'INT_CONST_BIN',
		'FLOAT_CONST',
		'CHAR_CONST',

		# String literals
		'STRING_LITERAL',

		# Underscore
		'UNDERSCORE',

		# Operators
		'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULUS',
		'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT',
		'LOR', 'LAND',
		'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

		# Assignment
		'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODULUSEQUAL',
		'PLUSEQUAL', 'MINUSEQUAL',
		'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL',
		'OREQUAL',

		# Increment/decrement
		# 'PLUSPLUS', 'MINUSMINUS',

		# Structure dereference (->)
		'ARROW',

		# Conditional operator (?)
		'CONDOP',

		# Delimeters
		'LPAREN', 'RPAREN',         # ( )
		'LBRACKET', 'RBRACKET',     # [ ]
		'LBRACE', 'RBRACE',         # { }
		'COMMA', 'PERIOD',          # . ,
		'SEMI', 'COLON',            # ; :
		'MATCHEQUAL',				# =>
		
		# Dots
		'ELLIPSIS', 'DOTDOT',

		# Others
		'PATTERNATCHAR'
		# pre-processor
		# 'PPHASH',       # '#'
		# 'PPPRAGMA',     # 'pragma'
		# 'PPPRAGMASTR',
	)

	##
	## Regexes for use in tokens
	##
	##

	# valid C identifiers (K&R2: A.2.3), plus '$' (supported by some compilers)
	identifier =  r'[a-zA-Z\x80-\xff_][a-zA-Z0-9\x80-\xff_]*'

	# Comments in Rust : Three types : // ; /**/ and ///

	hexPrefix = '0x'
	hexDigits = '[0-9a-fA-F]+'
	
	# decPrefix = ''
	decDigits = '[0-9]+'

	octPrefix = '0o'
	octDigits = '[0-7]+'
	
	binPrefix = '0b'
	binDigits = '[0-1]+'

	integerSuffixOpt = r'((u8) | (u16) | (u32) | (u64) | (i8) | (i16) | (i32) | (i64))?'
	floatSuffixOpt = r'((f32) | (f64))?'

	# integer constants (K&R2: A.2.5.1)

	decimalConstant = decDigits+integerSuffixOpt
	octalConstant = '0o[0-7]*'+integerSuffixOpt
	hexConstant = hexPrefix+hexDigits+integerSuffixOpt
	binConstant = binPrefix+binDigits+integerSuffixOpt
	badOctalConstant = '0o[0-7]*[89]'


	# character constants (K&R2: A.2.5.2)
	# Note: a-zA-Z and '.-~^_!=&;,' are allowed as escape chars to support #line
	# directives with Windows paths as filenames (..\..\dir\file)
	# For the same reason, decimalEscape allows all digit sequences. We want to
	# parse all correct code, even if it means to sometimes parse incorrect
	# code.
	#
	simpleEscape = r"""([a-zA-Z._!=&\^\-\\?'"])"""
	decimalEscape = r"""(\d+)"""
	hexEscape = r"""(x[0-9a-fA-F]+)"""
	badEscape = r"""([\\][^a-zA-Z._~^!=&\^\-\\?'"x0-7])"""

	escapeSequence = r"""(\\("""+simpleEscape+'|'+decimalEscape+'|'+hexEscape+'))'
	cconstChar = r"""([^'\\\n]|"""+escapeSequence+')'
	charConst = "'"+cconstChar+"'"
	unmatchedQuote = "('"+cconstChar+"*\\n)|('"+cconstChar+"*$)"
	badCharConst = r"""('"""+cconstChar+"""[^'\n]+')|('')|('"""+badEscape+r"""[^'\n]*')"""

	# string literals (K&R2: A.2.6)
	stringChar = r"""([^"\\\n]|"""+escapeSequence+')'
	rawString = '"'+stringChar+'"'+'|'+'\#'+stringChar+'\#'
	stringLiteral = '"'+stringChar+'*"'
	badStringLiteral = '"'+stringChar+'*?'+badEscape+stringChar+'*"'

	# floating constants (K&R2: A.2.5.3)
	exponentPart = r"""([eE][-+]?[0-9]+)"""
	fractionalConstant = r"""([0-9]*\.[0-9]+)"""
	floatingConstant = '(((('+fractionalConstant+')'+exponentPart+'?)|([0-9]+'+exponentPart+'))+'+floatSuffixOpt+')'

	#byte literals
	# TODO 
	# boolean literals
	booleanConstant = r"""['true'|'false']"""

	t_ignore = ' \t'

	# Newlines
	def t_NEWLINE(self, t):
		r'\n+'
		t.lexer.lineno += t.value.count("\n")

	# Operators
	t_PLUS              = r'\+'
	t_MINUS             = r'-'
	t_TIMES             = r'\*'
	t_DIVIDE            = r'/'
	t_MODULUS               = r'%'
	t_OR                = r'\|'
	t_AND               = r'&'
	t_NOT               = r'!'
	t_XOR               = r'\^'
	t_LSHIFT            = r'<<'
	t_RSHIFT            = r'>>'
	t_LOR               = r'\|\|'
	t_LAND              = r'&&'
	t_LT                = r'<'
	t_GT                = r'>'
	t_LE                = r'<='
	t_GE                = r'>='
	t_EQ                = r'=='
	t_NE                = r'!='

	# Assignment operators
	t_EQUALS            = r'='
	t_TIMESEQUAL        = r'\*='
	t_DIVEQUAL          = r'/='
	t_MODULUSEQUAL          = r'%='
	t_PLUSEQUAL         = r'\+='
	t_MINUSEQUAL        = r'-='
	t_LSHIFTEQUAL       = r'<<='
	t_RSHIFTEQUAL       = r'>>='
	t_ANDEQUAL          = r'&='
	t_OREQUAL           = r'\|='
	t_XOREQUAL          = r'\^='

	# Increment/decrement
	# t_PLUSPLUS          = r'\+\+'
	# t_MINUSMINUS        = r'--'

	# ->
	t_ARROW             = r'->'

	# ?
	t_CONDOP            = r'\?'

	# Dots
	t_ELLIPSIS          = r'\.\.\.'
	t_DOTDOT       		= r'\.\.'

	# Delimeters
	t_LPAREN            = r'\('
	t_RPAREN            = r'\)'
	t_LBRACKET          = r'\['
	t_RBRACKET          = r'\]'
	t_COMMA             = r','
	t_PERIOD            = r'\.'
	t_SEMI              = r';'
	t_COLON             = r':'
	t_MATCHEQUAL		= r'=>' 
	

	# Others
	t_PATTERNATCHAR		= r'@'

	# Scope delimiters
	# To see why onLbraceFunc is needed, consider:
	#   typedef char TT;
	#   void foo(int TT) { TT = 10; }
	#   TT x = 5;
	# Outside the function, TT is a typedef, but inside (starting and ending
	# with the braces) it's a parameter.  The trouble begins with yacc's
	# lookahead token.  If we open a new scope in brace_open, then TT has
	# already been read and incorrectly interpreted as TYPEID.  So, we need
	# to open and close scopes from within the lexer.
	# Similar for the TT immediately outside the end of the function.
	#
	@TOKEN(r'\{')
	def t_LBRACE(self, t):
		self.onLbraceFunc()
		return t
	@TOKEN(r'\}')
	def t_RBRACE(self, t):
		self.onRbraceFunc()
		return t

	t_STRING_LITERAL = stringLiteral

	# The following floating and integer constants are defined as
	# functions to impose a strict order (otherwise, decimal
	# is placed before the others because its regex is longer,
	# and this is bad)
	#
	@TOKEN(floatingConstant)
	def t_FLOAT_CONST(self, t):
		return t

	@TOKEN(hexConstant)
	def t_INT_CONST_HEX(self, t):
		return t

	@TOKEN(binConstant)
	def t_INT_CONST_BIN(self, t):
		return t

	@TOKEN(badOctalConstant)
	def t_BAD_CONST_OCT(self, t):
		msg = "Invalid octal constant"
		self._error(msg, t)

	@TOKEN(octalConstant)
	def t_INT_CONST_OCT(self, t):
		# msg = "************IT CAME HERE????***********"
		# self._error(msg,t)
		return t

	@TOKEN(decimalConstant)
	def t_INT_CONST_DEC(self, t):
		return t

	# Must come before badCharConst, to prevent it from
	# catching valid char constants as invalid
	#
	@TOKEN(charConst)
	def t_CHAR_CONST(self, t):
		return t

	@TOKEN(unmatchedQuote)
	def t_UNMATCHED_QUOTE(self, t):
		msg = "Unmatched '"
		self._error(msg, t)

	@TOKEN(badCharConst)
	def t_BAD_CHAR_CONST(self, t):
		msg = "Invalid char constant %s" % t.value
		self._error(msg, t)

	# unmatched string literals are caught by the preprocessor

	@TOKEN(badStringLiteral)
	def t_BAD_STRING_LITERAL(self, t):
		msg = "String contains invalid escape code"
		self._error(msg, t)

	@TOKEN(identifier)
	def t_ID(self, t):
		t.type = self.keywordMap.get(t.value, "ID")
		if t.type == 'ID' and self.typeLookupFunc(t.value):
			t.type = "TYPEID"
		return t

	def t_error(self, t):
		msg = 'Illegal character %s' % repr(t.value[0])
		self._error(msg, t)



