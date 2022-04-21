"""Minecraft Python Edition command control
By bailongyue
requires python 3.8+"""

# WARNING: Alpha test version! Use only if from github / gitee / baiduNetDisk

import tkinter as tk
from tkinter.scrolledtext import *
from tkinter import messagebox as msg
from utils import MinecraftError

cmdver = 'v0.1'
KWS = "help", "println", "label", "title", "echo", "exit", "math"
MATHS = "+", "-", "*", "/", "%", "sqrt", "^"

class AlternativeHost(object):
    def __init__(self, *args, **kw):
        pass

    def set_caption(self, text="Minecraft Python Edition"):
        pass

    def set_displaying_label_text(self, text="Hello world!"):
        pass

class CommandInterface(tk.Tk):
    def __init__(self, interpreter = None):
        tk.Tk.__init__(self)
        self.resizable(False, False)
        self.interpreter = interpreter
        self.title("Minecraft Commander %s" % cmdver)
        self.text_frame = fr1 = tk.Frame()
        self.scrolled_text = ScrolledText(fr1)
        self.scrolled_text.pack(expand=True, fill="both")
        fr1.pack(expand=True, fill="both")
        self.entry_frame = fr2 = tk.Frame(self)
        self.entry = tk.Entry(fr2)
        self.entry.pack(expand=True, fill="both", side="left")
        self.button2 = tk.Button(fr2, text="Clear", width=6, command=self.clear, background="#FFDDDD", activebackground="#CC6676")
        self.button2.pack(side="right")
        self.button1 = tk.Button(fr2, text="Run", width=5, command=self.execmd, background="#DDDDFF", activebackground="#9999FF")
        self.button1.pack(side="right")
        fr2.pack(expand=True, fill="both")
        self.known_tags = []
        self.scrolled_text.bind('<Return>', self.colorize)
        self.entry.bind('<Return>', self.execmd)
        self.bind('<Escape>', self.clear)

    def colorize(self, event=None):
        for tag in self.known_tags:
            self.scrolled_text.tag_delete(tag)
        txt = self.scrolled_text.get(1.0, "end")
        txt = txt.split("\n")
        for i in range(len(txt)):
            ln = txt[i]
            ws = ln.split(" ")
            wds = ""
            for j in range(len(ws)):
                wd = ws[j]
                if wd in KWS:
                    index_char = len(wds)
                    index_line = i + 1
                    len_char = len(wd)
                    tag_start = "%i.%i" % (index_line, index_char)
                    tag_end = "%i.%i" % (index_line, index_char+len_char)
                    tag_name = "%i %i %i %s" %(index_line, index_char, \
                                               len_char, wd)
                    self.known_tags.append(tag_name)
                    self.scrolled_text.tag_add(tag_name, tag_start, tag_end)
                    self.scrolled_text.tag_config(tag_name, foreground="red")
                wds += (wd + " ")

    def take_interpreter(self, interpreter):
        self.interpreter = interpreter

    def execmd(self, event=None):
        command = self.entry.get()
        self.entry.delete(0, "end")
        self._execmd(command)

    def clear(self, event=None):
        self.scrolled_text.delete(1.0, "end")
        self.entry.delete(0, "end")

    def _execmd(self, command=""):
        if command.strip() == "":
            return
        words = command.split(" ")
        if words[0] == "echo":
            self.println(command[5:])
        elif words[0] == "exit":
            self.destroy()
        else:
            msg.showerror("ERROR", "ERROR: Unknown command.\nCommand %s does not exist." % command)

    def println(self, text=""):
        self.scrolled_text.insert("end", text+"\n")

if __name__ == "__main__":
    shell = CommandInterface()
    shell.mainloop()
