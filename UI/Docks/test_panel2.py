from UI.panel import Panel
from PyQt6.QtWidgets import QLabel

class TestPanel2 (Panel):
    def __init__(self, parent, docked, x, y, w, h):
        super().__init__(parent, docked, x, y, w, h)
        self.parent = parent
        self.docks = []
        self.initUI()

    def initUI(self):
        lbl = QLabel("TestDock", self)
        
    
        