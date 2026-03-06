from UI.tab import Tab
from UI.dock import Dock
from UI.Docks.test_dock import TestDock
from UI.Docks.test_dock2 import TestDock2
from PyQt6.QtWidgets import QWidget

class TestTab(Tab):
    def __init__(self, parent, name, index):
        super().__init__(parent, name, index)
        self.initUI()

    def initUI(self):
        self.left_dock_end_ratio = 0.25
        self.top_dock_end_ratio = 0.70
        self.right_dock_end_ratio = 0.25




        self.add_docks([TestDock, TestDock2],
                        0,
                        0,
                        self.left_dock_end_ratio,
                        1)

        self.add_docks([],
                        1 - self.right_dock_end_ratio,
                        0,
                        self.right_dock_end_ratio,
                        1)

        self.add_docks([TestDock, TestDock2],
                        self.left_dock_end_ratio,
                        0,
                        1 - self.left_dock_end_ratio - self.right_dock_end_ratio,
                        self.top_dock_end_ratio)

        self.add_docks([TestDock, TestDock],
                        self.left_dock_end_ratio,
                        self.top_dock_end_ratio,
                        1 - self.left_dock_end_ratio - self.right_dock_end_ratio,
                        1 - self.top_dock_end_ratio)
         