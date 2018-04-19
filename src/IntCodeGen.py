#!/usr/bin/env python3

import RustAST

# Holds the generated IC for a given node
codeCache = {}

# Number of bytes occupied by each datatype
bytesMap = {
    "i8"  : 1,
    "i16" : 2,
    "i32" : 4,
    "i64" : 8,
    "u8"  : 1,
    "u16" : 2,
    "u32" : 4,
    "u64" : 8,
    "f32" : 4,
    "f64" : 8,
    "char": 4,
    "bool": 1
}

# Row in Quadruples data-structure
class Quad():
    def __init__(self, op=None, x=None, y=None, z=None):
        self.op = op
        self.x = x
        self.y = y
        self.z = z

        self.type = None
        if op in {"+", "-", "*", "/", "%", ">", "<", ">=", "<=", "!=", "==", "!", "&&", "||"}:
            self.type = "BINOP" if z else "UNOP"
        elif op in {"ASSIGN", "LABEL", "IF", "GOTO", "VAR", "ARR"}:
            self.type = op

    def __repr__(self):
        return "<Quad>: [op=%s, x=%s, y=%s, z=%s]" % (self.op, self.x, self.y, self.z)

    def __str__(self):
        if self.type == "BINOP":
            return "\t%s = %s %s %s" % (self.x, self.y, self.op, self.z)
        elif self.type == "UNOP":
            return "\t%s = %s %s" % (self.x, self.op, self.y)
        elif self.type == "ASSIGN":
            return "\t%s = %s" % (self.x, self.y)
        elif self.type == "LABEL":
            return "%s:" % self.x
        elif self.type in {"VAR", "ARR"}:
            return "\t%s %s = alloc %s" % (self.op.lower(), self.x, self.y)
        elif self.type == "IF":
            return "\tif %s goto %s" % (self.y, self.x)
        elif self.type == "GOTO":
            return "\tgoto %s" % (self.x)

        return "str: op=%s, x=%s, y=%s, z=%s" % (self.op, self.x, self.y, self.z)

# post order traversal of the ast to generate code bottom up
def _postOrderTraverse(node, offset=0):
    code = codeCache.get(node, None)

    if not code:
        for child_name, child in node.children():
            _postOrderTraverse(child)

        # TODO: For declarations, put variable in the symbolTable.

        gen = codeGens.get(type(node), None)

        if gen:
            codeCache[node] = gen(node)

# Count for temporary variables in the three address code
tc = -1
tTable = {}

def _getT():
    global tc
    tc += 1
    return "t" + str(tc)

# Count for labels (for each compound block) in the three address code
cc = -1
cTable = {}

def _getC():
    global cc
    cc += 1
    return "c" + str(cc)

# Utility Functions
def _joinCodes(*codeList):
    for code in codeList:
        if isinstance(code, Quad):
            yield code
        else:
            for quad in code:
                yield quad

def _getBytes(typ):
    length = int(typ["type"].get("length", 1))
    return str(bytesMap[typ["type"]["dataType"]] * length)

# Gets the operand representation of a node
def _getOperand(node):
    opRepr = ""

    if isinstance(node, RustAST.BinaryOp):
        opRepr = tTable[node]
    if isinstance(node, RustAST.UnaryOp):
        opRepr = tTable[node]
    elif isinstance(node, RustAST.Constant):
        opRepr = str(node.value)
    elif isinstance(node, RustAST.ID):
        opRepr = node.name
    elif isinstance(node, RustAST.ArrayElement):
        opRepr = node.arrId.name + "[%s]" % tTable[node.index]

    return opRepr

# IC generator functions
def _threeAddr_ID(idNode):
    return []

def _threeAddr_Constant(cNode):
    return []

def _threeAddr_BinaryOp(binOpNode):
    childCode = _joinCodes(codeCache[binOpNode.left], codeCache[binOpNode.right])

    if not tTable.get(binOpNode, None):
        tTable[binOpNode] = _getT()

    binaryOpQuad = Quad(op = binOpNode.op,
                        x  = tTable[binOpNode],
                        y  = _getOperand(binOpNode.left),
                        z  = _getOperand(binOpNode.right))
    return _joinCodes(childCode, binaryOpQuad)

def _threeAddr_UnaryOp(unOpNode):
    childCode = _joinCodes(codeCache[unOpNode.expr])

    if not tTable.get(unOpNode, None):
        tTable[unOpNode] = _getT()

    unaryOpQuad = Quad(op = unOpNode.op,
                       x  = tTable[unOpNode],
                       y  = _getOperand(unOpNode.expr))
    return _joinCodes(childCode, unaryOpQuad)

def _threeAddr_ArrayElement(aeNode):
    if not tTable.get(aeNode.index, None):
        tTable[aeNode.index] = _getT()

    aeQuad = Quad(op = "*",
                  x  = tTable[aeNode.index],
                  y  = _getOperand(aeNode.index),
                  z  = str(bytesMap[aeNode.arrId.type]))
    return _joinCodes(codeCache[aeNode.index], aeQuad)
    
def _threeAddr_Assignment(assnNode):
    childCode = _joinCodes(codeCache[assnNode.lvalue], codeCache[assnNode.rvalue])

    assnQuad = Quad(op = "ASSIGN",
                    x  = _getOperand(assnNode.lvalue),
                    y  = _getOperand(assnNode.rvalue))
    return _joinCodes(childCode, assnQuad)

def _threeAddr_Compound(compNode):
    childCode = _joinCodes(*(codeCache[child] for child in compNode.block_items))

    if not cTable.get(compNode, None):
        cTable[compNode] = _getC()

    compQuad = Quad(op = "LABEL", x = cTable[compNode])
    return _joinCodes(compQuad, childCode)

def _threeAddr_If(ifNode):
    afterIfC = _getC()
    elseCode = []

    if ifNode.iffalse:
        elseCode = codeCache[ifNode.iffalse]

    ifQuad = Quad(op = "IF",
                  x  = cTable[ifNode.iftrue],
                  y  = _getOperand(ifNode.cond))

    gotoAfterIf = Quad(op = "GOTO", x = afterIfC)

    labelAfterIf = Quad(op = "LABEL", x = afterIfC)
    # code = "\tif " + _getOperand(ifNode.cond) + " goto " + cTable[ifNode.iftrue] + elseCode + "\n\tgoto " + elseC
    return _joinCodes(codeCache[ifNode.cond], ifQuad, elseCode, gotoAfterIf, codeCache[ifNode.iftrue], labelAfterIf)

def _threeAddr_While(whileNode):
    condC = _getC()
    falseC = _getC()

    labelCond = Quad(op = "LABEL", x = condC)
    gotoCond = Quad(op = "GOTO", x = condC)

    condQuad = Quad(op = "IF",
                    x  = cTable[whileNode.stmt],
                    y  = _getOperand(whileNode.cond))

    gotoAfterWhile = Quad(op = "GOTO", x = falseC)
    labelAfterWhile = Quad(op = "LABEL", x = falseC)

    return _joinCodes(
        labelCond,
        codeCache[whileNode.cond],
        condQuad,
        gotoAfterWhile,
        codeCache[whileNode.stmt],
        gotoCond,
        labelAfterWhile)

def _threeAddr_Declaration(declNode):
    declQuad = Quad(op = "VAR",
                    x  = declNode.assn.lvalue.name,
                    y  = _getBytes(declNode.type))
    return _joinCodes(declQuad, codeCache[declNode.assn])

def _threeAddr_ArrayDecl(arrDeclNode):
    childCode = _joinCodes(*(codeCache[assn] for assn in arrDeclNode.assignments))
    declQuad = Quad(op = "ARR",
                    x  = arrDeclNode.assignments[0].lvalue.arrId.name,
                    y  = _getBytes(arrDeclNode.type))
    return _joinCodes(declQuad, childCode)

def _threeAddr_FileAST(fileASTNode):
    return codeCache[fileASTNode.ext[0]]

# List of functions that generate the code for each node
codeGens = {
    RustAST.FileAST:      _threeAddr_FileAST,
    RustAST.ArrayDecl:    _threeAddr_ArrayDecl,
    RustAST.Declaration:  _threeAddr_Declaration,
    RustAST.While:        _threeAddr_While,
    RustAST.ID:           _threeAddr_ID,
    RustAST.Constant:     _threeAddr_Constant,
    RustAST.BinaryOp:     _threeAddr_BinaryOp,
    RustAST.UnaryOp:      _threeAddr_UnaryOp,
    RustAST.ArrayElement: _threeAddr_ArrayElement,
    RustAST.Assignment:   _threeAddr_Assignment,
    RustAST.Compound:     _threeAddr_Compound,
    RustAST.If:           _threeAddr_If
}

# Reset all the global variables used
def _resetGlobals():
    codeCache = {}
    tc = -1
    tTable = {}
    cc = -1
    cTable = {}

# Returns a list of quads for the Intermediate Code
def generate(ast):
    _resetGlobals()
    _postOrderTraverse(ast)
    return codeCache[ast]
