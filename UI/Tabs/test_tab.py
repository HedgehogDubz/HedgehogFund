from UI.tab import Tab
from UI.dock import Dock
from UI.Docks.test_panel import TestPanel
from UI.Docks.test_panel2 import TestPanel2
from PyQt6.QtWidgets import QWidget
from UI.hconnector import HConnector
from UI.vconnector import VConnector

class TestTab(Tab):
    def __init__(self, parent, name, index):
        super().__init__(parent, name, index)

    def initUI(self):
        self.left_dock_end_ratio = 0.25
        self.top_dock_end_ratio = 0.70
        self.right_dock_end_ratio = 0.25

        left_dock = Dock(self, [TestPanel, TestPanel2],
                        0,
                        0,
                        self.left_dock_end_ratio,
                        1)
        self.add_dock(left_dock)

        right_dock = Dock(self, [],
                        1 - self.right_dock_end_ratio,
                        0,
                        self.right_dock_end_ratio,
                        1)
        self.add_dock(right_dock)

        top_dock = Dock (self,[TestPanel, TestPanel2],
                        self.left_dock_end_ratio,
                        0,
                        1 - self.left_dock_end_ratio - self.right_dock_end_ratio,
                        self.top_dock_end_ratio)
        self.add_dock(top_dock)

        bottom_dock = Dock(self, [TestPanel, TestPanel2],
                        self.left_dock_end_ratio,
                        self.top_dock_end_ratio,
                        1 - self.left_dock_end_ratio - self.right_dock_end_ratio,
                        1 - self.top_dock_end_ratio)
        self.add_dock(bottom_dock)
        

        self.add_connector(HConnector(self, self.left_dock_end_ratio, [left_dock], [top_dock, bottom_dock]))
        self.add_connector(HConnector(self, 1-self.right_dock_end_ratio, [top_dock, bottom_dock], [right_dock]))
        self.add_connector(VConnector(self, self.top_dock_end_ratio, [top_dock], [bottom_dock]))

        # Raise all docks above connectors to prevent connectors from blocking tab buttons
        for dock in [left_dock, right_dock, top_dock, bottom_dock]:
            dock.raise_()