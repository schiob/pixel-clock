class ViewManager:
    """Manages multiple views and displays one at a time."""

    def __init__(self, display):
        self.display = display
        self.views = []
        self.current_view_index = None
        self.current_view = None

    def add_view(self, view):
        """Register a new view with the manager."""
        self.views.append(view)

    def set_view(self, index):
        """Hide the old view and show the new one by index."""
        # Hide old view
        if self.current_view:
            self.current_view.hide()

        # Set and show new view
        self.current_view_index = index
        self.current_view = self.views[index]
        self.current_view.show()

    def next_view(self):
        """Convenient method to rotate to the next view."""
        if not self.views:
            return
        new_index = (self.current_view_index + 1) % len(self.views)
        self.set_view(new_index)

    def update(self):
        """Call the current view's update() method each loop."""
        if self.current_view:
            self.current_view.update()
