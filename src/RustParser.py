# Built-in
import re
import json

# Installed
from ply import yacc

# Project files
from RustLexer import RustLexer
from plyparser import PLYParser, Coord, ParseError, parameterized, template

# Generated project files
import RustAST

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
            taboutputdir='',
            verbose=0,):
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
        self.verbose = verbose
        self.clex = lexer(fileName="test-file-name.rs" , errorFunc=self._lexErrorFunc)

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
        if self.verbose > 0:
            self.printSymbolTable()

        # Keeps track of the last token given to yacc (the lookahead token)
        self._lastYieldedToken = None

    def parse(self, path='', debuglevel=0):
        fp = open(path, "r")
        text = fp.read()
        self.clex.fileName = path
        self.clex.reset_lineno()
        self._lastYieldedToken = None

        self.sourceCode = text.split("\n")

        return self.rustParser.parse(input=text,
                                     lexer=self.clex,
                                     debug=debuglevel)

    def _lexErrorFunc(self, msg, line, column):
        self._parse_error(msg, self._coord(line, column), errorType = "LexicalError")

    # TODO: determine if this lookahead is required based on the production
    #       rules. If not, then remove it from the lexer itself.
    # def _getYaccLookaheadToken(self):
    #     """ We need access to yacc's lookahead token in certain cases.
    #         This is the last token yacc requested from the lexer, so we
    #         ask the lexer.
    #     """
    #     return self.clex.last_token

    def _getCoord(self, p, i):
        return self._coord(lineno=p.lineno(i), column=self.clex.find_tok_column(p.lexpos(i)))

    def p_start(self, p):
        """ start : FN MAIN LPAREN RPAREN compStmt
        """
        fileAST = RustAST.FileAST(ext=[p[5]])
        p[0] = fileAST

    def p_stmtList(self, p):
        """ stmtList : stmtList stmt
                     | stmt
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_stmt(self, p):
        """ stmt : declStmt
                 | selStmt
                 | iterStmt
                 | compStmt
                 | assignStmt
                 | empty
        """
        p[0] = p[1]

    defaults = {
        "c": "\0",
        "f": 0.0,
        "i": 0,
        "u": 0,
        "b": False
    }

    def _checkAssignmentType(self, lhs, rhs, p):
        autoConv = False
        if lhs.type != rhs.type:
            if (rhs.type == "integer" and lhs.type[0] in {"i", "u"}) or (rhs.type == "float" and lhs.type.startswith("f")):
                rhs.type = lhs.type
                autoConv = True
            if not autoConv:
                self._parse_error("Mismatched types! expected %s, found %s!" % (lhs.type, rhs.type), rhs.coord)
        return lhs, rhs

    def p_declStmt(self, p):
        """ declStmt : LET ID COLON type EQUALS init SEMI
                     | LET MUT ID COLON type EQUALS init SEMI
        """
        mut, typ, ideInd, initInd = (True, p[5], 3, 7) if len(p) == 9 else (False, p[4], 2, 6)
        ide = p[ideInd]
        init = p[initInd]

        if typ["declType"] != init["initType"]:
            self._parse_error("Invalid initialization!", p[initInd]["coord"])

        entry = {
            "mut": mut,
            "type": typ
        }

        ideObj = RustAST.ID(ide, typ["dataType"], self._token_coord(p, ideInd))
        lhs = ideObj

        if typ["declType"] == "var":
            rhs = init["initData"]

            lhs, rhs = self._checkAssignmentType(lhs, rhs, p)

            p[0] = RustAST.Declaration(entry,
                                       RustAST.Assignment("=", lhs, rhs, self._token_coord(p, ideInd)),
                                       self._token_coord(p, 1))
        elif typ["declType"] == "arr":
            if len(init["initData"]) > int(typ["length"]):
                self._parse_error("Excess elements in array initializer!", p[initInd]["coord"])

            assignments = []

            for index, rhs in enumerate(init["initData"]):
                lhs, rhs = self._checkAssignmentType(lhs, rhs, p)
                assignments.append(RustAST.Assignment(
                    "=",
                    RustAST.ArrayElement(
                        RustAST.Constant(
                            "i64",
                            index,
                            self._token_coord(p, initInd)),
                        lhs,
                        lhs.type,
                        self._token_coord(p, initInd)),
                    rhs,
                    self._token_coord(p, initInd)
                ))

            for index in range(len(init["initData"]), int(typ["length"])):
                assignments.append(RustAST.Assignment(
                    "=",
                    RustAST.ArrayElement(RustAST.Constant("i64", index), lhs, lhs.type, self._token_coord(p, initInd)),
                    RustAST.Constant(
                        typ["dataType"],
                        self.defaults[typ["dataType"][0]],
                        self._token_coord(p, initInd)
                    ),
                    self._token_coord(p, initInd)
                ))

            p[0] = RustAST.ArrayDecl(entry, typ["length"], assignments, self._token_coord(p, 1))

        self.symbolTable[-1][ide] = entry

        if self.verbose > 0:
            print("Found Delcaration for %s %s." % ("Variable" if typ["declType"] == "var" else "Array", ide))
            self.printSymbolTable()

    def p_selStmt(self, p):
        """ selStmt : IF expr compStmt
                    | IF expr compStmt ELSE compStmt
                    | IF expr compStmt ELSE selStmt
        """
        ifExpr = p[2]

        if ifExpr.type != "bool":
            self._parse_error("Mismatched types! expected bool, found %s!" % ifExpr.type, p[2].coord)

        ifTrueBlock = p[3]
        ifFalseBlock = None

        if len(p) == 6:
            ifFalseBlock = p[5]

        p[0] = RustAST.If(ifExpr, ifTrueBlock, ifFalseBlock, self._token_coord(p, 1))

    def p_iterStmt(self, p):
        """ iterStmt : WHILE expr compStmt
        """
        if p[2].type != "bool":
            self._parse_error("Mismatched types! expected bool, found %s!" % p[2].type, p[2].coord)

        p[0] = RustAST.While(p[2], p[3], self._token_coord(p, 1))

    def p_compStmt(self, p):
        """ compStmt : lbrace stmtList rbrace
        """
        p[0] = RustAST.Compound(p[2], self._token_coord(p, 1))

    def p_arrayElement(self, p):
        """ arrayElement : ID LBRACKET expr RBRACKET
        """
        p[0] = RustAST.ArrayElement(p[3], RustAST.ID(p[1], None, self._token_coord(p, 1)), None, self._token_coord(p, 1))

    def p_assignStmt(self, p):
        """ assignStmt : ID EQUALS expr SEMI
                       | arrayElement EQUALS expr SEMI
        """
        isDecl = False
        isMut = None
        typ = None

        isArray = isinstance(p[1], RustAST.ArrayElement)

        p1 = p[1]
        p1Coord = self._token_coord(p, 1)
        if isArray:
            p1 = p[1].arrId.name
            p1Coord = p[1].coord

        for scope in reversed(self.symbolTable):
            if p1 in scope:
                isDecl = True
                isMut = scope[p1]["mut"]
                typ = scope[p1]["type"]
                break

        if not isDecl:
            self._parse_error("%s is not declared!" % p1, p1Coord)

        if not isMut:
            self._parse_error("%s is not mutable!" % p1, p1Coord)

        if isArray:
            p[1].arrId.type = typ["dataType"]
            p[1].type = typ["dataType"]

        lhs = None
        rhs = p[3]

        if not isArray:
            if typ["declType"] != "var":
                self._parse_error("%s is not a variable!" % p1, p1Coord)

            lhs = RustAST.ID(p1, typ["dataType"], self._token_coord(p, 1))
        else:
            if typ["declType"] != "arr":
                self._parse_error("%s is not an array!" % p1, p1Coord)

            lhs = p[1]

        lhs, rhs = self._checkAssignmentType(lhs, rhs, p)

        p[0] = RustAST.Assignment("=", lhs, rhs, p1Coord)

    def p_init(self, p):
        """ init : expr
                 | LBRACKET arrayInitList RBRACKET
                 | LBRACKET expr SEMI INT_CONST_DEC RBRACKET
        """
        init = {}
        lp = len(p)
        if lp == 2:
            init = {
                "initType": "var",
                "initData": p[1],
                "coord": p[1].coord
            }
        elif lp == 4:
            init = {
                "initType": "arr",
                "initData": p[2],
                "coord": p[2][0].coord
            }
        elif lp == 6:
            init = {
                "initType": "arr",
                "initData": [p[2] for _ in range(int(p[4]))],
                "coord": p[2].coord
            }
        p[0] = init

    def p_arrayInitList(self, p):
        """ arrayInitList : arrayInitList COMMA expr
                          | expr
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_lbrace(self, p):
        """ lbrace : LBRACE
        """
        self.symbolTable.append({})
        if self.verbose > 0:
            print("Found New Compound Statement.")
            self.printSymbolTable()

    def p_rbrace(self, p):
        """ rbrace : RBRACE
        """
        self.symbolTable.pop()
        if self.verbose > 0:
            print("Reached End of Compound Statement.")
            self.printSymbolTable()

    def p_type(self, p):
        """ type : dataType
                 | LBRACKET dataType SEMI INT_CONST_DEC RBRACKET
        """
        typ = {}
        if len(p) == 2:
            typ = {
                "declType": "var",
                "dataType": p[1]
            }
        else:
            typ = {
                "declType": "arr",
                "dataType": p[2],
                "length": p[4]
            }
        p[0] = typ

    def p_dataType(self, p):
        """ dataType : I8
                     | I16
                     | I32
                     | I64
                     | U8
                     | U16
                     | U32
                     | U64
                     | F32
                     | F64
                     | BOOL
                     | CHAR
        """
        p[0] = p[1]

    def p_expr(self, p):
        """ expr : literal
                 | ID
                 | arrayElement
                 | unopExpr
                 | binopExpr
                 | LPAREN expr RPAREN
        """
        p1Obj = None
        if len(p) == 2:
            isArray = isinstance(p[1], RustAST.ArrayElement)
            if isArray or p.slice[1].type == "ID":
                isDecl = False
                cd = None

                p1 = p[1]
                if isArray:
                    p1 = p[1].arrId.name

                for scope in reversed(self.symbolTable):
                    if p1 in scope:
                        isDecl = True
                        cs = scope
                        typ = scope[p1]["type"]
                        break

                if not isDecl:
                    self._parse_error("%s is not declared!" % p1, p[1].coord)

                if isArray:
                    p[1].arrId.type = typ["dataType"]
                    p[1].type = typ["dataType"]
                    p1Obj = p[1]
                else:
                    p1Obj = RustAST.ID(p1, cs[p1]["type"]["dataType"], self._token_coord(p, 1))
            else:
                p1Obj = p[1]
        else:
            p1Obj = p[2]
        p[0] = p1Obj

    typeMap = {
        "CHAR_CONST": {
            "typ": "char",
            "conv": str,
        },
        "FLOAT_CONST": {
            "typ": "float",
            "conv": float,
        },
        "INT_CONST_DEC": {
            "typ": "integer",
            "conv": int,
        },
        "BOOL_CONST": {
            "typ": "bool",
            "conv": lambda x: True if x=="true" else False,
        }
    }

    def p_literal(self, p):
        """ literal : CHAR_CONST
                    | FLOAT_CONST
                    | INT_CONST_DEC
                    | BOOL_CONST
        """
        p1 = p.slice[1]
        typ = self.typeMap[p1.type]["typ"]
        try:
            p[0] = RustAST.Constant(typ, self.typeMap[p1.type]["conv"](p1.value), self._token_coord(p, 1))
        except ValueError as ve:
            suffixStart = None
            if typ == "integer":
                if p1.value.find("i") >= 0:
                    suffixStart = "i"
                elif p1.value.find("u") >= 0:
                    suffixStart = "u"
            elif typ == "float":
                suffixStart = "f"

            p1Value = p1.value[:p1.value.find(suffixStart)]
            p1Type = p1.value[p1.value.find(suffixStart):]
            p[0] = RustAST.Constant(p1Type, self.typeMap[p1.type]["conv"](p1Value), self._token_coord(p, 1))

    def p_unopExpr(self, p):
        """ unopExpr : MINUS expr
                     | LNOT expr
        """
        if p[2].type != "char":
            if not ((p[1] == "-" and p[2].type.startswith("u")) or (p[1] == "!" and p[2].type.startswith("f"))):
                p[0] = RustAST.UnaryOp(p[1], p[2], p[2].type, self._token_coord(p, 1))
                return
        self._parse_error("Cannot apply unary operator `%s` to type %s!" % (p[1], p[2].type), self._token_coord(p, 1))

    precedence = (
        ("left", "LOR"),
        ("left", "LAND"),
        ("left", "EQ", "NE"),
        ("left", "GT", "GE", "LT", "LE"),
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE", "MODULUS"),
        ("left", "LNOT")
    )

    def p_binopExpr(self, p):
        """ binopExpr : expr PLUS expr
                      | expr MINUS expr
                      | expr TIMES expr
                      | expr DIVIDE expr
                      | expr MODULUS expr
                      | expr LAND expr
                      | expr LOR expr
                      | expr LT expr
                      | expr GT expr
                      | expr LE expr
                      | expr GE expr
                      | expr EQ expr
                      | expr NE expr
        """
        invalidTypes = {"char", "bool"}
        arithOpers = {"+", "-", "*", "/", "%"}
        if p[2] in arithOpers and (p[1].type in invalidTypes or p[3].type in invalidTypes):
            self._parse_error("No implementation for `%s %s %s`!" % (p[1].type, p[2], p[3].type), self._token_coord(p, 2))

        if p[2] in {"&&", "||"}:
            misMatch = None
            if p[1].type != "bool":
                misMatch = p[1]
            elif p[3].type != "bool":
                misMatch = p[3]

            if misMatch != None:
                self._parse_error("Mismatched types! expected bool, found %s!" % misMatch.type, misMatch.coord)

        autoConv = False
        if p[1].type != p[3].type:
            if (p[1].type[0] in {"i", "u"} and p[3].type == "integer") or (p[1].type.startswith("f") and p[3].type == "float"):
                p[3].type = p[1].type
                autoConv = True
            elif (p[3].type[0] in {"i", "u"} and p[1].type == "integer") or (p[3].type.startswith("f") and p[1].type == "float"):
                p[1].type = p[3].type
                autoConv = True

            if not autoConv:
                self._parse_error("Mismatched types! expected %s, found %s!" % (p[1].type, p[3].type), p[3].coord)

        if p[2] in arithOpers:
            p[0] = RustAST.BinaryOp(p[2], p[1], p[3], p[1].type, self._token_coord(p, 2))
        else:
            p[0] = RustAST.BinaryOp(p[2], p[1], p[3], "bool", self._token_coord(p, 2))


    def p_empty(self, p):
        """ empty : """
        p[0] = None

    def p_error(self, p):
        # If error recovery is added here in the future, make sure
        # _getYaccLookaheadToken still works!
        if p:
            self._parse_error("Before: %s" % p.value, self._coord(p.lineno, p.lexpos-self.clex.lexer.lexdata.rfind('\n', 0, p.lexpos)))
        else:
            self._parse_error("Reached EOF (maybe due to mismatched braces).", self._coord(len(self.sourceCode)-1))

    # Utility functions for printing symbol table.
    def _dictTable(self, sd):
        rows = []
        for entry in sd:
            rows.append([entry, json.dumps(sd[entry])])
        if len(rows) == 0:
            rows=[["", ""]]
        return multiLineTabulate(rows, ["IDENTIFIER", "DESCRIPTION"])

    def printSymbolTable(self):
        st = map(lambda x: [self._dictTable(x) if not isinstance(x, set) else "KEYWORDS: " + ",".join([str(keyword) for keyword in x])], self.symbolTable)
        print(multiLineTabulate(st, ["PER SCOPE SYMBOL TABLE"]))
        if self.verbose > 1:
            input()

# Utility function placed here for convenience
from itertools import zip_longest

# This function can take cells with multiple lines of text. Headers can only be a single line.
# Example:
#     For rows, header = [["r1c1", "r1c2"], ["r2c1", "r2c2l1\nr2c2l3\nr2c2l3"], ["r3c1l1\nr3c1l2\nr3c1l3", "r3c2"]], ["H1", "H2"]
#     We get the following table:
#     ╭──────┬──────╮
#     │  H1  │  H2  │
#     ╞══════╪══════╡
#     │r1c1  │r1c2  │
#     ├──────┼──────┤
#     │r2c1  │r2c2l1│
#     │      │r2c2l3│
#     │      │r2c2l3│
#     ├──────┼──────┤
#     │r3c1l1│r3c2  │
#     │r3c1l2│      │
#     │r3c1l3│      │
#     ╰──────┴──────╯
def multiLineTabulate(rows, headers):
    rowWidths = [len(header) for header in headers]

    lines = []
    for row in rows:
        rowList = []
        for column, cell in enumerate(row):
            rowList.append([])
            for line in cell.split("\n"):
                lineLen = len(line)
                rowWidths[column] = max(lineLen, rowWidths[column])
                rowList[column].append(line)
        lines.append(rowList)

    dashs = ["{:─<%d}" % width for width in rowWidths]
    doubleDashs = ["{:═<%d}" % width for width in rowWidths]
    spaceCentred = ["{:^%d}" % width for width in rowWidths]
    spaceLeft = ["{:<%d}" % width for width in rowWidths]

    topHolder = "╭%s╮" % ("┬".join(dashs))
    bottomHolder = "╰%s╯" % ("┴".join(dashs))

    centredRowHolder = "│%s│" % ("│".join(spaceCentred))
    leftRowHolder = "│%s│" % ("│".join(spaceLeft))
    headerLineHolder = "╞%s╡" % ("╪".join(doubleDashs))
    lineHolder = "├%s┤" % ("┼".join(dashs))

    emptys = [""] * len(headers)

    table = []

    table.append(topHolder.format(*emptys))
    table.append(centredRowHolder.format(*headers))
    table.append(headerLineHolder.format(*emptys))

    rows = []
    for row in lines:
        tmp = []
        for line in zip_longest(*row):
            line = list(map(lambda x: "" if x == None else str(x) , line))
            tmp.append(leftRowHolder.format(*line))
        tmp = "\n".join(tmp)
        rows.append(tmp)
    table.append(("\n"+lineHolder.format(*emptys)+"\n").join(rows))

    table.append(bottomHolder.format(*emptys))

    return "\n".join(table)
