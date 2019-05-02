        css_P.load_from_path("res/style.css")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_P,
            400
        )
