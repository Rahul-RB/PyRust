import re
import sys
import unittest

sys.path.insert(0, '..')
from lexer import RustLexer


def tokenList(clex):
    return list(iter(clex.token, None))


def tokenTypes(clex):
    return [i.type for i in tokenList(clex)]


class TestRustLexerNoErrors(unittest.TestCase):
    """ Test lexing of strings that are not supposed to cause
        errors. Therefore, the errorFunc passed to the lexer
        raises an exception.
    """
    def errorFunc(self, msg, line, column):
        self.fail(msg)

    def onLbraceFunc(self):
        pass

    def onRbraceFunc(self):
        pass

    def typeLookupFunc(self, typ):
        if typ.startswith('mytype'):
            return True
        else:
            return False

    def setUp(self):
        self.clex = RustLexer(self.errorFunc, lambda: None, lambda: None,
                           self.typeLookupFunc)
        self.clex.build(optimize=False)

    def assertTokensTypes(self, string, types):
        self.clex.input(string)
        self.assertEqual(tokenTypes(self.clex), types)

    def testTrivialTokens(self):
        self.assertTokensTypes('1', ['INT_CONST_DEC'])
        self.assertTokensTypes('-', ['MINUS'])
        # self.assertTokensTypes('volatile', ['VOLATILE'])
        self.assertTokensTypes('...', ['ELLIPSIS'])
        self.assertTokensTypes('..', ['DOTDOT'])
        # self.assertTokensTypes('++', ['PLUSPLUS'])
        # self.assertTokensTypes('case int', ['CASE', 'INT'])
        self.assertTokensTypes('caseint', ['ID'])
        self.assertTokensTypes('_dollar cent_', ['ID', 'ID'])
        self.assertTokensTypes('i ^= 1;', ['ID', 'XOREQUAL', 'INT_CONST_DEC', 'SEMI'])

    def testIdTypeid(self):
        self.assertTokensTypes('myt', ['ID'])
        self.assertTokensTypes('mytype', ['TYPEID'])
        self.assertTokensTypes('mytype6 var', ['TYPEID', 'ID'])

    def testIntegerConstants(self):
        self.assertTokensTypes('12', ['INT_CONST_DEC'])
        self.assertTokensTypes('12u8', ['INT_CONST_DEC'])
        self.assertTokensTypes('12u16', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872u32', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872u64', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872i8', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872i16', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872i32', ['INT_CONST_DEC'])
        self.assertTokensTypes('1009843200000i64', ['INT_CONST_DEC'])
        self.assertTokensTypes('12u8', ['INT_CONST_DEC'])
        self.assertTokensTypes('12u16', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872u32', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872u64', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872i8', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872i16', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872i32', ['INT_CONST_DEC'])
        self.assertTokensTypes('1009843200000i64', ['INT_CONST_DEC'])
        # self.assertTokensTypes('1009843200000LLu', ['INT_CONST_DEC'])

        self.assertTokensTypes('0o77', ['INT_CONST_OCT'])
        self.assertTokensTypes('0o123456', ['INT_CONST_OCT'])

        self.assertTokensTypes('0xf7', ['INT_CONST_HEX'])
        self.assertTokensTypes('0b110', ['INT_CONST_BIN'])
        self.assertTokensTypes('0x01202AAbbf7', ['INT_CONST_HEX'])

        # no 0 before x, so ID catches it
        self.assertTokensTypes('xf7', ['ID'])

        # - is MINUS, the rest a constnant
        self.assertTokensTypes('-1', ['MINUS', 'INT_CONST_DEC'])

    # def testSpecialNames(self):
    #     self.assertTokensTypes('sizeof offsetof', ['SIZEOF', 'OFFSETOF'])

    def testFloatingConstants(self):
        self.assertTokensTypes('1.5f32', ['FLOAT_CONST'])
        self.assertTokensTypes('01.5', ['FLOAT_CONST'])
        self.assertTokensTypes('.15f64', ['FLOAT_CONST'])
        # self.assertTokensTypes('0.', ['FLOAT_CONST'])

        # but just a period is a period
        self.assertTokensTypes('.', ['PERIOD'])

        self.assertTokensTypes('3.3e-3', ['FLOAT_CONST'])
        self.assertTokensTypes('.7e25f32', ['FLOAT_CONST'])
        self.assertTokensTypes('6.3e+125f64', ['FLOAT_CONST'])
        self.assertTokensTypes('666e666', ['FLOAT_CONST'])
        self.assertTokensTypes('00666e+3', ['FLOAT_CONST'])

        # but this is a hex integer + 3
        self.assertTokensTypes('0x0666e+3', ['INT_CONST_HEX', 'PLUS', 'INT_CONST_DEC'])

    # def testHexadecimalFloatingConstants(self):
    #     self.assertTokensTypes('0xDE.488641p0', ['HEX_FLOAT_CONST'])
    #     self.assertTokensTypes('0x.488641p0', ['HEX_FLOAT_CONST'])
    #     self.assertTokensTypes('0X12.P0', ['HEX_FLOAT_CONST'])

    def testCharConstants(self):
        self.assertTokensTypes(r"""'x'""", ['CHAR_CONST'])
        # self.assertTokensTypes(r"""L'x'""", ['WCHAR_CONST'])
        self.assertTokensTypes(r"""'\t'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\''""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\?'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\012'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\x2f'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\x2f12'""", ['CHAR_CONST'])
        # self.assertTokensTypes(r"""L'\xaf'""", ['WCHAR_CONST'])

    def testOnRbraceLbrace(self):
        braces = []
        def on_lbrace():
            braces.append('{')
        def on_rbrace():
            braces.append('}')
        clex = RustLexer(self.errorFunc, on_lbrace, on_rbrace,
                      self.typeLookupFunc)
        clex.build(optimize=False)
        clex.input('hello { there } } and again }}{')
        tokenList(clex)
        self.assertEqual(braces, ['{', '}', '}', '}', '}', '{'])

    def testStringLiteral(self):
        self.assertTokensTypes('"a string"', ['STRING_LITERAL'])
        # self.assertTokensTypes('L"ing"', ['WSTRING_LITERAL'])
        self.assertTokensTypes(
            '"i am a string too \t"',
            ['STRING_LITERAL'])
        self.assertTokensTypes(
            r'''"esc\ape \"\'\? \0234 chars \rule"''',
            ['STRING_LITERAL'])
        self.assertTokensTypes(
            r'''"hello 'joe' wanna give it a \"go\"?"''',
            ['STRING_LITERAL'])
        self.assertTokensTypes(
            '"\123\123\123\123\123\123\123\123\123\123\123\123\123\123\123\123"',
            ['STRING_LITERAL'])

    def testMess(self):
        self.assertTokensTypes(
            r'[{}]()',
            ['LBRACKET',
                'LBRACE', 'RBRACE',
            'RBRACKET',
            'LPAREN', 'RPAREN'])

        self.assertTokensTypes(
            r'()||!C&!Z?J',
            ['LPAREN', 'RPAREN',
            'LOR',
            'NOT', 'ID',
            'AND',
            'NOT', 'ID',
            'CONDOP', 'ID'])

        self.assertTokensTypes(
            r'+-*/%|||&&&^><>=<===!=',
            ['PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULUS',
            'LOR', 'OR',
            'LAND', 'AND',
            'XOR',
            'GT', 'LT', 'GE', 'LE', 'EQ', 'NE'])

        self.assertTokensTypes(
            r'+--->?.,;:',
            ['PLUS', 'MINUS','MINUS',
            'ARROW', 'CONDOP',
            'PERIOD', 'COMMA', 'SEMI', 'COLON'])

    def testExprs(self):
        self.assertTokensTypes(
            'bb-cc',
            ['ID', 'MINUS', 'ID'])

        self.assertTokensTypes(
            'foo & 0xFF',
            ['ID', 'AND', 'INT_CONST_HEX'])

        self.assertTokensTypes(
            '(2+k) * 62',
            ['LPAREN', 'INT_CONST_DEC', 'PLUS', 'ID',
            'RPAREN', 'TIMES', 'INT_CONST_DEC'],)

        self.assertTokensTypes(
            'x | y >> z',
            ['ID', 'OR', 'ID', 'RSHIFT', 'ID'])

        self.assertTokensTypes(
            'x <<= z << 5',
            ['ID', 'LSHIFTEQUAL', 'ID', 'LSHIFT', 'INT_CONST_DEC'])

        # self.assertTokensTypes(
        #     'x = y > 0 ? y : -6',
        #     ['ID', 'EQUALS','ID', 'GT', 'INT_CONST_OCT','CONDOP','ID','COLON','MINUS', 'INT_CONST_DEC'])
        self.assertTokensTypes(
            'x = y > 0',
            ['ID', 'EQUALS','ID','GT','INT_CONST_DEC'])

        self.assertTokensTypes(
            '+a-+b',
            ['PLUS', 'ID', 'MINUS', 'PLUS', 'ID'])

    def testStatements(self):
        self.assertTokensTypes(
            'for i in 0..10',
            ['FOR', 'ID', 'IN', 'INT_CONST_DEC', 'DOTDOT', 'INT_CONST_DEC'])
        self.assertTokensTypes(
            r'while i<=10 {}',
            ['WHILE', 'ID', 'LE', 'INT_CONST_DEC','LBRACE','RBRACE'])
        self.assertTokensTypes(

            r'if n < 10 && n > -10 {} else {println!(", and is a big number, half the number");};',
            ['IF','ID','LT','INT_CONST_DEC','LAND','ID','GT','MINUS','INT_CONST_DEC','LBRACE','RBRACE','ELSE','LBRACE','ID','NOT',
                'LPAREN','STRING_LITERAL','RPAREN','SEMI','RBRACE','SEMI'
            ]
            )
# Keeps all the errors the lexer spits in one place, to allow
# easier modification if the error syntax changes.
#
ERR_ILLEGAL_CHAR    = 'Illegal character'
ERR_OCTAL           = 'Invalid octal constant'
ERR_UNMATCHED_QUOTE = 'Unmatched \''
ERR_INVALID_CCONST  = 'Invalid char constant'
ERR_STRING_ESCAPE   = 'String contains invalid escape'

ERR_FILENAME_BEFORE_LINE    = 'filename before line'
ERR_LINENUM_MISSING         = 'line number missing'
ERR_INVALID_LINE_DIRECTIVE  = 'invalid #line directive'


class TestRustLexerErrors(unittest.TestCase):
    """ Test lexing of erroneous strings.
        Works by passing an error functions that saves the error
        in an attribute for later perusal.
    """
    def errorFunc(self, msg, line, column):
        self.error = msg

    def onLbraceFunc(self):
        pass

    def onRbraceFunc(self):
        pass

    def typeLookupFunc(self, typ):
        return False

    def setUp(self):
        self.clex = RustLexer(self.errorFunc, self.onLbraceFunc,
                self.onRbraceFunc, self.typeLookupFunc)
        self.clex.build(optimize=False)
        self.error = ""

    def assertLexerError(self, str, errorLike):
        # feed the string to the lexer
        self.clex.input(str)

        # Pulls all tokens from the string. Errors will
        # be written into self.error by the errorFunc
        # callback
        #
        tokenTypes(self.clex)

        # compare the error to the expected
        self.assertTrue(re.search(errorLike, self.error),
            "\nExpected error matching: %s\nGot: %s" %
                (errorLike, self.error))

        # clear last error, for the sake of subsequent invocations
        self.error = ""

    def testTrivialTokens(self):
        self.assertLexerError('~', ERR_ILLEGAL_CHAR)
        self.assertLexerError('`', ERR_ILLEGAL_CHAR)
        self.assertLexerError('\\', ERR_ILLEGAL_CHAR)

    def testIntegerConstants(self):
        self.assertLexerError('0o29', ERR_OCTAL)
        self.assertLexerError('0o12345678', ERR_OCTAL)

    def testCharConstants(self):
        self.assertLexerError("'", ERR_UNMATCHED_QUOTE)
        self.assertLexerError("'b\n", ERR_UNMATCHED_QUOTE)

        self.assertLexerError("'jx'", ERR_INVALID_CCONST)
        self.assertLexerError(r"'\*'", ERR_INVALID_CCONST)

    def testStringLiterals(self):
        self.assertLexerError(r'"jx\9"', ERR_STRING_ESCAPE)
        self.assertLexerError(r'"hekllo\* on ix"', ERR_STRING_ESCAPE)
        self.assertLexerError(r'L"hekllo\* on ix"', ERR_STRING_ESCAPE)

    # def test_preprocessor(self):
    #     self.assertLexerError('#line "ka"', ERR_FILENAME_BEFORE_LINE)
    #     self.assertLexerError('#line df', ERR_INVALID_LINE_DIRECTIVE)
    #     self.assertLexerError('#line \n', ERR_LINENUM_MISSING)


if __name__ == '__main__':
    unittest.main()
