import string

# C Keywords
# ------------------------------------------------------------------------
types = ["short", "int", "long", "float", "double", "char", "void", "bool"]
containers = ["enum", "struct", "union", "typedef"]
modifiers = [ "const", "volatile", "extern", "static", "register", "signed", "unsigned"]
flow = [ "if", "else",
         "goto", 
         "case", "default", 
         "continue", "break", ]
loops = ["for", "do", "while" "switch", ]
keywords = types + containers + modifiers + flow + loops + [ "return", "sizeof" ]

unary_operations = ["-","+","*","&","~"]
binary_operations = ["+","-","/","*",
                     "^","&","|",
                     "<<",">>",
                     "<",">", "<=",">=",
                     "&&","||","==","!=",
                     "=",
                     "+=","-=","/=","*=",
                     "^=","&=","|=",
                     "<<=",">>=",
                     ".","->"
                    ]

# Utitlity Functions
# ------------------------------------------------------------------------
def is_keyword(token):
    return token in keywords

def isonly(s,chars):
    return len(s) and all(map(lambda c: c in chars, s))

# Token Lexer
# ------------------------------------------------------------------------
class Token(str):
    def set(self,line=0,pos=0):
        self.line = line
        self.pos = pos
    def position(self):
        return (self.line,self.pos)
    def trim(self):
        ret = Token( str(self)[:-1] )
        ret.set(self.line, self.pos )
        return ret
    def __add__(self,other):
        ret = Token( str(self) + str(other))
        ret.set(self.line, self.pos )
        return ret

def escape_character( c, line, pos ):
    if c == "n":
        curtoken = Token("\n")
        curtoken.set(line,pos)
    elif c == "t":
        curtoken = Token("\t")
        curtoken.set(line,pos)
    elif c == "'":
        curtoken = Token("\'")
        curtoken.set(line,pos)
    elif c == '"':
        curtoken = Token("\"")
        curtoken.set(line,pos)
    elif c == '\\':
        curtoken = Token("\\")
        curtoken.set(line,pos)
    else:
        print "Lex Error at Line %d / Char %d - Character '%c' cannot be escaped" % (line, pos, c)
        assert(0)
    return curtoken


def tokenize( s ):
    symbols = string.punctuation.replace("_","")
    digital = string.digits
    floating = string.digits + "."
    hexal = string.hexdigits
    line = 1
    pos = 0
    curtoken = Token("")
    curtoken.set(line,pos)
    in_string = False
    in_char = False
    in_comment = False
    in_pragma = False
    for c in s:
        pos += 1
        #print (c,curtoken)
        if in_comment or in_pragma:
            if c=="\n":
                if curtoken.startswith("//") or curtoken.startswith("#") :
                    curtoken = Token("")
                    curtoken.set(line,pos)
                    in_comment = False
                    in_pragma = False
                line += 1
            elif c=='/' and curtoken.endswith("*"):
                print "End */"
                curtoken = Token("")
                curtoken.set(line,pos)
                in_comment = False
            else:
                curtoken += c
        elif c == '"' and not in_char:
            if not in_string:
                # Start of new String
                if curtoken != "":
                    yield curtoken
                in_string = True
                curtoken = Token('"')
                curtoken.set(line,pos)
            elif len(curtoken) and curtoken[-1] == '\\':
                curtoken = Token(curtoken[:-1] + "\"")
                curtoken.set(line,pos)
            else:
                # End of String
                in_string = False
                curtoken += c
                yield curtoken
                curtoken = Token("")
                curtoken.set(line,pos)
        elif in_string:
            if curtoken.endswith('\\'):
                # Char Symbols
                curtoken = curtoken.trim()
                curtoken += escape_character( c, line, pos )
            else:
                curtoken += Token(c)
        elif in_char:
            if curtoken.endswith("\\"):
                # Escape this Character
                curtoken = curtoken.trim()
                curtoken += escape_character(c, line, pos)
            elif c == "'":
                # End of Character:
                curtoken += c
                if len(curtoken) != 3:
                    print "Lex Error at Line %d / Char %d - Character '%s' is too long." % (curtoken.line, curtoken.pos, c)
                yield curtoken
                in_char = False
                curtoken = Token("")
                curtoken.set(line,pos)
            else:
                curtoken += c
        elif c == "'" and not in_string:
            # Start of Character:
            if curtoken != "":
                yield curtoken
            curtoken = Token("'")
            curtoken.set(line,pos)
            in_char = True
        elif c == "#":
            if curtoken != "":
                yield curtoken
            curtoken = Token("#")
            curtoken.set(line,pos)
            in_pragma = True
        elif curtoken=="/" and c=="*":
            print "Start /*"
            curtoken += Token(c)
            in_comment = True
        elif c == "/" and curtoken == "/":
            curtoken += Token(c)
            in_comment = True
        elif c in symbols:
            if (curtoken+c) in binary_operations:
                curtoken = Token((curtoken+c))
                curtoken.set(line,pos)
            elif c=='.' and isonly(curtoken, floating):
                curtoken += Token(c)
            else:
                if curtoken != "":
                    yield curtoken
                curtoken = Token(c)
                curtoken.set(line,pos)
        else:
        # Non-Symbols
            if isonly(curtoken, symbols):
                yield curtoken
                curtoken = Token("")
                curtoken.set(line,pos)
            if c in string.whitespace:
                if curtoken != "":
                    yield curtoken
                if c == "\n":
                    #yield c
                    line += 1
                    pos = 0
                curtoken = Token("")
                curtoken.set(line,pos)
            # Int
            elif c in digital and isonly(curtoken,digital):
                curtoken += Token(c)
            # Float
            elif c in floating and isonly(curtoken, floating):
                curtoken += Token(c)
            # Hex
            elif curtoken.startswith("0x") and c in hexal and isonly(curtoken[2:], hexal):
                curtoken += Token(c)
            elif curtoken == "0" and c in "xX":
                curtoken += Token(c)
            else:
                curtoken += Token(c)
    if curtoken not in string.whitespace:
        yield curtoken

# Token Parser
# ------------------------------------------------------------------------
def parse_value(tokens):
    if tokens[0] in unary_operations:
        unary = tokens.pop(0)
        inner,tokens = parse_value( tokens )
        #print "Value",unary,name
        return ('Math',(unary,inner)),tokens
    elif is_keyword(tokens[0]):
        print "Parse Error at Line %d / Char %d - Value Expected at '%s', found keyword" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    elif tokens[0] in string.punctuation:
        print "Parse Error at Line %d / Char %d - Value Expected at '%s', found punctuation" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    elif tokens[1] == "(":
        return parse_call( tokens )
    elif tokens[1] == "[":
        name = tokens.pop(0)
        if tokens[0]!="[":
            print "Parse Error at Line %d / Char %d - Accessor must have '[', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
            assert(0)
        tokens.pop(0)
        index,tokens = parse_expression( tokens )
        if tokens[0]!="]":
            print "Parse Error at Line %d / Char %d - Function must have ']', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
            assert(0)
        tokens.pop(0)
        return ('Index',(name, index) ),tokens
    else:
        name = tokens.pop(0)
        #print "Value",name
        return ('Value',name),tokens

def parse_call(tokens ):
    name = tokens.pop(0)
    if tokens[0]!="(":
        print "Parse Error at Line %d / Char %d - Function must have '(', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    # Get the Arguements
    arguments = []
    while len(tokens):
        # Reached end of Argument List
        if tokens[0]==")":
            break
        arg,tokens = parse_expression( tokens )
        arguments.append( arg )
        if tokens[0]!=",":
            break
        else:
            tokens.pop(0)
    
    if tokens[0]!=")":
        print "Parse Error at Line %d / Char %d - Function must have ')', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    return ('Call',(name,arguments)),tokens

def parse_if( tokens ):
    if tokens[0] not in ["if"]:
        print "Parse Error at Line %d / Char %d - if must start with 'if', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    if tokens[0]!="(":
        print "Parse Error at Line %d / Char %d - if must have '(', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    test,tokens = parse_expression( tokens )
    
    if tokens[0]!=")":
        print "Parse Error at Line %d / Char %d - if must have ')', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    action,tokens = parse_statement_or_block(tokens)
    
    alternative = None
    if tokens[0]=="else":
        tokens.pop(0)
        alternative,tokens = parse_statement_or_block(tokens)
    
    #print "If",test,action
    return ("If",(test,action,alternative)), tokens

def parse_while( tokens ):
    if tokens[0] not in ["while"]:
        print "Parse Error at Line %d / Char %d - while must start with 'while', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    if tokens[0]!="(":
        print "Parse Error at Line %d / Char %d - while must have '(', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    test,tokens = parse_expression( tokens )
    
    if tokens[0]!=")":
        print "Parse Error at Line %d / Char %d - if must have ')', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    action,tokens = parse_statement_or_block(tokens)
    
    #print "While",test,action
    return ("While",(test,action)), tokens

def parse_for( tokens ):
    if tokens[0] not in ["for"]:
        print "Parse Error at Line %d / Char %d - for must start with 'for', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    if tokens[0]!="(":
        print "Parse Error at Line %d / Char %d - for must have '(', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    init,tokens = parse_expression( tokens )
    
    if tokens[0]!=";":
        print "Parse Error at Line %d / Char %d - for must have first ';', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    test,tokens = parse_expression( tokens )
    
    if tokens[0]!=";":
        print "Parse Error at Line %d / Char %d - for must have second ';', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    step,tokens = parse_expression( tokens )
    
    if tokens[0]!=")":
        print "Parse Error at Line %d / Char %d - if must have ')', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    action,tokens = parse_statement_or_block(tokens)
    
    #print "For",init,test,step,action
    return ("For",(init,test,step,action)), tokens

def parse_expression( tokens ):
    # This should be a tree not a list
    expression = []
    while len(tokens):
        #TODO: Add Unary Operators
        #TODO: Add Ternary Operator "?:"
        #TODO: Add Comma
        #TODO: Symbol Symbol should be illegal
        if tokens[0] == "(":
            tokens.pop(0)
            inner,tokens = parse_expression( tokens )
            expression.append( inner )
            if tokens[0] != ")":
                print "Parse Error at Line %d / Char %d -')' expected after expression %s" % inner
                assert(0)
            tokens.pop(0)
            break
        elif tokens[0] == ";":
            break
        elif tokens[0] == ",":
            break
        elif tokens[0] == ")":
            break
        elif tokens[0] == "]":
            break
        else:
            value,tokens = parse_value( tokens )
            expression.append( value )
            # TODO: Add Right/Left Associations
            if tokens[0] in binary_operations:
                symbol = tokens.pop(0)
                right,tokens = parse_expression( tokens )
                expression.append( ("Math", (symbol, right) ) )
    #print "Expression", tuple(expression)
    return ("Expression", tuple(expression)),tokens

def parse_struct( tokens ):
    struct = []
    if tokens[0] not in ["struct","union"]:
        print "Parse Error at Line %d / Char %d - struct must start with 'struct' or 'union', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    kind = "Struct" if (tokens.pop(0) == "struct") else "Union"
    if tokens[0]!="{":
        print "Parse Error at Line %d / Char %d - Blocks must start with 'struct {', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    while len(tokens):
        if tokens[0]=="}":
            break
        if tokens[0]=="struct" or tokens[0]=="union":
            inner,tokens = parse_struct(tokens)
            struct.append(inner)
            if tokens[0]!=";":
                print "Parse Error at Line %d / Char %d - struct values must end in ';', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
                assert(0)
            tokens.pop(0)
        else:
            type = tokens.pop(0)
            name = tokens.pop(0)
            if tokens[0]!=";":
                print "Parse Error at Line %d / Char %d - struct values must end in ';', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
                assert(0)
            tokens.pop(0)
            struct.append(("Declaration", [(type,name)]))
    if tokens[0]!="}":
        print "Parse Error at Line %d / Char %d - Blocks must start with 'struct {', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    #print kind, struct
    return (kind, struct), tokens

def parse_declaration( tokens ):
    assignments = []
    type = tokens.pop(0)
    #print "Type %s" % type
    while len(tokens):
        name = tokens.pop(0)
        #print "Name %s" % name
        if not is_keyword(name):
            if tokens[0]=="=":
                # Declaration value
                tokens.pop(0)
                expression,tokens = parse_expression( tokens )
                assignments.append((type,name,expression))
            else:
                # Non-Assignmed value
                assignments.append((type,name))
        if tokens[0]==",":
            tokens.pop(0)
            continue
        elif tokens[0]==";":
            break
        if len(tokens):
            print "Parse Error at Line %d / Char %d - unknown token encountered at '%s'" % (tokens[0].line, tokens[0].pos, tokens[0])
            assert(0)
    return ("Declaration", assignments), tokens

def parse_function( tokens ):
    returntype = tokens.pop(0)
    name = tokens.pop(0)
    
    if tokens[0]!="(":
        print "Parse Error at Line %d / Char %d - for must have '(', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    # Arguements
    arguments = []
    while len(tokens):
        # Reached end of Argument List
        if tokens[0]==")":
            break
        type = tokens.pop(0)
        if type == "void" and tokens[0]==")":
            break
        name = tokens.pop(0)
        if is_keyword(name):
            print "Parse Error at Line %d / Char %d - Function argument #%d's name '%s' cannot be a keyword" % (len(arguments)+1, name)
            assert(0)
        arguments.append( (type,name) )
        if tokens[0]!=",":
            break
        else:
            tokens.pop(0)
    
    if tokens[0]!=")":
        print "Parse Error at Line %d / Char %d - functions arguments must have ')', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    
    if tokens[0]!="{":
        print "Parse Error at Line %d / Char %d - functions must have '{', found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    block,tokens = parse_block( tokens );
    #print "Function",returntype,name,arguments,block
    return ("Function",(returntype,name,arguments,block)), tokens

def parse_statement( tokens ):
    statement = []
    needsemicolon = True
    if tokens[0] == "if":
        statement,tokens = parse_if( tokens )
        needsemicolon = False
    elif tokens[0] == "while":
        statement,tokens = parse_while( tokens )
        needsemicolon = False
    elif tokens[0] == "for":
        statement,tokens = parse_for( tokens )
        needsemicolon = False
    elif tokens[0] in types and tokens[2] == "(":
        statement,tokens = parse_function( tokens )
        needsemicolon = False
    elif tokens[0] in types:
        statement,tokens = parse_declaration( tokens )
    elif tokens[0]=="struct" or tokens[0]=="union":
        statement,tokens = parse_struct(tokens)
    elif tokens[0] == "break":
        statement = ("Break",None)
        tokens.pop(0)
    elif tokens[0] == "continue":
        statement = ("Continue",None)
        tokens.pop(0)
    elif tokens[0] == "return":
        tokens.pop(0)
        expression,tokens = parse_expression( tokens );
        statement = ("Return",expression)
    else:
        statement,tokens = parse_expression(tokens)
    if needsemicolon:
        if tokens[0]==";":
            tokens.pop(0)
        else:
            print "Parse Error at Line %d / Char %d - Statements must end in a semicolon: found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
            assert(0)
    #print "Statement",statement,"\n"
    return statement, tokens

def parse_block( tokens ):
    if tokens[0]!="{":
        print "Parse Error at Line %d / Char %d - Blocks must start with a {, found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    block = []
    while len(tokens) and tokens[0] != "}":
        statement,tokens = parse_statement_or_block(tokens)
        block.append( statement )
    if tokens[0]!="}":
        print "Parse Error at Line %d / Char %d - Blocks must end with a }, found %s instead" % (tokens[0].line, tokens[0].pos, tokens[0])
        assert(0)
    tokens.pop(0)
    #print "Block", block
    return ("Block",block), tokens

def parse_statement_or_block( tokens ):
    if tokens[0]=="{":
        return parse_block( tokens )
    else:
        return parse_statement( tokens )

# Print Abstract Syntax Tree (AST)
# ------------------------------------------------------------------------
def print_thing( thing, depth=0 ):
    name,value = thing
    #print "\t"*depth+ "THING:", name,value
    if name == "Block":
        print "\t"*depth+ "Block"
        print "\t"*depth+ "{"
        for statement in value:
            print_thing(statement,depth+1)
        print "\t"*depth+ "}"
    elif name == "Statement":
        print "\t"*depth+ "Statement"
        pass
    elif name == "Math":
        print "\t"*depth+ "Math"
        symbol, expression = value
        print "\t"*depth+symbol
        print_thing(expression,depth+1)
    elif name == "Value":
        print "\t"*depth+ "Value"
        print "\t"*depth+ value
    elif name == "Index":
        print "\t"*depth+ "Index"
        name, expression = value
        print "\t"*depth+ name
        print "\t"*depth+ "["
        print_thing(expression,depth+1)
        print "\t"*depth+ "]"
    elif name == "Declaration":
        print "\t"*depth+ name
        for declaration in value:
            if len(declaration) == 2:
                type,name = declaration
                print "\t"*depth+ type,name 
            else:
                type,name,expression = declaration
                print "\t"*depth+ type,name, "= ("
                print_thing(expression,depth+1)
                print "\t"*depth+ ")"
    elif name == "Expression":
        print "\t"*depth+ name
        print "\t"*depth+ "("
        for expression in value:
            print_thing(expression,depth+1)
        print "\t"*depth+ ")"
    elif name=="Struct" or name=="Union":
        print "\t"*depth+ name
        print "\t"*depth+ "{"
        for expression in value:
            print_thing(expression,depth+1)
        print "\t"*depth+ "}"
    elif name=="If":
        test,action,alternative = value
        print "\t"*depth+ name
        print "\t"*depth+ "("
        print_thing(test,depth+1)
        print "\t"*depth+ ")"
        print "\t"*depth+ "{"
        print_thing(action,depth+1)
        print "\t"*depth+ "}"
        if alternative:
            print "\t"*depth+ "else"
            print "\t"*depth+ "{"
            print_thing(alternative,depth+1)
            print "\t"*depth+ "}"
    elif name=="While":
        test,action = value
        print "\t"*depth+ name
        print "\t"*depth+ "("
        print_thing(test,depth+1)
        print "\t"*depth+ ")"
        print "\t"*depth+ "{"
        print_thing(action,depth+1)
        print "\t"*depth+ "}"
    elif name=="For":
        init,test,step,action = value
        print "\t"*depth+ name
        print "\t"*depth+ "("
        print "\t"*depth+ "INIT"
        print_thing(init,depth+1)
        print "\t"*depth+ "TEST"
        print_thing(test,depth+1)
        print "\t"*depth+ "STEP"
        print_thing(step,depth+1)
        print "\t"*depth+ ")"
        print "\t"*depth+ "{"
        print_thing(action,depth+1)
        print "\t"*depth+ "}"
    elif name=="Break":
        print "\t"*depth+ name
    elif name=="Continue":
        print "\t"*depth+ name
    elif name=="Return":
        print "\t"*depth+ name
        print_thing(value,depth+1)
    elif name=="Function":
        returntype,name,arguments,block = value
        print "\t"*depth+ returntype
        print "\t"*depth+ name
        print "\t"*depth+ "("
        for argtype,argname in arguments:
            print "\t"*(depth+1)+ argtype,argname
        print "\t"*depth+ ")"
        print "\t"*depth+ "{"
        print_thing(block,depth+1)
        print "\t"*depth+ "}"
    elif name=="Call":
        func,arguments = value
        print "\t"*depth+ name
        print "\t"*depth+ func
        print "\t"*depth+ "("
        for arg in arguments:
            print_thing(arg,depth+1)
        print "\t"*depth+ ")"
    else:
        print "\t"*depth+ "Warning!  Unknown type"
        print "\t"*depth+ str(name)
        print "\t"*depth+ str(value)

if __name__ == "__main__":
    import sys
    import glob
    files = []
    for arg in sys.argv[1:]:
        for filenames in glob.glob( arg ):
                files.append( filenames )
    for filename in files:
        print
        data = open(filename,"r").read()
        tokens = list(tokenize( data ))
        # Print out the Lexer
        print "Lexical Analysis:"
        for i,token in enumerate( tokens ):
            loc = ("%d (%d,%d): " %(i, token.line, token.pos)).ljust(16)
            print loc,token

        # Parse tokens
        print
        print "Structural Analysis:"
        while len(tokens):
            block, tokens = parse_statement_or_block( tokens )
            print_thing(block)
            
