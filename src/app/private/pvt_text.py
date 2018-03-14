from ..tkimport import Tk
from ...utils import CONTROL_KEY

class TextInput(Tk.Text):
    """docstring for TextInput"""
    def __init__(self, parent, *args, **kwargs):
        Tk.Text.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.lang   = self.parent.parent.lang
        self.lang_format = self.lang.Workspace.Format

        # Set some custom colours

        self.lang_format.colour_map["strings"] = "Green"
        self.lang_format.colour_map["arrow"]   = "#e89c18"

        for tier in self.lang_format.tag_weights:

            for tag_name in tier:

                self.tag_config(tag_name, foreground=self.lang_format.colour_map[tag_name])

        self.tag_config("highlight", background="red", foreground="white")

        self.bind("<Key>",       self.keypress)

        # Over-ride Key binding for undo/redo shortcuts : TODO - add to Menu

        self.bind("<{}-z>".format(CONTROL_KEY), lambda e: None)
        self.bind("<{}-y>".format(CONTROL_KEY), lambda e: None)

        self.config(undo=True, autoseparators=True, maxundo=50)

        self.key_down = False

    @staticmethod
    def convert_index(index1, index2=None):
        if type(index1) == str and index2 == None:
            return tuple(int(n) for n in index1.split('.'))
        return str(index1) + '.' + str(index2)
        
    def get_text(self):
        """ Returns the contents of the text box """
        return self.get(1.0, Tk.END)

    def set_text(self, text):
        """ Sets the contents of the text box """
        self.clear()
        self.insert("1.0", text)
        self.edit_reset()
        self.update_colours()
        return

    def clear(self):
        """ Deletes the contents of the text box """
        self.delete(1.0, Tk.END)
        self.edit_reset()
        return

    def keypress(self, event):
        """ Inserts a character and then updates the syntax formatting """
        if event.keysym == "BackSpace":
            self.edit_separator()
            return
        elif event.char != "":
            if event.char == "\r":
                char = "\n"
            elif event.char == "\t":
                char = " "*4
            else:
                char = event.char
            index = self.index(Tk.INSERT)
            self.insert(index, char)
            self.update_colours()
            self.edit_separator()
            return "break"
        return

    def highlight(self):
        """ Highlights a chunk of text and schedules it to un-highlight 150ms later """

        # Get start and end of the buffer
        start, end = "1.0", self.index(Tk.END)
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_x, cur_y = [int(x) for x in self.index(Tk.INSERT).split(".")]
        
        # 2. Go through line by line (back) and see what it's value is
        
        for line in range(cur_x, 0, -1):
            if not self.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[0] = line

        # 3. Iterate forwards until we get two \n\n or index==END
        for line in range(cur_x, lastline):
            if not self.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[1] = line

        # Now we have the lines of code!

        a, b = block
    
        if a == b: b += 1

        for line in range(a, b):

            start = "%d.0" % line
            end   = "%d.end" % line

            # Highlight text only to last character, not whole line

            if len(self.get(start, end).strip()) > 0:

                self.tag_add("highlight", start, end)

        self.after(150, self.unhighlight)

        return 

    def unhighlight(self):
        """ Removes the highlight from text """
        return self.tag_remove("highlight", "1.0", Tk.END)

    def update_colours(self, event=None):
        this_line = self.index(Tk.INSERT)
        line, col = this_line.split(".")
        self.colour_line(line)
        return

    def colour_line(self, line):
        """ Checks a line for any tags that match regex and updates IDE colours """

        line = int(line)

        start_of_line, end_of_line = self.convert_index(line,0), self.convert_index(line,"end")

        thisline = self.get(start_of_line, end_of_line)

        try:

            # Remove tags at current point

            for tag_name in self.tag_names():

                self.tag_remove(tag_name, start_of_line, end_of_line)

            # Re-apply tags

            for tag_name, start, end in self.lang_format.findstyles(thisline):
                
                self.tag_add(tag_name, self.convert_index(line, start), self.convert_index(line, end))

        except Exception as e:

            print(e)

        return