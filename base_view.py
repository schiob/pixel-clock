import displayio


class BaseView:
    """
    A base class for all views. 
    Each View must handle at least show(), hide(), and update() methods.
    """

    def __init__(self, palette, font, display):
        self.palette = palette
        self.font = font
        self.display = display

        # Each view should have its own Group or TileGrid
        # so that 'show()' can add it to display.root_group
        self.group = displayio.Group()

    def show(self):
        """Show this view by adding its group to the display's root_group."""
        if self.group not in self.display.root_group:
            self.display.root_group.append(self.group)

    def hide(self):
        """Hide this view by removing its group from the display's root_group."""
        if self.group in self.display.root_group:
            self.display.root_group.remove(self.group)

    def update(self):
        """Update logic that runs every loop iteration."""
        pass
