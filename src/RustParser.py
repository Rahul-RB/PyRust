# Built-in
import re

# Installed
from ply import yacc

# Project files
from RustLexer import RustLexer
from plyparser import PLYParser, Coord, ParseError, parameterized, template

# Generated project files
import RustAst

@template
class RustParser(PLYParser):
    def __init__(
            self,
            lex_optimize=False,
            lexer=RustLexer,
            lextab=None,
            yacc_optimize=False,
            yacctab=None,
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

        # NOTE: set lex/yacc optimize to False due to generated files.
        self.clex = lexer(errorFunc=self._lexErrorFunc)

        self.clex.build(optimize=lex_optimize,
                        lextab=lextab,
                        outputdir=taboutputdir)

        self.tokens = self.clex.tokens

        self.rustParser = yacc.yacc(module=self,
                                    start='start',
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
        # This is a per scope Symbol Table

        # [0] is set of keywords, [1] is the global scope.
        self.symbolTable = [{ keyword for keyword in self.clex.keywords }]

        # Keeps track of the last token given to yacc (the lookahead token)
        self._lastYieldedToken = None

    def parse(self, text, filename='', debuglevel=0):
        self.clex.filename = filename
        self.clex.reset_lineno()
        self._lastYieldedToken = None

        return self.rustParser.parse(input=text,
                                     lexer=self.clex,
                                     debug=debuglevel)

    def _lexErrorFunc(self, msg, line, column):
        print(msg, line, column)
        self._parse_error(msg, self._coord(line, column))

    # TODO: determine if this lookahead is required based on the production
    #       rules. If not, then remove it from the lexer itself.
    # def _getYaccLookaheadToken(self):
    #     """ We need access to yacc's lookahead token in certain cases.
    #         This is the last token yacc requested from the lexer, so we
    #         ask the lexer.
    #     """
    #     return self.clex.last_token

    # TODO: Either use this or write better grammar
    # precedence = (
    #     ('left', 'LOR'),
    #     ('left', 'LAND'),
    #     ('left', 'EQ', 'NE'),
    #     ('left', 'GT', 'GE', 'LT', 'LE'),
    #     ('left', 'PLUS', 'MINUS'),
    #     ('left', 'TIMES', 'DIVIDE')
    # )

    def p_start(self, p):
        """ start : FN MAIN LPAREN RPAREN compStmt
        """
        pass

    def p_stmtList(self, p):
        """ stmtList : stmt
                     | stmt stmtList
        """
        pass

    def p_stmt(self, p):
        """ stmt : declStmt
                 | selStmt
                 | iterStmt
                 | compStmt
                 | assignStmt
                 | empty
        """
        pass

    def p_declStmt(self, p):
        """ declStmt : LET ID COLON type EQUALS expr SEMI
                     | LET MUT ID COLON type EQUALS expr SEMI
        """
        print("Adding ", (p[2], p[4]), "to", self.symbolTable[-1])
        self.symbolTable[-1][p[2]] = p[4]

    def p_selStmt(self, p):
        """ selStmt : IF expr compStmt
                    | IF expr compStmt ELSE compStmt
        """
        pass

    def p_iterStmt(self, p):
        """ iterStmt : WHILE expr compStmt
        """
        pass


    def p_compStmt(self, p):
        """ compStmt : lbrace stmtList rbrace
        """
        pass

    def p_assignStmt(self, p):
        """ assignStmt : ID EQUALS expr SEMI
        """
        pass

    def p_lbrace(self, p):
        """ lbrace : LBRACE
        """
        print("\nNew scope...")
        self.symbolTable.append({})

    def p_rbrace(self, p):
        """ rbrace : RBRACE
        """
        print("\nPopping:", self.symbolTable[-1])
        print("Symbol Table: ", self.symbolTable)
        self.symbolTable = self.symbolTable[:-1]

    def p_type(self, p):
        """ type : dataType
                 | LBRACKET dataType SEMI INT_CONST_DEC RBRACKET
        """

        # TODO: check if p is for array and return accordingly.
        p[0] = p[1]

    def p_dataType(self, p):
        """ dataType : I8
                     | I16
                     | I32
                     | I64
                     | U8
                     | U16
                     | U32
                     | U64
                     | BOOL
                     | CHAR
        """
        p[0] = p[1]

    def p_expr(self, p):
        """ expr : literal
                 | ID
                 | unopExpr
                 | binopExpr
                 | LPAREN expr RPAREN
        """
        pass

    def p_literal(self, p):
        """ literal : CHAR_CONST
                    | FLOAT_CONST
                    | INT_CONST_DEC
                    | BOOL_CONST
        """
        pass

    def p_unopExpr(self, p):
        """ unopExpr : unop expr
        """
        pass

    def p_unop(self, p):
        """ unop : PLUS
                 | MINUS
                 | LNOT
        """
        pass

    def p_binopExpr(self, p):
        """ binopExpr : expr binop expr
        """
        pass

    def p_binop(self, p):
        """ binop : arithOp
                  | logiOp
                  | relOp
        """
        pass

    def p_arithOp(self, p):
        """ arithOp : PLUS
                    | MINUS
                    | TIMES
                    | DIVIDE
                    | MODULUS
        """
        pass

    def p_logiOp(self, p):
        """ logiOp : LAND
                   | LOR
        """
        pass

    def p_relOp(self, p):
        """ relOp : LT
                  | GT
                  | LE
                  | GE
                  | EQ
                  | NE
        """
        pass


    def p_empty(self, p):
        """ empty : """
        p[0] = None

    def p_error(self, p):
        # If error recovery is added here in the future, make sure
        # _getYaccLookaheadToken still works!
        print(p)
        if p:
            self._parse_error(
                'before: %s' % p.value,
                self._coord(lineno=p.lineno,
                            column=self.clex.find_tok_column(p)))
        else:
            self._parse_error('At end of input', self.clex.filename)
