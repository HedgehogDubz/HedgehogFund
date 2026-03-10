import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt
from UI.TabDock import TabDock
from UI.Tabs.test_tab import TestTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HedgehogFund")

        # Enable drops on the main window to handle external dock creation
        self.setAcceptDrops(True)

        self.window_width = 1200
        self.window_height = 800

        self.setGeometry(0,0, self.window_width, self.window_height)
        self.center_on_screen()

        self.TD = TabDock(create_external_docks=True, min_dock_size=100)
        self.setCentralWidget(self.TD)

        tt = TestTab(self.TD, "Test Tab 1", 0)
        self.TD.add_tab(tt)
        tt = TestTab(self.TD, "Test Tab 2", 1)
        self.TD.add_tab(tt)
        
    def center_on_screen(self):
        screen = self.screen() or QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        frame_geo = self.frameGeometry()

        frame_geo.moveCenter(screen_geo.center())
        self.move(frame_geo.topLeft())

    







        





def start_UI():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())