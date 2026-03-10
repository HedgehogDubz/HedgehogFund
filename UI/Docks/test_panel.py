from UI.panel import Panel

class TestPanel (Panel):
    def __init__(self, parent, docked, x, y, w, h):
        super().__init__(parent, docked, x, y, w, h)
        self.parent = parent
        self.docks = []
        self.initUI()

    def initUI(self):
        pass

    
        