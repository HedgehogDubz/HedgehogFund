from PyQt6.QtWidgets import QWidget
from UI.dock import Dock

class Tab(QWidget):
    def __init__(self, parent, name, index):
        super().__init__(parent)
        self.parent = parent

        self.name = name
        self.index = index
        self.docks = []
        self.connectors = []
        self.min_dock_size = getattr(parent, 'min_dock_size', 100)

        self.initUI()

    def initUI(self):
        pass

    def add_dock(self, dock):
        self.docks.append(dock)
        self.parent.add_dock(dock)
        return dock

    def remove_dock(self, dock):
        if dock in self.docks:
            self.docks.remove(dock)
            self.parent.remove_dock(dock)

    def centralWidget(self):
        return self.tab_content_widget if hasattr(self, 'tab_content_widget') else self

    def width(self):
        return self.tab_content_widget.width() if hasattr(self, 'tab_content_widget') else super().width()

    def height(self):
        return self.tab_content_widget.height() if hasattr(self, 'tab_content_widget') else super().height()
    
    def add_connector(self, connector):
        self.connectors.append(connector)
        self.parent.add_connector(connector)

    def remove_connector(self, connector):
        if connector in self.connectors:
            self.connectors.remove(connector)
            self.parent.remove_connector(connector)

            if self.connector_manager:
                self.connector_manager.remove_connector(connector)