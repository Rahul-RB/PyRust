import sys
sys.path.insert(0, '../src/')

import RustLexer
from RustLexer import RustLexer


def tokenList(clex):
	return list(iter(clex.token, None))


def tokenTypes(clex):
	return [i.type for i in tokenList(clex)]

def errorFunc(msg, line, column):
	fail(msg)

def onLbraceFunc():
	pass

def onRbraceFunc():
	pass

def typeLookupFunc(typ):
	if typ.startswith('mytype'):
		return True
	else:
		return False

# def test(obj,data):
# 	obj.lexer.input(data)
# 	while True:
# 		tok = obj.lexer.token()
# 		if not tok: 
# 			break
# 		print(tok)

m = RustLexer(errorFunc,onLbraceFunc,onRbraceFunc,typeLookupFunc)
m.build(optimize=False)
# m.build()

m.input("""
	fn main() {
	//this is a comment
	println!("Hello World!");
	/*
		this is one type of commetn
	*/
	panic!("asdfasdf");
	/* ** */
	/**/ 
	/*//*/ 
	////
	/// This is a doc comment type 1 	
	//! This is a doc comment type 2 
}""")

m.test()
print("Tokens being generated:")
print(tokenTypes(m))