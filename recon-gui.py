#!/usr/bin/env python

import optparse
import sys
# prep python path for base module
sys.path.append('./core/')
import base

import Tkinter as tk
import ttk
from xml.dom.minidom import parseString
from idlelib.TreeWidget import TreeItem, TreeNode#import idlelib.TreeWidget
import os

class Application(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.init_ui()
        self.createWidgets()

    def init_ui(self):
        self.master.title('Recon-ng')
        #self.style = ttk.Style()
        #self.style.theme_use("default")
        self.pack(fill=tk.BOTH, expand=1)

    def createWidgets(self):
        mainPane = tk.PanedWindow(self, sashrelief=tk.RAISED, sashwidth=10, orient=tk.VERTICAL)
        mainPane.pack(fill=tk.BOTH, expand=1)

        infoPane = tk.PanedWindow(mainPane, sashrelief=tk.RAISED, sashwidth=10, orient=tk.HORIZONTAL)
        mainPane.add(infoPane)

        modules = ['/recon/hosts/gather/http/api/google',
                   '/recon/hosts/gather/http/api/google',
                   '/recon/hosts/gather/http/api/baidu',
                   '/recon/contacts/gather/http/api/linkedin_auth',
                   '/recon/contacts/gather/http/web/jigsaw',
                   ]

        result = {}
        for item in modules:
            hierarchy = item[1:].split('/')
            local_result = result
            for node in hierarchy:
                local_result = local_result.setdefault(node, {})

        # http://www.pyinmyeye.com/2012/07/tkinter-tree-demo.html
        # http://docs.python.org/dev/library/tkinter.ttk.html#tkinter.ttk.Treeview
        modTree = ttk.Treeview(selectmode='browse', show='tree')
        infoPane.add(modTree)
        #modTree.bind('<<TreeviewOpen>>', self.updateTree)
        self.populateRoot(modTree, result)

        top = tk.Label(infoPane, text="info pane")
        infoPane.add(top)

        outputText = tk.Text(mainPane, bd=0, bg='black', fg='green', highlightthickness=0)#, state=tk.DISABLED)
        mainPane.add(outputText)

    def populateRoot(self, tree, result):
        parent = tree.insert('', tk.END, text='modules')
        self.buildTree(tree, parent, result)

    def buildTree(self, tree, parent, dictionary):
        for key in dictionary : 
            if isinstance(dictionary[key], dict): 
                cid = tree.insert(parent, tk.END, text=key)
                self.buildTree(tree, cid, dictionary[key])
            else: 
                tree.insert(parent, tk.END, text=key, value = dictionary[key])

root = tk.Tk()
#root.geometry("250x150+300+300")
app = Application(root)
app.mainloop()





"""
    def populateTree(self, tree, parent, path):
        for child in os.listdir(path):
            cpath = os.path.join(path, child).replace('\\', '/')
            if os.path.isdir(cpath):
                cid = tree.insert(parent, tk.END, text=child, values=[cpath])
                tree.insert(cid, tk.END, text='dummy')  
            else:
                if not child.endswith('pyc'):
                    tree.insert(parent, tk.END, text='.'.join(child.split('.')[:-1]), values=[cpath])

    def updateTree(self, event):
        tree = event.widget
        nodeId = tree.focus()
        if tree.parent(nodeId):
            topChild = tree.get_children(nodeId)[0]
            if tree.item(topChild, option='text') == 'dummy':
                tree.delete(topChild)
                path = tree.set(nodeId, 'fullpath')
                self.populateTree(tree, nodeId, path)
                """





"""modListbox = tk.Listbox(infoPane)
for module in modules:
    modListbox.insert(tk.END, module)
#modListbox.bind('<<ListboxSelect>>', self.onSelect)
infoPane.add(modListbox)"""

"""
self.columnconfigure(0, weight=1)
self.columnconfigure(1, weight=1)
self.columnconfigure(2, weight=4)
self.rowconfigure(3, weight=1)
self.rowconfigure(4, weight=4)

modLabel = tk.Label(self, text='Modules')
modLabel.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)

optLabel = tk.Label(self, text='Options')
optLabel.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)

infoLabel = tk.Label(self, text='Info')
infoLabel.grid(row=0, column=2, pady=5, padx=5, sticky=tk.W)

modules = ['/recon/hosts/gather/http/api/google',
           '/recon/hosts/gather/http/api/google',
           '/recon/hosts/gather/http/api/baidu',
           '/recon/hosts/gather/http/api/shodan',
           '/recon/hosts/gather/http/api/bing'
           ]
modListbox = tk.Listbox(self)
for module in modules:
    modListbox.insert(tk.END, module)
#modListbox.bind('<<ListboxSelect>>', self.onSelect)
modListbox.grid(column=0, row=1, rowspan=4, padx=5, pady=(0,5), sticky=tk.E+tk.W+tk.S+tk.N)

optListbox = tk.Listbox(self)
optListbox.grid(column=1, row=1, rowspan=3, padx=(0,5), sticky=tk.E+tk.W+tk.S+tk.N)

infoText = tk.Text(self, bd=0, highlightthickness=0)#, state=tk.DISABLED)
infoText.grid(column=2, row=1, rowspan=3, sticky=tk.E+tk.W+tk.S+tk.N)

runButton = tk.Button(self, text='Run')
runButton.grid(column=3, row=1)

helpButtonbtn = tk.Button(self, text='Help')
helpButtonbtn.grid(column=3, row=2, pady=4)

outputText = tk.Text(self, bd=0, bg='black', fg='green', highlightthickness=0)#, state=tk.DISABLED)
outputText.grid(column=1, columnspan=3, row=4, padx=(0,5), pady=5, sticky=tk.E+tk.W+tk.S+tk.N)
"""




"""
def recon_ui(opts):
    # set up command completion
    try:
        import readline
    except ImportError:
        print '%s[!] Module \'readline\' not available. Tab complete disabled.%s' % (R, N)
    else:
        import rlcompleter
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(readline.get_completer_delims().replace('/', ''))
        # for possible future use to format command completion output
        #readline.set_completion_display_matches_hook(display_hook)
    x = base.Recon()
    # check for and load workspace
    if opts.workspace: x.do_set('workspace %s' % (opts.workspace))
    # check for and run script session
    if opts.script_file: x.do_resource(opts.script_file)
    try: x.cmdloop()
    except KeyboardInterrupt: print ''

usage = './%prog [options]'
description = '%%prog - %s %s' % (base.__author__, base.__email__)
parser = optparse.OptionParser(usage=usage, description=description, version=base.__version__)
parser.add_option('-w', help='load/create a workspace', metavar='workspace', dest='workspace', type='string', action='store')
parser.add_option('-r', help='load commands from a resource file', metavar='filename', dest='script_file', type='string', action='store')
(opts, args) = parser.parse_args()
recon_ui(opts)
"""
