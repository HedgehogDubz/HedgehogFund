from PyQt6.QtWidgets import QWidget
from UI.dock import Dock
class Tab(QWidget):
    def __init__(self, parent, name, index):
        super().__init__(parent)
        self.parent = parent

        self.name = name
        self.index = index
        self.docks = []

        self.initUI()

    def initUI(self):
        pass

    def add_docks(self,dockable_windows, x_ratio, y_ratio, w_ratio, h_ratio):
        dock = Dock(self, dockable_windows, x_ratio, y_ratio, w_ratio, h_ratio)
        self.docks.append(dock)
        self.parent.add_dock(dock)

    def centralWidget(self):
        return self.tab_content_widget if hasattr(self, 'tab_content_widget') else self

    def width(self):
        return self.tab_content_widget.width() if hasattr(self, 'tab_content_widget') else super().width()

    def height(self):
        return self.tab_content_widget.height() if hasattr(self, 'tab_content_widget') else super().height()