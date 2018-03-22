class SymbolTable(object):
	"""docstring for SymbolTable"""
	def __init__(self):
		self.symbolTable = []

	def insert(self,symbolName,symbolType,symbolValue):
		if(lookup(symbolName)==False):
			return False
		self.symbolTable[-1][symbolName] = [symbolType,symbolValue]

	def lookup(self,symbolName):
		if(symbolName in self.symbolTable[-1]):
			return False
		return True

	def printSymbolTable(self):
		for scope in list(reversed(symbolTable)):
			for symName,attributes in scope:
				print(symName,"\t",attributes)