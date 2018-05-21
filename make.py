#!/usr/bin/python3

import os, sys, subprocess, string, textwrap

if "--help" in sys.argv:
    raise SystemExit("""
Usage: ./make.py [-i] [--dump]
    -i: use dot's X11 viewer
    --dump: print compiled source to stdout
""")

mydir = os.path.dirname(sys.argv[0])
os.chdir(mydir)

# Build
bulk = """digraph {
    node[style = "filled, rounded"; shape = box];
"""
top = []
for name in os.listdir("./src/"):
    if not name.endswith(".dot"): continue
    filename = "./src/" + name
    name = name.replace(".dot", "")
    clean_name = name.replace('_', ' ')
    bulk += "\t// ### " + filename + "\n"
    bulk += "\tsubgraph " + "\"cluster_" + name + "\" {\n"
    bulk += "\t\tlabel = < <b>" + clean_name + "</b> >;\n"
    bulk += "\t\tstyle = filled;\n"
    bulk += "\t\tcolor = gray92;\n"
    bulk += '\t\t' + open(filename).read().replace('\n', '\n\t\t') + '\n'
    bulk += "\t}\n"
    top += ['"' + clean_name + '"']

bulk += "}\n"

# Create notes with this syntax: @node "some long comment"
class Parser:
    def __init__(self, src):
        self.src = src

    def try_eat(self, c):
        if self.src.startswith(c):
            self.src = self.src[len(c):]
            return True

    def eat(self):
        if not self.src: return ''
        r = self.src[0]
        self.src = self.src[1:]
        return r

    def eat_line_comment(self):
        if not self.try_eat("//"): return
        r = "//"
        while self.src and self.src[0] != '\n':
            r += self.eat()
        return r

    def eat_c_comment(self):
        if not self.try_eat("/*"): return
        r = "/*"
        while self.src and not self.src.startswith("*/"):
            r += self.eat()
        if self.src.startswith("*/"):
            self.src = self.src[2:]
        r += "*/"
        return r

    def eat_str(self):
        if not self.try_eat('"'): return ""
        r = '"'
        while self.src:
            c = self.eat()
            r += c
            if c == '\\':
                r += self.eat()
                continue
            elif c == '"':
                break
        return r

    def eat_ident(self):
        r = ""
        while self.src:
            c = self.src[0]
            if c.isalnum() or c == '_':
                r += c
                self.src = self.src[1:]
            else:
                break;
        return r

    def eat_thing(self):
        i = self.eat_ident()
        if i: return i
        return self.eat_str()[1:-1]

    def eat_ws(self):
        while self.src:
            if self.src[0].isspace():
                self.eat()
            else:
                break

escape_str = str.maketrans({
    "\\": r"\\",
    '"': '\\"',
    '\n': '\\n',
})
def esc_str(s):
    return '"' + s.translate(escape_str) + '"'

p = Parser(bulk)
out = ""
while p.src:
    #print(repr(p.src[:10]))
    s = p.eat_c_comment()
    if s:
        out += s
        continue
    s = p.eat_line_comment()
    if s:
        out += s
        continue
    s = p.eat_str()
    if s:
        out += s
        continue
    s = p.eat_ident()
    if s:
        out += s
        continue
    c = p.eat()
    if c == '@':
        node = esc_str(p.eat_thing())
        p.eat_ws()
        rem = p.eat_thing()
        name = "note" + str(abs(hash(rem)))
        rem = esc_str('\n'.join(textwrap.wrap(rem, width=40)))
        # out += node + '[xlabel = ' + rem + '];\n'
        out += "\t" + name + "[shape = note, fillcolor = none, label = " + rem + "];\n"
        out += "\t" + name + ":w -> " + node + ":e [arrowhead = none, color = gray, weight = 10];\n"
        #out += name + ":w -> " + node + ":e"
        #out += "subgraph { " + name + "[shape = note, fillcolor = none, label = " + rem + "]; } -> " + node + ":e"
        # subgraph { note18 [shape = note, label = "HERE"]; } -> @THING;
    else:
        out += c




out = out.replace("\t", "    ")

if "--dump" in sys.argv:
    for (i, line) in enumerate(out.splitlines()):
        print(i + 1, "\t", line)

viewer = "-i" in sys.argv
if viewer:
    os.system("killall dot")
    dot = subprocess.Popen(["dot", "-Txlib"], stdin=subprocess.PIPE)
else:
    dot = subprocess.Popen(["dot", "-Tpng", "-o", "all.png"], stdin=subprocess.PIPE)

dot.stdin.write(bytes(out, "utf-8"))
dot.stdin.close()

if viewer:
    pass
else:
    if dot.wait() == 0:
        #os.system("killall display")
        #os.system("display ./all.png")
        pass
