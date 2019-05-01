        def __init__(self):
            Gtk.Window.__init__(self, title="OptiGreeter")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.add(vbox)
            #self.u_entry = Gtk.Entry()


            #self.p_entry = Gtk.Entry()
            self.button = Gtk.Button(label="Click Here")
            vbox.pack_start(self.button, True, True, 0)

            #self.add(self.u_entry)
            #self.add(self.p_entry)
