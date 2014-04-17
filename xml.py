#!/usr/bin/python2.5

"""
 PyNarcissus S-expression converter.

 Converts a PyNarcissus parse tree into S-expressions.
"""

__author__ = "JT Olds"
__author_email__ = "jtolds@xnet5.com"
__date__ = "2009-03-24"
__all__ = ["convert", "UnknownNode", "OtherError", "ProgrammerError", "Error_"]

class Error_(Exception): pass
class UnknownNode(Error_): pass
class OtherError(Error_): pass
class ProgrammerError(OtherError): pass

import sys
import traceback
import jsparser as js
from lxml.builder import E
import lxml.etree as ET

def o(n, i, c, handledattrs=[]):
    attrs_ = {}
    for attr in handledattrs:
        attrs_[attr] = True
    subnodes_ = []
    had_error = False
    def check(attrs=[], optattrs=[], subnodes=0):
        if not (type(attrs) == list and type(optattrs) == list and
                type(subnodes) == int):
            raise ProgrammerError, "Wrong arguments to check(...)!"
        for attr in attrs: attrs_[attr] = True
        for attr in optattrs:
            if hasattr(n, attr): attrs_[attr] = True
        for i in xrange(subnodes):
            subnodes_.append(True)
    def props():
        if c["include_props"]:
            props_to_include = [x for x in ("lineno", "start", "end",
                    "readOnly") if hasattr(n, x)]
            if len(props_to_include) > 0:
                s = " (@"
                for prop in props_to_include:
                    s += " (%s %s)" % (prop.upper(), getattr(n, prop))
                return s +")"
        return ""
    try:
        check(attrs=["append", "count", "extend", "filename", "getSource",
                    "indentLevel", "index", "insert", "lineno", "pop",
                    "remove", "reverse", "sort", "tokenizer", "type", "type_"],
                    optattrs=["end", "start", "value"])
        print n.type
        if n.type == "ARRAY_INIT":
            check(subnodes=len(n))
            e = E.ARRAY_INIT()
            #return e
            s = "(ARRAY-INIT%s" % props()
            for x in n:
                if x is not None:
                    #s += " " + o(x,i,c)
                    e.append(o(x,i,c))
                else:
                    s += " NULL"
                    e.append(E.NULL())
            return e
            return s + ")"

        elif n.type == "ASSIGN":
            check(subnodes=2)
            s = "("
            if getattr(n[0],"assignOp", None) is not None:
                print n[0].assignOp
                s += "UPDATE%s " % props() + js.tokens[n[0].assignOp]
                #print js.tokens[n[0].assignOp]
                e = E.UPDATE()
                e.append(E.OPERATOR(js.tokens[n[0].assignOp]))
            else:
                s += "ASSIGN%s" % props()
                e = E.ASSIGN()
            e.append(o(n[0], i, c, handledattrs=["assignOp"]))
            e.append(o(n[1], i, c))
            return e
            #return s + " %s %s)" % (o(n[0], i, c, handledattrs=["assignOp"]),
                    #o(n[1], i, c))

        elif n.type == "BLOCK":
            check(subnodes=len(n))
            e = E.BLOCK()
            if len(n) > 0:
                for x in n:
                    e.append(o(x,i+"  ",c))
                return e
                #return ("(BLOCK%s\n  " % props()) + i + \
                        #("\n  "+i).join((o(x,i+"  ",c) for x in n)) + ")"
            return E.BLOCK()
            #return "(BLOCK%s)" % props()

        elif n.type in ("BREAK", "CONTINUE"):
            check(attrs=["target"], optattrs=["label"])
            return ET.Element(n.type)
            if hasattr(n,"label"):
                return "(%s%s %s)" % (n.value.upper(), props(), n.label)
            return "(%s%s)" % (n.value.upper(), props())

        elif n.type == "CALL":
            check(subnodes=2)
            return E.CALL(E.METHOD(o(n[0], i, c)), E.ARGUMENTS(o(n[1], i, c)))
            #return "(CALL%s %s%s)" % (props(), o(n[0], i, c), o(n[1], i, c))

        elif n.type == "CASE":
            check(attrs=["caseLabel","statements"])
            return E.CASE(E.LABEL(o(n.caseLabel,i,c)), E.STATEMENTS(o(n.statements,i,c)))
            return "(CASE%s %s %s)" % (props(), o(n.caseLabel,i,c),
                    o(n.statements,i,c))

        elif n.type == "CATCH":
            check(attrs=["block","guard","varName"])

            if n.guard is not None:
                return E.GUARDED_CATCH(n.varName, o(n.guard,i,c), o(n.block,i,c))
                return "(GUARDED-CATCH%s %s %s %s)" % (props(), n.varName,
                        o(n.guard,i,c), o(n.block,i,c))
            return E.CATCH(E.VAR(n.varName), E.BLOCK(o(n.block,i,c)))
            #return "(CATCH%s %s %s)" % (props(), n.varName, o(n.block,i,c))

        elif n.type == "COMMA":
            check(subnodes=2)
            e = E.COMMA()
            e.append(o(n[0],i,c))
            e.append(o(n[1],i,c))
            return e
            #return "(COMMA%s %s %s)" % (props(), o(n[0],i,c), o(n[1],i,c))

        elif n.type == "DEBUGGER":
            return E.DEBUGGER()
            return "(DEBUGGER%s)" % props()

        elif n.type == "DEFAULT":
            check(attrs=["statements"])
            return E.DEFAULT()
            return "(DEFAULT%s %s)" % (props(), o(n.statements,i,c))

        elif n.type in ("DELETE", "TYPEOF", "NEW", "UNARY_MINUS", "NOT",
                "VOID", "BITWISE_NOT", "UNARY_PLUS"):
            check(subnodes=1)
            e = ET.Element(n.type.replace('_', '-'))
            e.append(E.STATEMENT(o(n[0],i,c)))
            return e
            return "(%s%s %s)" % (n.type.replace('_', '-'), props(),
                    o(n[0],i,c))

        elif n.type == "DO":
            check(attrs=["body", "condition", "isLoop"])
            assert n.isLoop
            return E.DO_WHILE(o(n.condition,i,c), o(n.body,i,c))
            return "(DO-WHILE%s %s %s)" % (props(), o(n.condition,i,c),
                    o(n.body,i,c))

        elif n.type == "DOT":
            check(subnodes=2)
            return E.ATTRIBUTE(o(n[0],i,c), o(n[1],i,c))
            return "(ATTRIBUTE%s %s %s)" % (props(), o(n[0],i,c), o(n[1],i,c))

        elif n.type == "FUNCTION":
            check(attrs=["functionForm","params","body"],
                    optattrs=["name"])
            if n.functionForm == 0:
                e = E.DEF_FUNCTION(E.NAME(n.name))
                for param in n.params:
                    e.append(E.PARAM(param))
                e.append(E.BODY(o(n.body,i,c)))
                return e
                return "(DEF-FUNCTION%s (%s%s) %s)" % (props(), n.name,
                        "".join(" " + param for param in n.params),
                        o(n.body,i,c))
            else:
                #print n.params
                e = E.FUNCTION()
                for param in n.params:
                    e.append(E.PARAM(param))
                e.append(E.BODY(o(n.body,i,c)))
                return e
                return "(FUNCTION%s (%s) %s)" % (props(), " ".join(n.params),
                        o(n.body,i,c))

        elif n.type == "FOR":
            check(attrs=["body","setup","condition","update","isLoop"])
            assert n.isLoop
            if n.setup is not None: setup = o(n.setup,i,c)
            else: setup = "(BLOCK)"
            if n.condition is not None: condition = o(n.condition,i,c)
            else: condition = "(BLOCK)"
            if n.update is not None: update = o(n.update,i,c)
            else: update = "(BLOCK)"
            if n.body is not None: body = o(n.body,i+"  ",c)
            else: body = "(BLOCK)"
            return E.FOR()
            return "(FOR%s %s %s %s\n  %s%s)" % (props(), setup, condition,
                    update, i, body)

        elif n.type == "FOR_IN":
            check(attrs=["body","iterator","object","isLoop","varDecl"])
            assert n.isLoop
            return E.FOR_IN()
            s = "(FOR-IN"
            if n.varDecl:
                assert n.varDecl.type == "VAR"
                assert len(n.varDecl) == 1
                assert n.varDecl[0].type == "IDENTIFIER"
                assert n.varDecl[0].value == n.iterator.value
                s += "-VAR"
            return s + "%s %s %s %s)" % (props(), o(n.iterator,i,c),
                    o(n.object,i,c), o(n.body,i,c))

        elif n.type == "GROUP":
            check(subnodes=1)
            return E.GROUP(o(n[0],i,c))
            #return o(n[0],i,c)

        elif n.type == "HOOK":
            check(subnodes=3)
            return E.HOOK()
            return "(TERNARY%s %s %s %s)" % (props(),o(n[0],i,c),o(n[1],i,c),
                    o(n[2],i,c))

        elif n.type == "IDENTIFIER":
            check(optattrs=["initializer","name","readOnly"])

#            if getattr(n,"readOnly",False): assert hasattr(n,"initializer")
            if hasattr(n,"name"): assert n.name == n.value

            if hasattr(n,"initializer"):
                return E.INITVAR(E.IDENTIFIER(n.value), o(n.initializer, i, c))
                return "(INITVAR%s %s %s)" % (props(), n.value,
                        o(n.initializer, i, c))
            return E.IDENTIFIER(str(n.value))
            return str(n.value)

        elif n.type == "IF":
            check(attrs=["condition","thenPart","elsePart"])

            if n.elsePart:
                return E.IF_ELSE(E.CONDITION(o(n.condition,i,c)),
                                 E.THEN(o(n.thenPart,i+"  ",c)),
                                 E.ELSE(o(n.elsePart, i+"  ", c)))
                return "(IF-ELSE%s %s\n  %s%s\n  %s%s)" % (props(),
                        o(n.condition,i,c), i, o(n.thenPart,i+"  ",c), i,
                        o(n.elsePart, i+"  ", c))
            return E.IF(E.CONDITION(o(n.condition,i,c)),
                        E.THEN(o(n.thenPart, i+"  ",c)))
            #return "(IF%s %s\n  %s%s)" % (props(), o(n.condition,i,c), i,
                    #o(n.thenPart, i+"  ",c))

        elif n.type in ("INCREMENT", "DECREMENT"):
            check(optattrs=["postfix"], subnodes=1)
            if getattr(n, "postfix", False):
                e = ET.Element("POST_%s" % n.type.upper())
                #print e, o(n[0], i, c)
                e.append(o(n[0], i, c))
                return e
                #return "(POST-%s%s %s)" % (n.type, props(), o(n[0], i, c))
            e = ET.Element(n.type.upper())
            e.append(o(n[0], i, c))
            return e
            #return "(%s%s %s)" % (n.type, props(), o(n[0], i, c))

        elif n.type == "INDEX":
            check(subnodes=2)
            return E.ARRAY_INDEX(o(n[0],i,c), o(n[1],i,c))
            #return "(ARRAY-INDEX%s %s %s)" % (props(), o(n[0],i,c), o(n[1],i,c))

        elif n.type == "LABEL":
            check(attrs=["label","statement"])
            return E.LABEL()
            return "(LABELED-STATEMENT%s %s\n  %s%s)" % (props(), n.label, i,
                    o(n.statement, i+"  ", c))

        elif n.type == "LIST":
            check(subnodes=len(n))
            e = E.LIST()
            for x in n:
                e.append(o(x, i, c))
            return e
            #return ''.join((' ' + o(x, i, c) for x in n))

        elif n.type == "NEW_WITH_ARGS":
            check(subnodes=2)
            return E.NEW_WITH_ARGS(o(n[0],i,c), o(n[1],i,c))
            #return "(%s%s %s %s)" % (n.value.upper(), props(), o(n[0],i,c),
                    #o(n[1],i,c))

        elif n.type in ("NUMBER",):
            return E.NUMBER(str(n.value))

        elif n.type in ("TRUE", "FALSE", "THIS", "NULL"):
            return ET.Element(n.type)
            #return str(n.value).upper()

        elif n.type == "OBJECT_INIT":
            check(subnodes=len(n))
            e = E.OBJECT_INIT()
            if len(n) > 0:
                for x in n:
                    e.append(o(x,i+"  ",c))
                return e
                #return ("(OBJECT_INIT%s\n  " % props() + i +
                        #("\n  "+i).join(o(x,i+"  ",c) for x in n) + ")")
            return e
            #return "(OBJECT-INIT%s)" % props()

        elif n.type in ("PLUS", "LT", "EQ", "AND", "OR", "MINUS", "MUL", "LE",
                "NE", "STRICT_EQ", "DIV", "GE", "INSTANCEOF", "IN", "GT",
                "BITWISE_OR", "BITWISE_AND", "BITWISE_XOR", "STRICT_NE", "LSH",
                "RSH", "URSH", "MOD"):
            check(subnodes=2)
            e = ET.Element(n.type.replace('_', '-'))
            e.append(o(n[0],i,c))
            e.append(o(n[1],i,c))
            return e
            #return "(%s%s %s %s)" % (n.type.replace('_', '-'), props(),
                    #o(n[0],i,c), o(n[1],i,c))

        elif n.type == "PROPERTY_INIT":
            check(subnodes=2)
            e = E.PROPERTY_INIT()
            e.append(E.NAME(o(n[0],i,c)))
            e.append(E.VALUE(o(n[1],i,c)))
            return e
            #return "(PROPERTY%s %s %s)" % (props(), o(n[0],i,c), o(n[1],i,c))

        elif n.type == "REGEXP":
            return E.REGEXP()
            return "(REGEXP%s %r %r)" % (props(), n.value["regexp"],
                    n.value["modifiers"])

        elif n.type == "RETURN":
            if type(n.value) == str:
                return E.RETURN(n.value)
                #return "(RETURN%s %r)" % (props(), n.value)
            return E.RETURN(o(n.value, i, c))
            #return "(RETURN%s %s)" % (props(), o(n.value, i, c))

        elif n.type == "SCRIPT":
            check(attrs=["funDecls","varDecls"], subnodes=len(n))
            e = E.SCRIPT()
#            sys.stderr.write("WARNING: skipping funDecls and varDecls\n")
            if len(n) > 0:
                for x in n:
                    e.append(o(x,i+"  ",c))
                return e
                #return ("(SCRIPT%s\n  " % props() + i +
                        #("\n  "+i).join((o(x,i+"  ",c) for x in n)) + ")")
            return e
            #return "(SCRIPT%s)" % props()

        elif n.type == "SEMICOLON":
            check(attrs=["expression"])
            if not n.expression:
                #return "(BLOCK)"
                return E.BLOCK()
            #return E.SEMICOLON(o(n.expression, i, c))
            #print n.expression
            return o(n.expression, i, c)

        elif n.type == "STRING":
            return E.STRING(n.value)
            #return repr(n.value)

        elif n.type == "SWITCH":
            check(attrs=["cases", "defaultIndex", "discriminant"])
            assert (n.defaultIndex == -1 or
                    n.cases[n.defaultIndex].type == "DEFAULT")
            return E.SWITCH()
            #return "(SWITCH%s %s\n  %s%s)" % (props(), o(n.discriminant,i,c), i,
                    #("\n  "+i).join(o(x,i+"  ",c) for x in n.cases))

        elif n.type == "THROW":
            check(attrs=["exception"])
            return E.THROW(o(n.exception,i,c))
            #return "(THROW%s %s)" % (props(), o(n.exception,i,c))

        elif n.type == "TRY":
            check(attrs=["catchClauses","tryBlock"], optattrs=["finallyBlock"])

            if hasattr(n,"finallyBlock"):
                e = E.TRY_FINALLY()
                e.append(o(n.tryBlock,i+"  ",c))
                for x in n.catchClauses:
                    e.append(o(x,i+"  ",c))
                e.append(o(n.finallyBlock,i+"  ",c))
                return e
                #return "(TRY-FINALLY%s\n  " % props() + i + ("\n  "+i).join(
                        #[o(n.tryBlock,i+"  ",c)] + [o(x,i+"  ",c)
                        #for x in n.catchClauses] + \
                        #[o(n.finallyBlock,i+"  ",c)]) + ")"
            e = E.TRY()
            e.append(o(n.tryBlock,i+"  ",c))
            for x in n.catchClauses:
                e.append(o(x,i+"  ",c))
            return e
            #return "(TRY%s\n  " % props() + i + ("\n  "+i).join(
                    #[o(n.tryBlock,i+"  ",c)] + [o(x,i+"  ",c)
                    #for x in n.catchClauses]) + ")"

        elif n.type in ("VAR", "CONST"):
            check(subnodes=len(n))
            e = ET.Element(n.type)
            #e.append(E.VALUE(n.value.upper()))
            for x in n:
                e.append(o(x,i,c))
            return e
            return ("(%s%s " % (n.value.upper(), props())) + " ".join((o(x,i,c)
                    for x in n)) + ")"

        elif n.type == "WITH":
            check(attrs=["body", "object"])
            return E.WITH(o(n.object,i,c), o(n.body,i,c))
            sys.stderr.write("WARNING: A bad person wrote the code being "
                    "parsed. Don't use 'with'!\n")
            return "(WITH%s %s %s)" % (props(), o(n.object,i,c), o(n.body,i,c))

        elif n.type == "WHILE":
            check(attrs=["condition","body","isLoop"])
            assert n.isLoop
            cond = E.CONDITION(o(n.condition,i,c))
            body = E.BODY(o(n.body, i+"  ",c))
            return E.WHILE(cond, body)
            #return "(WHILE%s %s\n  %s%s)" % (props(), o(n.condition,i,c), i,
                    #o(n.body, i+"  ",c))

        else:
            raise UnknownNode, "Unknown type %s" % n.type
    except Exception, e:
        traceback.print_exc(e)
        raise e
        #had_error = True
        #raise OtherError("%s\nException in node %s on line %s" % (e, n.type,
                #getattr(n, "lineno", None)))
    finally:
        if not had_error:
            realkeys = [x for x in dir(n) if x[:2] != "__"]
            for key in realkeys:
                if key not in attrs_:
                    continue
                    raise ProgrammerError, "key '%s' unchecked on node %s!" % (
                            key, n.type)
            if len(realkeys) != len(attrs_):
                for key in attrs_:
                    if key not in realkeys:
                        raise ProgrammerError, ("key '%s' checked "
                                "unnecessarily on node %s!" % (key, n.type))
            if len(subnodes_) != len(n):
                raise ProgrammerError, ("%d subnodes out of %d checked on node "
                        "%s" % (len(subnodes_), len(n), n.type))

def convert(parsetree, include_props=False):
    """Takes a PyNarcissus parse tree and returns a string of S-expressions

    Args:
        parsetree: the PyNarcissus parse tree
        include_props: if true, the s-expressions have additional information
            included via @ attribute expressions, such as line-number.
    Returns:
        string
    Raises:
        UnknownNode: if a node hasn't been properly accounted for in the
            conversion
        ProgrammerError: if the conversion routine wasn't written with the best
            understanding of the parse tree
        OtherError: if some other error happened we didn't understand.
    """

    return o(parsetree, "", {"include_props": include_props})

if __name__ == "__main__":
    try:
        include_props = (sys.argv[1] == "--props")
    except:
        include_props = False

    tree = js.parse(sys.stdin.read(), include_props)
    print tree

    parsed = convert(tree)
    print ET.tostring(parsed, pretty_print=True)
    #print parsed.xpath('.//STRING/text()')
