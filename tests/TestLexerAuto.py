#!/usr/bin/env python3

import re
import sys
import unittest
from os import path

scriptPath = path.dirname(path.realpath(__file__))
sys.path.append(path.join(scriptPath, "..", "src"))

sys.path.insert(0, '..')
from RustLexer import RustLexer


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

    def setUp(self):
        self.clex = RustLexer(self.errorFunc)
        self.clex.build(optimize=False)

    def assertTokensTypes(self, string, types):
        self.clex.input(string)
        self.assertEqual(tokenTypes(self.clex), types)

    def testTrivialTokens(self):
        self.assertTokensTypes('1', ['INT_CONST_DEC'])
        self.assertTokensTypes('-', ['MINUS'])
        self.assertTokensTypes('caseint', ['ID'])
        self.assertTokensTypes('_dollar cent_', ['ID', 'ID'])

    def testIdTypeid(self):
        self.assertTokensTypes('myt', ['ID'])

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

        # - is MINUS, the rest a constnant
        self.assertTokensTypes('-1', ['MINUS', 'INT_CONST_DEC'])

    # def testSpecialNames(self):
    #     self.assertTokensTypes('sizeof offsetof', ['SIZEOF', 'OFFSETOF'])

    def testFloatingConstants(self):
        self.assertTokensTypes('1.5f32', ['FLOAT_CONST'])
        self.assertTokensTypes('01.5', ['FLOAT_CONST'])
        self.assertTokensTypes('.15f64', ['FLOAT_CONST'])
        self.assertTokensTypes('3.3e-3', ['FLOAT_CONST'])
        self.assertTokensTypes('.7e25f32', ['FLOAT_CONST'])
        self.assertTokensTypes('6.3e+125f64', ['FLOAT_CONST'])
        self.assertTokensTypes('666e666', ['FLOAT_CONST'])
        self.assertTokensTypes('00666e+3', ['FLOAT_CONST'])

    def testMess(self):
        self.assertTokensTypes(
            r'[{}]()',
            ['LBRACKET',
                'LBRACE', 'RBRACE',
            'RBRACKET',
            'LPAREN', 'RPAREN'])

    def testExprs(self):
        self.assertTokensTypes(
            'bb-cc',
            ['ID', 'MINUS', 'ID'])

        self.assertTokensTypes(
            '(2+k) * 62',
            ['LPAREN', 'INT_CONST_DEC', 'PLUS', 'ID',
            'RPAREN', 'TIMES', 'INT_CONST_DEC'],)

        self.assertTokensTypes(
            'x = y > 0',
            ['ID', 'EQUALS','ID','GT','INT_CONST_DEC'])

        self.assertTokensTypes(
            '+a-+b',
            ['PLUS', 'ID', 'MINUS', 'PLUS', 'ID'])

    def testStatements(self):
        self.assertTokensTypes(
            r'while i<=10 {}',
            ['WHILE', 'ID', 'LE', 'INT_CONST_DEC','LBRACE','RBRACE'])

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

    def setUp(self):
        self.clex = RustLexer(self.errorFunc)
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

    def testCharConstants(self):
        self.assertLexerError("'", ERR_UNMATCHED_QUOTE)
        self.assertLexerError("'b\n", ERR_UNMATCHED_QUOTE)

        self.assertLexerError("'jx'", ERR_INVALID_CCONST)
        self.assertLexerError(r"'\*'", ERR_INVALID_CCONST)

if __name__ == '__main__':
    unittest.main(verbosity=2)
