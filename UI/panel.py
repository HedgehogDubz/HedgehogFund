from PyQt6.QtWidgets import QFrame
from UI._style_guide import bg


class Panel(QFrame):
    def __init__(self, parent, docked, x, y, w, h):
        super().__init__(parent)
        self.setStyleSheet(f"""
                            background-color: {bg};
                            border: none;
                            margin: 0px; padding: 0px;
                            """)
        self.setGeometry(x, y, w, h)
        self.setContentsMargins(0, 0, 0, 0)

        self.docked = docked

    
        
