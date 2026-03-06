from UI.dockable_window import DockableWindow
from PyQt6.QtWidgets import QLabel

class TestDock2 (DockableWindow):
    def __init__(self, parent, docked, x, y, w, h):
        super().__init__(parent, docked, x, y, w, h)
        self.parent = parent
        self.docks = []
        self.initUI()

    def initUI(self):
        lbl = QLabel("TestDock", self)
        
    
        