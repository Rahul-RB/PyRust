import re

fp = open("file1.rs","r")
l = fp.readlines()
inp = ''.join(l)

def stripComments(text):
    return re.sub('//.*?(\r\n?|\n)|/\*.*?\*/', '', text, flags=re.S)

print(stripComments(inp))