from UI.panel import Panel
from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

class TestPanel (Panel):
    def __init__(self, parent, docked, x, y, w, h):
        super().__init__(parent, docked, x, y, w, h)
        self.parent = parent
        self.docks = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        lbl = QLabel("TestPanel", self)
        layout.addWidget(lbl, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)

    
        