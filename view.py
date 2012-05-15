
#import Tkinter as tk
import Tkinter as tk
import ttk
from ScrolledText import ScrolledText
import tkMessageBox
import tkFileDialog
import tkSimpleDialog


class WidgetRedirector:

    """Support for redirecting arbitrary widget subcommands."""

    def __init__(self, widget):
        self.dict = {}
        self.widget = widget
        self.tk = tk = widget.tk
        w = widget._w
        self.orig = w + "_orig"
        tk.call("rename", w, self.orig)
        tk.createcommand(w, self.dispatch)

    def __repr__(self):
        return "WidgetRedirector(%s<%s>)" % (self.widget.__class__.__name__,
                                             self.widget._w)

    def close(self):
        for name in self.dict.keys():
            self.unregister(name)
        widget = self.widget; del self.widget
        orig = self.orig; del self.orig
        tk = widget.tk
        w = widget._w
        tk.deletecommand(w)
        tk.call("rename", orig, w)

    def register(self, name, function):
        if self.dict.has_key(name):
            previous = dict[name]
        else:
            previous = OriginalCommand(self, name)
        self.dict[name] = function
        setattr(self.widget, name, function)
        return previous

    def unregister(self, name):
        if self.dict.has_key(name):
            function = self.dict[name]
            del self.dict[name]
            if hasattr(self.widget, name):
                delattr(self.widget, name)
            return function
        else:
            return None

    def dispatch(self, cmd, *args):
        m = self.dict.get(cmd)
        try:
            if m:
                return m(*args)
            else:
                return self.ttk.call((self.orig, cmd) + args)
        except tk.TclError:
            return ""


class OriginalCommand:

    def __init__(self, redir, name):
        self.redir = redir
        self.name = name
        self.tk = redir.tk
        self.orig = redir.orig
        self.tk_call = self.tk.call
        self.orig_and_name = (self.orig, self.name)

    def __repr__(self):
        return "OriginalCommand(%r, %r)" % (self.redir, self.name)

    def __call__(self, *args):
        return self.tk_call(self.orig_and_name + args)


#########################################################################
class RedirectedText(tk.Text):
    """We would like to know when the Text widget's contents change.  We can't
    just override the insert method, we have to make use of some Tk magic.
    This magic is encapsulated in the idlelib.WidgetRedirector class which
    we use here.
    """

    def __init__(self, master=None, cnf={}, **kw):
        tk.Text.__init__(self, master, cnf, **kw)

        # now attach the redirector
        self.redir = WidgetRedirector(self)
        self.orig_insert = self.redir.register("insert", self.new_insert)
        self.orig_delete = self.redir.register("delete", self.new_delete)

    def new_insert(self, *args):
        self.orig_insert(*args)
        self.event_generate('<<Change>>')

    def new_delete(self, *args):
        self.orig_delete(*args)
        self.event_generate('<<Change>>')

#########################################################################
class StatusBar(ttk.Frame):
    """From the tkinterbook.
    """

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.label = ttk.Label(self, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set_label(self, fmt, *args):
        self.label.config(text=fmt % args)
        self.label.update_idletasks()

    def clear_label(self):
        self.label.config(text="")
        self.label.update_idletasks()

class View:
    """Main user interface class.
    """
    
    def __init__(self, controller):
        self.controller = controller

        self.root = None

        self._create_ui()
        self._bind_events()

        #self._current_text = None
        #self.user_text.focus_set()
        
    def cmd_lb_notes_select(self, evt):
        print self.lb_notes.curselection()
        
    def _bind_events(self):
        self.root.bind_all("<Control-f>", lambda e: self.search_entry.focus())
        
        self.lb_notes.bind("<<ListboxSelect>>", self.cmd_lb_notes_select)        

    def _create_menu(self):
        """Utility function to setup main menu.

        Called by _create_ui.
        """
        
        # MAIN MENU ####################################################
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=False)
        menu.add_cascade(label="File", underline='0', menu=file_menu)
        

        # FILE ##########################################################
        file_menu.add_command(label = "Exit", underline=1,
                              command=self.cmd_exit, accelerator="Ctrl+Q")
        self.root.bind_all("<Control-q>", self.cmd_exit)

        # EDIT ##########################################################
        edit_menu = tk.Menu(menu, tearoff=False)
        menu.add_cascade(label="Edit", underline=0, menu=edit_menu)
        
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X",
                              underline=2, command=self.cmd_cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C",
                              underline=0, command=self.cmd_copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V",
                              underline=0, command=self.cmd_paste)


        # HELP ##########################################################
        help_menu = tk.Menu(menu, tearoff=False)
        menu.add_cascade(label="Help", underline='0', menu=help_menu)

        help_menu.add_command(label = "About", underline = 0,
                              command = self.cmd_help_about)

        # END MENU ######################################################

    def _create_ui(self):

        # these two variables determine the final dimensions of our interface
        #FRAME_HEIGHT=400
        TEXT_WIDTH=80
        
        self.root = tk.Tk()
        self.root.title("nvPY")

        # try finding icon in resdir and in appdir
#        try:
#            self.iconpath = os.path.join(
#                self.controller.get_resdir(), 'envedit.ico')
#            self.root.iconbitmap(self.iconpath)
            
#        except TclError:
#            try:
#                self.iconpath = os.path.join(
#                    self.controller.get_appdir(), 'envedit.ico')
#                self.root.iconbitmap(self.iconpath)
                
#            except TclError:
#                self.show_error('Error', 'Error opening icon.  Continuing.')

        # create menu ###################################################
        self._create_menu()

        # separator after menu ##########################################
        #separator = ttk.Frame(self.root, height=2, bd=1, relief=ttk.SUNKEN)
        #separator.pack(fill=ttk.X, padx=5, pady=2, side=ttk.TOP)

        # setup statusbar ###############################################
        # first pack this before panedwindow, else behaviour is unexpected
        # during sash moving and resizing
        self.statusbar = StatusBar(self.root)
        self.statusbar.set_label('%s', 'Welcome to nvPY!')
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        search_frame = ttk.Frame(self.root)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(fill=tk.X)
        search_frame.pack(side=tk.TOP, fill=tk.X)
        
        # the paned window ##############################################
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=1)
        
        left_frame = ttk.Frame(paned_window, width=100)
        paned_window.add(left_frame)
        
        self.lb_notes = tk.Listbox(left_frame)
        
        # need both fill and expand to make it fill all avail area
        self.lb_notes.pack(fill=tk.BOTH, expand=1)

        right_frame = ttk.Frame(paned_window, width=400)
        paned_window.add(right_frame)

        # we'll use this method to create the different edit boxes
        def create_scrolled_text(master):
            yscrollbar = ttk.Scrollbar(master)
            yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # this determines the width of the complete interface (yes)
            text = RedirectedText(master, height=15, width=TEXT_WIDTH,
                                  wrap=tk.CHAR,
                                  yscrollcommand=yscrollbar.set)

            text.pack(fill=tk.BOTH, expand=1)

            #xscrollbar.config(command=text.xview)
            yscrollbar.config(command=text.yview)

            return text


        # setup user_text ###############################################
        self.text_note = create_scrolled_text(right_frame)

#        def cb_ut_fi(event):
#            self.set_current_text(CURTEXT_USER)
#
#        self.user_text.bind('<FocusIn>', cb_ut_fi)
#
#        def cb_ut_m(event):
#            self.set_user_mode(MODE_MODIFIED)
#
#        self.user_text.bind('<<Change>>', cb_ut_m)
#
#        # setup sys_text ################################################
#        self.sys_text, self._sys_mode_label_var = \
#                      create_scrolled_text(bottom_frame, "System Environment")
#
#        def cb_st_fi(event):
#            self.set_current_text(CURTEXT_SYS)
#
#        self.sys_text.bind('<FocusIn>', cb_st_fi)
#
#        def cb_st_c(event):
#            self.set_sys_mode(MODE_MODIFIED)
#            
#        self.sys_text.bind('<<Change>>', cb_st_c)

        # finish UI creation ###########################################

        # now set the minsize so that things can not disappear
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        
        # call update so we know that sizes are up to date
        self.root.update_idletasks()
        
        
    def close(self):
        self.root.destroy()


    def cmd_cut(self):
        t = self.get_text_with_focus()
        if t:
            t.event_generate('<<Cut>>')

    def cmd_copy(self):
        t = self.get_text_with_focus()
        if t:
            t.event_generate('<<Copy>>')
        
    def cmd_paste(self):
        t = self.get_text_with_focus()
        if t:
            t.event_generate('<<Paste>>')


    def cmd_help_about(self):
        tkMessageBox.showinfo(
            'Help | About',
            'nvPY %s is copyright 2012 by Charl P. Botha '
            '<http://charlbotha.com/>\n\n'
            'Because SimpleNote deserves better.' % (self.controller.get_version(),),
            parent = self.root)

    def cmd_exit(self, event=None):
        self.controller.quit()

    def main_loop(self):
        self.root.mainloop()
        
    def set_note_content(self, note_content):
        self.text_note.delete(1.0, tk.END) # clear all
        self.text_note.insert(tk.END, note_content)
        
        
    def set_note_names(self, note_names):
        # clear the listbox
        self.lb_notes.delete(0)
        
        for nn in note_names:
            self.lb_notes.insert(tk.END, nn.title)

    def show_error(self, title, msg):
        tkMessageBox.showerror(title, msg)
        