# lexer for Rust language

import re
import sys

from ply import lex
from ply.lex import TOKEN

class RustLexer(object):
    """ A lexer for the Rust language. After building it, set the
        input text with input(), and call token() to get new
        tokens.
    """

    def __init__(self, errorFunc):
        """ Create a new Lexer.

            errorFunc:
                An error function. Will be called with an error message, line and column as arguments, in case of
                an error during lexing.

            NOTE: typeLookupFunc, onRbrace and onLbrace all shifter to parser.
        """

        self.errorFunc = errorFunc
        self.fileName = ''

        # Keeps track of the last token returned from self.token()
        self.lastToken = None

    def build(self, **kwargs):
        self.lexer = lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def stripComments(self,text):
        res = re.sub('//.*?(\r\n?|\n)|/\*.*?\*/', '', text, flags=re.S)
        return res

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
            # print(tok)

    # Internal auxiliary methods
    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.errorFunc(msg, location[0], location[1])
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return (token.lineno, self.find_tok_column(token))

    def _get_keywords(self):
        return keywords

    # Reserved keywords
    keywords = (
        "FN", "MAIN",
        "MUT", "LET",
        "IF", "ELSE",
        "WHILE",
        "U8","U16","U32","U64", "I8","I16", "I32", "I64", "CHAR", "BOOL"
        )

    keywordMap = {}
    for keyword in keywords:
        keywordMap[keyword.lower()] = keyword

    # All the tokens recognized by the lexer
    tokens = keywords + (
        # Identifiers
        'ID',

        # constants
        'INT_CONST_DEC',
        'FLOAT_CONST',
        'CHAR_CONST',
        'BOOL_CONST',

        # Operators
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULUS',
        'LOR', 'LAND', 'LNOT',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

        # Assignment
        'EQUALS',
        # 'TIMESEQUAL', 'DIVEQUAL', 'MODULUSEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',

        # Delimeters
        'LPAREN', 'RPAREN',         # ( )
        'LBRACKET', 'RBRACKET',     # [ ]
        'LBRACE', 'RBRACE',         # { }
        # 'COMMA',                    # ,
        'SEMI', 'COLON',            # ; :
    )

    # Regexes for use in tokens
    identifier =  r'[a-zA-Z\x80-\xff_][a-zA-Z0-9\x80-\xff_]*'

    simpleEscape = r"""([a-zA-Z._!=&\^\-\\?'"])"""
    badEscape = r"""([\\][^a-zA-Z._~^!=&\^\-\\?'"x0-7])"""

    escapeSequence = r"""(\\("""+simpleEscape+"))"
    cconstChar = r"""([^'\\\n]|"""+escapeSequence+')'
    charConst = "'"+cconstChar+"'"
    unmatchedQuote = "('"+cconstChar+"*\\n)|('"+cconstChar+"*$)"
    badCharConst = r"""('"""+cconstChar+"""[^'\n]+')|('')|('"""+badEscape+r"""[^'\n]*')"""

    decDigits = '[0-9]+'
    
    integerSuffixOpt = r'((u8) | (u16) | (u32) | (u64) | (i8) | (i16) | (i32) | (i64))?'
    floatSuffixOpt = r'((f32) | (f64))?'

    decimalConstant = decDigits+integerSuffixOpt

    # floating constants
    exponentPart = r"""([eE][-+]?[0-9]+)"""
    fractionalConstant = r"""([0-9]*\.[0-9]+)"""
    floatingConstant = '(((('+fractionalConstant+')'+exponentPart+'?)|([0-9]+'+exponentPart+'))+'+floatSuffixOpt+')'

    boolConstant = r"(true)|(false)"

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
    t_MODULUS           = r'%'
    t_LOR               = r'\|\|'
    t_LAND              = r'&&'
    t_LNOT              = r'!'
    t_LT                = r'<'
    t_GT                = r'>'
    t_LE                = r'<='
    t_GE                = r'>='
    t_EQ                = r'=='
    t_NE                = r'!='

    # Assignment operators
    t_EQUALS            = r'='

    # TODO: implement shorthand assignment
    # t_TIMESEQUAL        = r'\*='
    # t_DIVEQUAL          = r'/='
    # t_MODULUSEQUAL      = r'%='
    # t_PLUSEQUAL         = r'\+='
    # t_MINUSEQUAL        = r'-='

    # Delimeters
    t_LPAREN            = r'\('
    t_RPAREN            = r'\)'
    t_LBRACE            = r'\{'
    t_RBRACE            = r'\}'
    t_LBRACKET          = r'\['
    t_RBRACKET          = r'\]'

    # TODO: implement array experssions
    # t_COMMA             = r','

    t_SEMI              = r';'
    t_COLON             = r':'

    # The following floating and integer constants are defined as
    # functions to impose a strict order (otherwise, decimal
    # is placed before the others because its regex is longer,
    # and this is bad)
    @TOKEN(floatingConstant)
    def t_FLOAT_CONST(self, t):
        return t

    @TOKEN(decimalConstant)
    def t_INT_CONST_DEC(self, t):
        return t

    @TOKEN(boolConstant)
    def t_BOOL_CONST(self, t):
        return t

    # Must come before badCharConst, to prevent it from
    # catching valid char constants as invalid
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

    @TOKEN(identifier)
    def t_ID(self, t):
        t.type = self.keywordMap.get(t.value, "ID")
        return t

    def t_error(self, t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)
