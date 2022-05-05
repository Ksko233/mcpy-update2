"""设置Minecraft Python Edition的启动器
目前有Launchpad(不推荐)和AlphaLaunchpad(推荐)"""

import tkinter as tk
from tkinter import simpledialog as dialog
from tkinter import messagebox as msgbox
from tkinter import ttk
from platform import mac_ver
from textview import view_file
from sys import exit
from easygui import exceptionbox
from utils import log

from language import *


def nothing():
    pass

def get_wrong_value(number=0):
    return 114514

if mac_ver()[0]:
    style = {"width":9}
else:
    style = {"width":11}



class ClassicLaunchpad(object):
    """MCPY Dev的启动器窗口, 不推荐使用"""
    def __init__(self, runcmd, mainloop=False):
        """初始化MCPY Dev的启动器界面, 建议使用AlphaLaunchpad"""
        self.root = tk.Tk()
        self.root.title("MCPYLauncher")
        lb = ttk.Label(self.root, text="Minecraft Python Edition Launchpad")
        lb.pack()
        self.cmd = runcmd
        btn = ttk.Button(self.root, text="Play", command=self.fcmd)
        btn.pack(**style)
        if mainloop:
            self.root.mainloop()

    def fcmd(self, *args, **kw):
        self.root.destroy()
        self.cmd(*args, **kw)

class AlphaLaunchpad(tk.Tk):
    """MCPY Alpha的启动器窗口, 功能未完善
       参数介绍:
       *args **kw 用于tkinter.Tk的参数和关键字参数"""
    def __init__(self, *args, **kw):
        """初始化MCPY Alpha的启动器界面
           参数介绍:
           *args **kw 为旧版的Mod兼容性制作, 没有实际用处"""
        tk.Tk.__init__(self)
        self.configure(bg="#EEEEEE")
        log("Starting launchpad")
        self.title(textLaunchpadTitle)
        self.resizable(False, False)
        self.notebook = ttk.Notebook(self)
        self.setup_listbox()
        self.setup_world_buttons()
        self.notebook.add(self.fr_worlds, text=textNoteRun)
        self.notebook.grid(row=0, column=0)
        self.setup_mod_buttons()
        self.setup_checks()
        if not mac_ver()[0]:
            self.iconbitmap("./resources/favicon.ico")
        log("Launchpad is ready")

    def setup_world_buttons(self):
        """初始化加载世界的IGUI"""
        self.fr_worlds = tk.Frame(self.notebook, bg="#EEEEEE")
        self.fr_worlds.grid(column=0, row=1, padx=1, pady=2)
        self.bu_start = ttk.Button(self.fr_worlds, text=textStart, \
                                   command=self.__loadgame, **style)
        self.bu_start.grid(column=0, row=0, padx=1) #快速开始, 不推荐
        self.bu_worlds = ttk.Button(self.fr_worlds, text=textWorlds,\
                                    command=self.show_worlds, **style)
        self.bu_worlds.grid(column=1, row=0, padx=1) #选择与查看世界
        self.bu_multi = ttk.Button(self.fr_worlds, text=textMultiplayer, \
                                  command=self.infoNoServer, **style)
        self.bu_multi.grid(column=2, row=0, padx=1) #多人游戏, 正在开发中

    def setup_listbox(self):
        """设置选项框"""
        self.glistbox = tk.Listbox(self, height=10, width=37)
        self.glistbox.grid(column=0, row=2, pady=(0, 7))

    def setup_mod_buttons(self):
        """初始化加载Mod的IGUI"""
        self.fr_modify = tk.Frame(self.notebook, bg="#EEEEEE")
        self.notebook.add(self.fr_modify, text=textNoteModify)
        self.bu_config = ttk.Button(self.fr_modify, text=textResetWorld,\
                                    state="disabled",\
                                    command=lambda:self.run_world(1), **style)
        self.bu_config.grid(column=0, row=0, padx=1) #世界设置
        self.bu_help = ttk.Button(self.fr_modify, text=textHelp, \
                                  command=self.view_help, **style)
        self.bu_help.grid(column=1, row=0, padx=1) #获得帮助
        self.bu_addons = ttk.Button(self.fr_modify, text=textAddons,\
                                    **style) # No command
        self.bu_addons.grid(column=2, row=0, padx=1) #Mod选项
        self.fr_extool = tk.Frame(self.notebook, bg="#EEEEEE")
        self.notebook.add(self.fr_extool, text=textNoteOptions)
        self.bu_settings = ttk.Button(self.fr_extool, text=textSettings,\
                                      state="enabled", command=self.ConfigUser,\
                                      **style)
        self.bu_settings.grid(column=0, row=1, padx=1) #设置功能正在开发中
        self.bu_market = ttk.Button(self.fr_extool, text=textMarket,\
                                    command=self.infoNoServer, **style)
        self.bu_market.grid(column=1, row=1, padx=1) #创意市场, 等到开服再做
        self.bu_exit = ttk.Button(self.fr_extool, text=textExit, \
                                  command=self.destroy, **style)
        self.bu_exit.grid(column=2, row=1, padx=1) #退出MCPY启动器

    def setup_checks(self):
        self.checks = cks = tk.Frame(self, bg="#EEEEEE")
        self.ckvs = []
        v1 = tk.BooleanVar(value=True)
        self.ckvs.append(v1)
        v2 = tk.BooleanVar()
        self.ckvs.append(v2)
        v3 = tk.BooleanVar()
        self.ckvs.append(v3)
        v4 = tk.BooleanVar()
        self.ckvs.append(v4)
        v5 = tk.BooleanVar()
        self.ckvs.append(v5)
        v6 = tk.BooleanVar(value=True)
        self.ckvs.append(v6)
        self.ck1 = ttk.Checkbutton(cks, text=terrainForest, variable=v1)
        self.ck1.grid(row=0, column=0, sticky='w')
        self.ck2 = ttk.Checkbutton(cks, text=terrainSnow, variable=v2)
        self.ck2.grid(row=0, column=1, sticky='w')
        self.ck3 = ttk.Checkbutton(cks, text=terrainIceRiver, variable=v3)
        self.ck3.grid(row=0, column=2, sticky='w')
        self.ck4 = ttk.Checkbutton(cks, text=terrainDesert, variable=v4)
        self.ck4.grid(row=1, column=0, sticky='w')
        self.ck5 = ttk.Checkbutton(cks, text=terrainArid, variable=v5)
        self.ck5.grid(row=1, column=1, sticky='w')
        self.ck6 = ttk.Checkbutton(cks, text=textInfDev, variable=v6)
        self.ck6.grid(row=1, column=2, sticky='w', padx=(3, 0))
        self.checks.grid(row=4, column=0)

    def destroy(self):
        """退出MCPY启动器"""
        if msgbox.askyesno(textLaunchpadTitle, \
                           textExitInfo):
            log("Launchpad is closed")
            tk.Tk.destroy(self) #在询问是否退出之后退出(坑人同原理)
            exit()

    def view_help(self):
        view_file(self, textLaunchpadTitle, "./README.md", "utf-8")

    def __rungame(self):
        log("Starting engine...")
        import engine
        engine.INFWORLD = self.ckvs[5].get()
        engine.TERRAIN = [self.ckvs[0].get(), self.ckvs[1].get(), self.ckvs[2].get(), self.ckvs[3].get(), self.ckvs[4].get()]
        tk.Tk.destroy(self)
        engine.SAVED = False
        engine.main()
        exit()

    def __loadgame(self):
        log("Loading game...")
        import engine
        tk.Tk.destroy(self)
        engine.SAVED = True
        engine.main()
        exit()

    def show_worlds(self):
        self.glistbox.delete(0,"end")
        for name in WORLDS_NAMES:
            self.glistbox.insert("end", name)
        self.bu_config["state"] = "normal"
        self.bu_addons["state"] = "normal"
        self.bu_start.configure(text=textPlayWorld, command=self.run_world)

    def show_addons(self):
        self.glistbox.delete(0,"end")
        self.bu_start.configure(text="Play mod", command=None)
        self.bu_addons["state"] = "disabled"

    def run_world(self, cfg=False, saved=True):
        try:
            index = self.glistbox.curselection()[0]
        except IndexError:
            msgbox.showerror(textLaunchpadTitle, textNoSelect)
            return
        import engine
        engine.TMP_WORLD_PATH = engine.WORLDS_PATHS[index]
        engine.SAVED = saved
        engine.INFWORLD = self.ckvs[5].get()
        engine.TERRAIN = [self.ckvs[0].get(), self.ckvs[1].get(), self.ckvs[2].get(), self.ckvs[3].get(), self.ckvs[4].get()]
        if not cfg:
            tk.Tk.destroy(self)
            log(engine.TMP_WORLD_PATH)
            engine.main()
        else:
            if msgbox.askokcancel(textLaunchpadTitle, textResetInfo):
                self.run_world(saved=False)
        exit()

    def ConfigUser(self):
        _Settings(self).mainloop()

    def infoNoServer(self):
        msgbox.showerror(textLaunchpadTitle, textNoServer)

class _Settings(tk.Toplevel):
    def __init__(self, parent=None, *args, **kw):
        tk.Toplevel.__init__(self, parent, *args, **kw)
        self.title("MCPY Settings")
        self.lang = tk.StringVar()
        self.lang.set("English")
        self.setup_lang_choices()
        self.transient(parent)
        self.grab_set()
        self.bind("<Escape>", self.destroy)

    def setup_lang_choices(self):
        self.fr1 = tk.Frame(self)
        self.fr1.pack()
        lb_lang = ttk.Label(self.fr1, text="Select your language:")
        lb_lang.grid(column=0, row=0, padx=6, pady=6)
        lb_help = ttk.Label(self.fr1, text="Default: English")
        lb_help.grid(column=0, row=1)
        self.r_frame = tk.Frame(self.fr1)
        self.r_frame.grid(column=1, row=0, padx=6, pady=6)
        self.r1 = ttk.Radiobutton(self.r_frame, text='简体中文', value='zh-cn', \
                              variable=self.lang, command=self.set_apply)
        self.r2 = ttk.Radiobutton(self.r_frame, text='English', value='en-us', \
                              variable=self.lang, command=self.set_apply)
        self.r1.grid(column=1, row=0)
        self.r2.grid(column=2, row=0)
        self.bu_apply = ttk.Button(self, text="Apply", state="disabled",\
                                   command=self.apply, width=8)
        self.bu_apply.pack()

    def destroy(self, event=None):
        self.grab_release()
        tk.Toplevel.destroy(self)

    def set_apply(self):
        self.bu_apply.configure(state="enabled")

    def apply(self, event=None):
        la = self.lang.get()
        if la == 'zh-cn':
            with open("config/lang", "w") as f:
                f.seek(0)
                f.truncate()
                f.write("zh")
        elif la=='en-us':
            with open("config/lang", "w") as f:
                f.seek(0)
                f.truncate()
                f.write("en")
        self.bu_apply.configure(state="disabled")
        if msgbox.askokcancel(textLaunchpadTitle, "Restart to apply settings"):
            self.destroy()
            tk.Tk.destroy(self.master)

    def reset(self):
        self.lang.set("en-us")

    def infoNoServer(self):
        msgbox.showerror(textLaunchpadTitle, textNoServer)

class _QueryConfigWorld(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.setup_buttons()

    def setup_buttons(self):
        self.ok = ttk.Button(self, text="Ok", command=self.destroy)
        self.ok.pack(padx=3, pady=3, ipadx=2, ipady=2)

def process_run_command(command, *args, **kw):
    """处理一个函数, 返回包装参数的函数"""
    def ecmd():
        command(*args, **kw)
    return ecmd

def main():
    try:
        AlphaLaunchpad().mainloop()
    except Exception as msg:
        if not msg.__class__ == SystemExit:
            exceptionbox()

if __name__ == "__main__":
    main()
