import re

import IntCodeGen as icg

# for (!, != : Rust :: not, != : Python)
# "!" if not followed by "="
notRe = re.compile(r"!(?!=)")

def _getLoops(quadList = []):
    labelInd = {}
    loops = set()

    for ind, quad in enumerate(quadList):
        if quad.type == "LABEL":
            labelInd[quad.x] = ind
        if quad.type == "GOTO":
            if quad.x in labelInd:
                loops.add((labelInd[quad.x], ind))

    return labelInd, loops

# Constant Folding and Constant Propagation
def constantFoldingAndPropagation(quadList = []):
    newQuadList = [None for _ in quadList]
    vcd = {}
    labelInd, loops = _getLoops(quadList)

    ind, quad = 0, None
    while ind < len(quadList):
        quad = quadList[ind]
        inLoop = False
        for lb, ub in loops:
            if lb <= ind <= ub:
                inLoop = True
                break
        if inLoop:
            ind += 1
            continue

        if quad.type == "ASSIGN" and quad.y.type == "CONSTANT":
            vcd[quad.x.value] = ind
        elif quad.type == "ASSIGN" and quad.y.type in {"ID", "TEMPVAR"}:
            # Constant Propagation
            if quad.y.value in vcd:
                quadList[ind].y = icg.Operand(quadList[vcd[quad.y.value]].y.value, "CONSTANT")
                continue
        elif quad.type == "UNOP":
            # Constant Propagation
            if quad.y.type in {"ID", "TEMPVAR"}:
                if quad.y.value in vcd:
                    quadList[ind].y = icg.Operand(quadList[vcd[quad.y.value]].y.value, "CONSTANT")
                    continue
            # Constant Folding
            if quad.y.type == "CONSTANT":
                expr = "%s %s" % (quad.op, str(quad.y.value))
                expr = notRe.sub("not", expr.replace("&&", "and").replace("||", "or"))
                expr = eval(expr)
                quadList[ind] = icg.Quad(op = "ASSIGN", x = quad.x, y = icg.Operand(expr, "CONSTANT"))
                continue
        elif quad.type == "BINOP":
            # Constant Propagation
            if quad.y.type in {"ID", "TEMPVAR"}:
                if quad.y.value in vcd:
                    quadList[ind].y = icg.Operand(quadList[vcd[quad.y.value]].y.value, "CONSTANT")
                    continue
            # Constant Propagation
            if quad.z.type in {"ID", "TEMPVAR"}:
                if quad.z.value in vcd:
                    quadList[ind].z = icg.Operand(quadList[vcd[quad.z.value]].y.value, "CONSTANT")
                    continue
            # Constant Folding
            if quad.y.type == "CONSTANT" and quad.z.type == "CONSTANT":
                expr = "%s %s %s" % (str(quad.y.value), quad.op, str(quad.z.value))
                expr = notRe.sub("not", expr.replace("&&", "and").replace("||", "or"))
                expr = eval(expr)
                quadList[ind] = icg.Quad(op = "ASSIGN", x = quad.x, y = icg.Operand(expr, "CONSTANT"))
                continue
        elif quad.type == "IF":
            # Constant Propagation
            if quad.y.value in vcd:
                boolQuad = quadList[vcd[quad.y.value]]
                expr = eval(str(boolQuad.y.value))
                if expr:
                    quadList[ind] = icg.Quad(op = "GOTO", x = quad.x)
                    continue
                else:
                    quadList[ind] = icg.Quad(op = "EMPTY")
            # Constant Folding
            elif quad.y.type == "CONSTANT":
                if quad.y.value:
                    quadList[ind] = icg.Quad(op = "GOTO", x = quad.x)
                    continue
                else:
                    quadList[ind] = icg.Quad(op = "EMPTY")
        elif quad.type == "GOTO":
            # Skip loops
            if labelInd[quad.x] > ind:
                ind = labelInd[quad.x]
                continue
        ind += 1
    for ind, quad in enumerate(newQuadList):
        if not quad:
            newQuadList[ind] = quadList[ind]
    # print(vcd)
    return newQuadList

# Loop Invariant Code Motion
def loopInvariantCodeMotion(quadList = []):
    labelInd, loops = _getLoops(quadList)

    # variables in LHS
    vil = {loop:{} for loop in loops}
    
    for loop in loops:
        for ind in range(loop[0], loop[1]+1):
            quad = quadList[ind]
            if quad.type in {"ASSIGN", "BINOP", "UNOP"}:
                vil[loop][quad.x.value] = vil[loop].get(quad.x.value, 0) + 1
    for loop in loops:
        loopStartIndex = loop[0]
        for ind in range(loop[0], loop[1]+1):
            quad = quadList[ind]
            operands = [quad.y, quad.z]
            if quad.type in {"UNOP", "ASSIGN", "BINOP"}:
                if quad.x.type =="AE":
                    operands.append(quad.x)
            # if binop, unop or assign and can be moved out
            if \
            (
                quad.type in {"UNOP", "ASSIGN", "BINOP"}
                and
                all( map
                (
                    lambda operand: 
                        # For unop's z operand
                        True if operand == None
                        # Can definitrly move if operand is constant
                        else True if operand.type == "CONSTANT"
                        # Can't move if operand is being assigned something in loop
                        else False if \
                        (
                            operand.value if operand.type != "AE"
                            # Index value of the Array Element
                            else quad.x.value[quad.x.value.find("[")+1:-1]
                        ) in vil[loop]
                        # Operand is not on LHS in the loop
                        else True,
                    operands
                ))
            ):
                vil[loop][quad.x.value] -= 1
                if vil[loop][quad.x.value] <= 0:
                    del vil[loop][quad.x.value]
                quadList.insert(loopStartIndex, quadList.pop(ind))
                loopStartIndex += 1
    return quadList

def optimize(quadList = [], passes = [], verbose = 0):
    for pas in passes:
        if verbose > 0:
            print("Applying ", pas)
        quadList = pas(quadList)
        if verbose > 0:
            for lno, i in enumerate(quadList):
                print("%s: %s" % ("{:>2}".format(lno), i))
    return quadList
