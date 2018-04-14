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
    joined = "\n".join((code for code in codeList if code != ""))

    if len(joined) > 1:
        return joined + "\n"
    return ""

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
    return ""

def _threeAddr_Constant(cNode):
    return ""

def _threeAddr_BinaryOp(binOpNode):
    childCode = _joinCodes(codeCache[binOpNode.left], codeCache[binOpNode.right])

    if not tTable.get(binOpNode, None):
        tTable[binOpNode] = _getT()

    return childCode + "\t" + tTable[binOpNode] + " = " + _getOperand(binOpNode.left) + " " + binOpNode.op + " " + _getOperand(binOpNode.right)

def _threeAddr_UnaryOp(unOpNode):
    childCode = _joinCodes(codeCache[unOpNode.expr])

    if not tTable.get(unOpNode, None):
        tTable[unOpNode] = _getT()

    return childCode + "\t" + tTable[unOpNode] + " = " + unOpNode.op + " " + _getOperand(unOpNode.expr)

def _threeAddr_ArrayElement(aeNode):
    if not tTable.get(aeNode.index, None):
        tTable[aeNode.index] = _getT()

    return _joinCodes(codeCache[aeNode.index],
        "\t" + tTable[aeNode.index] + " = " + _getOperand(aeNode.index) + " * " + str(bytesMap[aeNode.arrId.type]))[:-1]
    
def _threeAddr_Assignment(assnNode):
    childCode = _joinCodes(codeCache[assnNode.lvalue], codeCache[assnNode.rvalue])

    return childCode + "\t" + _getOperand(assnNode.lvalue) + " " + assnNode.op + " " + _getOperand(assnNode.rvalue)

def _threeAddr_Compound(compNode):
    childCode = _joinCodes(*(codeCache[child] for child in compNode.block_items))

    if not cTable.get(compNode, None):
        cTable[compNode] = _getC()

    return cTable[compNode] + ":" + childCode[:-1]

def _threeAddr_If(ifNode):
    elseC = _getC()
    elseCode = ""

    if ifNode.iffalse:
        elseCode = "\n" + codeCache[ifNode.iffalse]

    code = "\tif " + tTable[ifNode.cond] + " goto " + cTable[ifNode.iftrue] + elseCode + "\n\tgoto " + elseC
    return _joinCodes(codeCache[ifNode.cond], code, codeCache[ifNode.iftrue]) + elseC + ":"

def _threeAddr_While(whileNode):
    condC = _getC()
    falseC = _getC()

    return _joinCodes(
        condC + ":" + codeCache[whileNode.cond], 
        "\tif " + _getOperand(whileNode.cond) + " goto " + cTable[whileNode.stmt],
        "\tgoto " + falseC,
        codeCache[whileNode.stmt],
        "\tgoto " + condC,
        falseC + ":")[:-1]

def _threeAddr_Declaration(declNode):
    return _joinCodes(
        "\t.var " + declNode.assn.lvalue.name + " = alloc " + _getBytes(declNode.type),
        codeCache[declNode.assn])[:-1]

def _threeAddr_ArrayDecl(arrDeclNode):
    childCode = _joinCodes(*(codeCache[assn] for assn in arrDeclNode.assignments))
    return _joinCodes(
        "\t.arr " + arrDeclNode.assignments[0].lvalue.arrId.name + " = alloc " + _getBytes(arrDeclNode.type),
        childCode)[:-2]

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

# Returns a string for the Intermediate Code
def generate(ast):
    _resetGlobals()
    _postOrderTraverse(ast)
    return codeCache[ast]
