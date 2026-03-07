from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen, QDrag
from PyQt6.QtCore import Qt, QMimeData
from UI._style_guide import bg, black, border_color
import math

class DraggableTabButton(QPushButton):
    def __init__(self, text, dock, index):
        super().__init__(text)
        self.dock = dock
        self.index = index
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.drag_start_position is None:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("dockable_window")
        drag.setMimeData(mime_data)

        Dock._drag_source_dock = self.dock
        Dock._drag_window_index = self.index

        drag.exec(Qt.DropAction.MoveAction)

class Dock(QFrame):
    _drag_source_dock = None
    _drag_window_index = None

    def __init__(self, parent, dockable_windows, x_ratio, y_ratio, w_ratio, h_ratio):
        self.parent = parent
        super().__init__(parent.centralWidget())

        self.setStyleSheet(f"background-color: {black}; margin: 0px;")
        self.setAcceptDrops(True)

        self.x_ratio = x_ratio
        self.y_ratio = y_ratio
        self.w_ratio = w_ratio
        self.h_ratio = h_ratio

        dock_x = int(x_ratio * parent.width())
        dock_y = int(y_ratio * parent.height())
        x_end = int((x_ratio + w_ratio) * parent.width())
        y_end = int((y_ratio + h_ratio) * parent.height())
        dock_w = x_end - dock_x
        dock_h = y_end - dock_y

        self.setGeometry(dock_x, dock_y, dock_w, dock_h)

        self.dockIndex = 0
        self.dockable_windows_classes = dockable_windows
        self.dockable_windows = []
        self.tab_buttons = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(0)

        self.tab_bar_widget = QWidget()
        self.tab_bar_widget.setStyleSheet("margin: 0px; padding: 0px; border: none;")
        self.tab_bar_widget.setContentsMargins(0, 0, 0, 0)

        self.tab_bar = QHBoxLayout(self.tab_bar_widget)
        self.tab_bar.setContentsMargins(0, 0, 0, 0)
        self.tab_bar.setSpacing(0)

        for i, dw_class in enumerate(dockable_windows):
            tab_button = DraggableTabButton(dw_class.__name__, self, i)
            tab_button.setFlat(True)
            tab_button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px;")
            tab_button.setContentsMargins(0, 0, 0, 0)
            tab_button.clicked.connect(lambda _, index=i: self.switch_tab(index))
            self.tab_buttons.append(tab_button)
            self.tab_bar.addWidget(tab_button)

            dw_instance = dw_class(self, True, 0, 0, int(math.ceil(self.w_ratio * parent.width())), int(math.ceil(self.h_ratio * parent.height())))
            dw_instance.hide()
            self.dockable_windows.append(dw_instance)

        self.layout.addWidget(self.tab_bar_widget, 0)

        for dw in self.dockable_windows:
            self.layout.addWidget(dw, 1)

        if self.dockable_windows:
            self.switch_tab(0)

    def update_geometry(self):
        parent_width = self.parent.width()
        parent_height = self.parent.height()

        dock_x = int(self.x_ratio * parent_width)
        dock_y = int(self.y_ratio * parent_height)
        x_end = int((self.x_ratio + self.w_ratio) * parent_width)
        y_end = int((self.y_ratio + self.h_ratio) * parent_height)
        dock_w = x_end - dock_x
        dock_h = y_end - dock_y

        self.setGeometry(dock_x, dock_y, dock_w, dock_h)
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        pen = QPen(QColor(border_color))
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

    def switch_tab(self, index):
        if 0 <= index < len(self.dockable_windows):
            if 0 <= self.dockIndex < len(self.dockable_windows):
                self.dockable_windows[self.dockIndex].hide()

            self.dockIndex = index
            self.dockable_windows[self.dockIndex].show()

            for i, button in enumerate(self.tab_buttons):
                if i == index:
                    button.setStyleSheet(f"background-color: {bg}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px;")
                else:
                    button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            if Dock._drag_source_dock is not None and Dock._drag_source_dock != self:
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "dockable_window":
            if Dock._drag_source_dock is not None and Dock._drag_source_dock != self:
                event.acceptProposedAction()

    def dropEvent(self, event):
        if Dock._drag_source_dock is not None and Dock._drag_window_index is not None:
            source_dock = Dock._drag_source_dock
            window_index = Dock._drag_window_index

            if source_dock != self:
                dockable_window = source_dock.dockable_windows[window_index]
                window_name = dockable_window.__class__.__name__

                source_dock.remove_dockable_window(window_index)
                self.add_dockable_window(dockable_window, window_name)

                event.acceptProposedAction()

            Dock._drag_source_dock = None
            Dock._drag_window_index = None

    def remove_dockable_window(self, index):
        if 0 <= index < len(self.dockable_windows):
            dw = self.dockable_windows.pop(index)
            button = self.tab_buttons.pop(index)

            self.layout.removeWidget(dw)
            self.tab_bar.removeWidget(button)
            button.deleteLater()

            for i, btn in enumerate(self.tab_buttons):
                btn.index = i
                btn.clicked.disconnect()
                btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

            if self.dockable_windows:
                self.dockIndex = min(self.dockIndex, len(self.dockable_windows) - 1)
                self.switch_tab(self.dockIndex)
            else:
                self.dockIndex = 0

    def add_dockable_window(self, dockable_window, window_name):
        index = len(self.dockable_windows)

        tab_button = DraggableTabButton(window_name, self, index)
        tab_button.setFlat(True)
        tab_button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px;")
        tab_button.setContentsMargins(0, 0, 0, 0)
        tab_button.clicked.connect(lambda _, idx=index: self.switch_tab(idx))
        self.tab_buttons.append(tab_button)
        self.tab_bar.addWidget(tab_button)

        dockable_window.setParent(self)
        dockable_window.hide()
        self.dockable_windows.append(dockable_window)
        self.layout.addWidget(dockable_window, 1)

        self.switch_tab(index)

