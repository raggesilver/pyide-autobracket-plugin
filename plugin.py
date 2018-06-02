
import git, os

from gi.repository import GObject, GLib, Gtk, Gdk

class Plugin(GObject.GObject):

    def __init__(self, *args, **kwargs):

        GObject.GObject.__init__(self)

        self.chars = {
            'parenleft': ')',
            'bracketleft': ']',
            'braceleft': '}',
            'quotedbl': '"',
            'apostrophe': '\'' # ,
            # 'less': '>' # FIXME disabled until there is a way to check if the language needs this auto bracket
        }

        self.history = {} # For storing hadSelection

        if 'applicationWindow' in kwargs:
            self.applicationWindow = kwargs['applicationWindow']

    def do_activate(self):

        self.applicationWindow.editor.connect("editor-created-after", self.do_attach_to_editor)

    def do_attach_to_editor(self, *args):
        
        currentEditor = self.applicationWindow.editor.activeEditor

        self.history[currentEditor.sview] = { "hadSelection": False }

        if currentEditor is not None:
            currentEditor.sview.connect("event-after", self.do_completion)

    def do_completion(self, sview, event):

        sbuff = sview.get_buffer()
        hasSelection = sbuff.props.has_selection

        # Selection iters
        startIter = endIter = None
        # Selection text

        # Capture selection (in case there is one)
        if hasSelection:
            startIter, endIter = sbuff.get_selection_bounds()
            self.history[sview]["selectionText"] = sbuff.get_text(startIter, endIter, False)
        
        # Masks to ignore
        ignore = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK

        if (event.type != Gdk.EventType.KEY_PRESS or event.state & ignore or Gdk.keyval_name(event.key.keyval) not in self.chars):

            # TODO Create a way to store hasSelection and hadSelection per buffer
            self.history[sview]["hadSelection"] = hasSelection

            return

        insert = self.get_insert(sbuff)
        closing = self.chars[Gdk.keyval_name(event.key.keyval)]

        # TODO check if the language needs auto bracket for < and >

        if not hasSelection and not self.history[sview]["hadSelection"]:
            # Allows one Ctrl+Z to undo everything until we close user action
            sbuff.begin_user_action()
            sbuff.insert(insert, closing)
        else:
            sbuff.begin_user_action()
            text = self.history[sview]["selectionText"] + closing
            sbuff.insert(insert, text)

        insert.backward_chars(1)
        sbuff.place_cursor(insert)
        sbuff.end_user_action()
        
    def get_insert(self, sbuff):

        mark = sbuff.get_insert()
        return sbuff.get_iter_at_mark(mark)