from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QApplication
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor, QPixmap
from PyQt6.QtCore import Qt, QPoint
from UI._style_guide import bg, black, border_color
import math

class DragPreviewWidget(QWidget):
    """Floating widget that shows a preview of the tab being dragged"""
    def __init__(self, text, size):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setFixedSize(size)

        self.button_text = text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setOpacity(1.0)
        painter.fillRect(self.rect(), QColor(bg))

        painter.setOpacity(1.0)
        painter.setPen(QColor("white"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.button_text)

class DraggableTabButton(QPushButton):
    def __init__(self, text, dock, index):
        super().__init__(text)
        self.dock = dock
        self.index = index
        self.drag_start_position = None
        self.drag_preview = None
        self.is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.drag_start_position is None:
            return

        if not self.is_dragging:
            if (event.pos() - self.drag_start_position).manhattanLength() < 10:
                return

            self.is_dragging = True
            Dock._drag_source_dock = self.dock
            Dock._drag_window_index = self.index

            self.hide()

            self.dock._hide_dragged_tab(self.index)

            self.drag_preview = DragPreviewWidget(self.text(), self.size())
            self.drag_preview.show()

            self.grabMouse()

        if self.drag_preview:
            cursor_pos = QCursor.pos()
            self.drag_preview.move(
                cursor_pos.x() - self.drag_preview.width() // 2,
                cursor_pos.y() - self.drag_preview.height() // 2
            )

            self._update_drop_targets(cursor_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.releaseMouse()

            if self.drag_preview:
                self.drag_preview.close()
                self.drag_preview.deleteLater()
                self.drag_preview = None

            # Handle the drop
            self._handle_drop(QCursor.pos())

            # Clean up all preview buttons in all docks
            app = QApplication.instance()
            for widget in app.allWidgets():
                if isinstance(widget, Dock):
                    widget._hide_drop_preview()

            # Only show the dragged tab if it still exists in the source dock
            # (it won't exist if it was moved to a different dock)
            if Dock._drag_source_dock and Dock._drag_window_index is not None:
                if Dock._drag_window_index < len(Dock._drag_source_dock.tab_buttons):
                    Dock._drag_source_dock._show_dragged_tab(Dock._drag_window_index)

            self.is_dragging = False
            self.drag_start_position = None
        else:
            super().mouseReleaseEvent(event)

    def _update_drop_targets(self, global_pos):
        app = QApplication.instance()

        if self.drag_preview:
            self.drag_preview.hide()

        widget_at_cursor = app.widgetAt(global_pos)

        target_dock = None
        current = widget_at_cursor
        while current:
            if isinstance(current, Dock):
                target_dock = current
                break
            current = current.parentWidget()

        all_docks = [widget for widget in app.allWidgets() if isinstance(widget, Dock)]

        if target_dock:
            local_pos = target_dock.mapFromGlobal(global_pos)
            if target_dock._is_over_tab_bar(local_pos):
                target_dock._update_drop_preview(local_pos)
                for dock in all_docks:
                    if dock != target_dock:
                        dock._hide_drop_preview()
            else:
                for dock in all_docks:
                    dock._hide_drop_preview()
                if self.drag_preview:
                    self.drag_preview.show()
        else:
            for dock in all_docks:
                dock._hide_drop_preview()
            if self.drag_preview:
                self.drag_preview.show()

    def _handle_drop(self, global_pos):
        """Handle the drop at the given global position"""
        app = QApplication.instance()
        widget_at_cursor = app.widgetAt(global_pos)

        # Find the Dock widget if cursor is over one
        target_dock = None
        current = widget_at_cursor
        while current:
            if isinstance(current, Dock):
                target_dock = current
                break
            current = current.parentWidget()

        if target_dock:
            #internal dock
            local_pos = target_dock.mapFromGlobal(global_pos)

            if target_dock._is_over_tab_bar(local_pos):
                self._handle_tab_move(target_dock, local_pos)
            else:
                self._create_external_dock()
        else:
            # external dock
            tab_dock = self._get_tab_dock()
            if tab_dock and hasattr(tab_dock, 'create_external_docks') and tab_dock.create_external_docks:
                self._create_external_dock()
            else:
                self.show()

        # Clear drag state
        Dock._drag_source_dock = None
        Dock._drag_window_index = None

    def _handle_tab_move(self, target_dock, local_pos):
        """Move tab to target dock at the drop position"""
        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index

        if source_dock is None or window_index is None:
            return

        panel = source_dock.panels[window_index]
        window_name = panel.__class__.__name__

        insert_index = target_dock._calculate_insert_index(local_pos)

        if source_dock == target_dock:
            # Reordering within same dock
            if insert_index > window_index:
                insert_index -= 1
            if insert_index != window_index:
                # IMPORTANT: Hide preview BEFORE removing panel to avoid layout corruption
                target_dock._hide_drop_preview()
                source_dock.remove_panel(window_index)
                target_dock.add_panel(panel, window_name, insert_index)
            else:
                target_dock._hide_drop_preview()
                self.show()
                if 0 <= window_index < len(source_dock.panels):
                    source_dock.panels[window_index].show()
                    source_dock.dockIndex = window_index
        else:
            # Moving between docks
            # IMPORTANT: Hide preview BEFORE removing panel to avoid layout corruption
            target_dock._hide_drop_preview()
            source_dock.remove_panel(window_index)
            target_dock.add_panel(panel, window_name, insert_index)

    def _get_tab_dock(self):
        """Get the TabDock instance from the parent chain, or ExternalDock if applicable"""
        try:
            # Dock has a parent attribute (Tab instance or ExternalDock)
            dock_parent = self.dock.parent
            if dock_parent is None:
                return None

            # Check if parent is an ExternalDock (which supports creating more external docks)
            if isinstance(dock_parent, ExternalDock):
                return dock_parent

            if hasattr(dock_parent, '__dict__') and 'parent' in dock_parent.__dict__:
                tab_dock = dock_parent.__dict__['parent']
                if hasattr(tab_dock, 'create_external_docks'):
                    return tab_dock
        except Exception:
            pass

        return None

    def _create_external_dock(self):
        """Create an external floating dock with the dragged panel"""
        if Dock._drag_source_dock is None or Dock._drag_window_index is None:
            return

        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index

        # Get the panel
        panel = source_dock.panels[window_index]
        panel_name = panel.__class__.__name__

        external_dock = ExternalDock(panel_name)
        source_dock.remove_panel(window_index)

        external_dock.dock.add_panel(panel, panel_name, 0, is_external=True)

        cursor_pos = QCursor.pos()
        external_dock.show()
        external_dock.move(cursor_pos.x() - 40, cursor_pos.y() - 43)

class ExternalDock(QWidget):
    """A floating window that contains a single Dock"""
    def __init__(self, window_name, width=400, height=300):
        super().__init__()
        self.setWindowTitle(f"External Dock - {window_name}")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(width, height)

        # Store that external docks are enabled (since this IS an external dock)
        self.create_external_docks = True

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create a dock that fills this window
        self.dock = Dock(self, [], 0, 0, 1, 1)
        layout.addWidget(self.dock)

    def centralWidget(self):
        """Return self as the central widget for Dock compatibility"""
        return self

    def width(self):
        """Override to provide width for Dock"""
        return super().width()

    def height(self):
        """Override to provide height for Dock"""
        return super().height()

class Dock(QFrame):
    _drag_source_dock = None
    _drag_window_index = None
    _preview_dock = None

    def __init__(self, parent, panels, x_ratio, y_ratio, w_ratio, h_ratio):
        self.parent = parent
        super().__init__(parent.centralWidget())

        self.setStyleSheet(f"background-color: {black}; margin: 0px;")
        self.setAcceptDrops(True)
        self.preview_button = None
        self.drop_insert_index = -1
        self.preview_active = False

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
        self.panel_classes = panels
        self.panels = []
        self.tab_buttons = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(0)

        self.tab_bar_widget = QWidget()
        self.tab_bar_widget.setStyleSheet("margin: 0px; padding: 0px; border: none;")
        self.tab_bar_widget.setContentsMargins(0, 0, 0, 0)
        self.tab_bar_widget.setAcceptDrops(False)
        self.tab_bar_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.tab_bar_widget.setFixedHeight(25)

        self.tab_bar = QHBoxLayout(self.tab_bar_widget)
        self.tab_bar.setContentsMargins(0, 0, 0, 0)
        self.tab_bar.setSpacing(0)
        self.tab_bar.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.tab_bar.addStretch()

        for i, panel_class in enumerate(panels):
            tab_button = DraggableTabButton(panel_class.__name__, self, i)
            tab_button.setFlat(True)
            tab_button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px;")
            tab_button.setContentsMargins(0, 0, 0, 0)
            tab_button.setAcceptDrops(False)
            tab_button.clicked.connect(lambda _, index=i: self.switch_tab(index))
            self.tab_buttons.append(tab_button)
            self.tab_bar.insertWidget(i, tab_button)

            panel_instance = panel_class(self, True, 0, 0, int(math.ceil(self.w_ratio * parent.width())), int(math.ceil(self.h_ratio * parent.height())))
            panel_instance.hide()
            self.panels.append(panel_instance)

        self.layout.addWidget(self.tab_bar_widget, 0)

        for panel in self.panels:
            self.layout.addWidget(panel, 1)

        if self.panels:
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

        old_geometry = self.geometry()
        self.setGeometry(dock_x, dock_y, dock_w, dock_h)

        if old_geometry != self.geometry():
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
        if 0 <= index < len(self.panels):
            if 0 <= self.dockIndex < len(self.panels):
                self.panels[self.dockIndex].hide()

            self.dockIndex = index
            self.panels[self.dockIndex].show()

            for i, button in enumerate(self.tab_buttons):
                if i == index:
                    button.setStyleSheet(f"background-color: {bg}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px;")
                else:
                    button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "panel":
            if Dock._drag_source_dock is not None:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "panel":
            if Dock._drag_source_dock is not None:
                pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
                if self._is_over_tab_bar(pos):
                    self._update_drop_preview(pos)
                else:
                    self._hide_drop_preview()
                # Accept the drag move event regardless of position
                # This ensures dropEvent will be called even when not over tab bar
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return
        event.ignore()

    def dragLeaveEvent(self, _):
        self._hide_drop_preview()

    def dropEvent(self, event):
        if Dock._drag_source_dock is not None and Dock._drag_window_index is not None:
            source_dock = Dock._drag_source_dock
            window_index = Dock._drag_window_index

            pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()

            if self._is_over_tab_bar(pos):
                panel = source_dock.panels[window_index]
                window_name = panel.__class__.__name__

                insert_index = self.drop_insert_index if self.drop_insert_index >= 0 else self._calculate_insert_index(pos)

                if source_dock == self:
                    if insert_index > window_index:
                        insert_index -= 1
                    if insert_index != window_index:
                        source_dock.remove_panel(window_index)
                        self._hide_drop_preview()
                        self.add_panel(panel, window_name, insert_index)
                    else:
                        self._hide_drop_preview()
                else:
                    source_dock.remove_panel(window_index)
                    self._hide_drop_preview()
                    self.add_panel(panel, window_name, insert_index)
                    if self.parent is None and self.panels:
                        self.hide()

                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                Dock._drag_source_dock = None
                Dock._drag_window_index = None
                return
            else:
                # Not over tab bar - create external dock here since event won't bubble up
                self._hide_drop_preview()

                # Create external dock at cursor position
                window = source_dock.panels[window_index]
                window_name = window.__class__.__name__

                from UI.dock import ExternalDock
                external_dock = ExternalDock(window_name)

                # Remove from source
                source_dock.remove_panel(window_index)

                # Add to external dock
                external_dock.dock.add_panel(window, window_name, 0)

                # Position at cursor
                cursor_pos = QCursor.pos()
                external_dock.move(cursor_pos.x() - 100, cursor_pos.y() - 20)

                # Show the external dock
                external_dock.show()

                # Clear drag state
                Dock._drag_source_dock = None
                Dock._drag_window_index = None

                # Accept the drop to prevent return animation
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                return

        # Only clear drag state if no drag was active
        event.ignore()

    def _is_over_tab_bar(self, pos):
        tab_bar_rect = self.tab_bar_widget.geometry()
        result = tab_bar_rect.contains(pos)

        # Fallback: accept drops if Y is within the tab bar's height OR within top 50px
        # This handles edge cases where geometry() doesn't perfectly align
        # or when dragging from external docks
        if not result:
            # Check if Y position is within the tab bar's height (regardless of where it is)
            # OR if it's in the top 50 pixels of the dock
            tab_bar_height = tab_bar_rect.height()
            if pos.y() <= tab_bar_height + 5 or pos.y() <= 50:
                # Also check if X is roughly within the dock's width
                if 0 <= pos.x() <= self.width():
                    return True

        return result

    def _calculate_insert_index(self, pos):
        mouse_x = pos.x()

        if not self.tab_buttons:
            return 0

        for i, button in enumerate(self.tab_buttons):
            button_global_pos = button.mapToGlobal(button.rect().topLeft())
            button_parent_pos = self.mapFromGlobal(button_global_pos)
            button_left = button_parent_pos.x()
            button_right = button_left + button.width()
            button_center = button_left + button.width() / 2

            if button_left <= mouse_x <= button_right:
                if mouse_x < button_center:
                    return i
                else:
                    return i + 1
            elif mouse_x < button_left:
                return i

        return len(self.tab_buttons)

    def _hide_dragged_tab(self, index):
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].hide()
            if self.dockIndex == index:
                if len(self.panels) > 1:
                    for i in range(len(self.panels)):
                        if i != index:
                            self.switch_tab(i)
                            break
                else:
                    if 0 <= index < len(self.panels):
                        self.panels[index].hide()

    def _show_dragged_tab(self, index):
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].show()

    def _update_drop_preview(self, pos):
        if Dock._drag_source_dock is None or Dock._drag_window_index is None:
            return

        insert_index = self._calculate_insert_index(pos)

        if self.preview_active and self.drop_insert_index == insert_index:
            return

        if Dock._preview_dock and Dock._preview_dock != self:
            Dock._preview_dock._hide_drop_preview()

        source_dock = Dock._drag_source_dock
        window_index = Dock._drag_window_index
        panel = source_dock.panels[window_index]
        window_name = panel.__class__.__name__

        is_same_dock = (Dock._preview_dock == self)

        if not is_same_dock:
            self._hide_drop_preview()

            for dw in self.panels:
                dw.hide()

            if source_dock != self:
                already_in_layout = False
                for i in range(self.layout.count()):
                    item = self.layout.itemAt(i)
                    if item and item.widget() == panel:
                        already_in_layout = True
                        break

                if not already_in_layout:
                    source_dock.layout.removeWidget(panel)
                    panel.setParent(self)
                    self.layout.addWidget(panel, 1)

            panel.show()
            panel.raise_()
        else:
            if self.preview_button is not None:
                self.tab_bar.removeWidget(self.preview_button)
                self.preview_button.deleteLater()

        self.preview_button = QPushButton(window_name)
        self.preview_button.setFlat(True)
        self.preview_button.setStyleSheet(f"background-color: {bg}; color: white; border: none; padding: 5px 10px; margin: 0px; border-top-left-radius: 5px; border-top-right-radius: 5px; opacity: 0.7;")
        self.preview_button.setContentsMargins(0, 0, 0, 0)
        self.preview_button.setEnabled(False)

        self.tab_bar.insertWidget(insert_index, self.preview_button)
        self.preview_button.show()

        self.drop_insert_index = insert_index
        self.preview_active = True
        Dock._preview_dock = self

    def _hide_drop_preview(self):
        if not self.preview_active:
            return

        if self.preview_button is not None:
            self.preview_button.hide()
            self.tab_bar.removeWidget(self.preview_button)
            self.preview_button.setParent(None)
            self.preview_button.deleteLater()
            self.preview_button = None

        if Dock._drag_source_dock and Dock._drag_window_index is not None:
            source_dock = Dock._drag_source_dock
            window_index = Dock._drag_window_index
            if 0 <= window_index < len(source_dock.panels):
                panel = source_dock.panels[window_index]

                if source_dock != self:
                    panel.hide()

                    for i in range(self.layout.count()):
                        item = self.layout.itemAt(i)
                        if item and item.widget() == panel:
                            self.layout.removeWidget(panel)
                            break

                    panel.setParent(source_dock)

                    already_in_layout = False
                    for i in range(source_dock.layout.count()):
                        item = source_dock.layout.itemAt(i)
                        if item and item.widget() == panel:
                            already_in_layout = True
                            break

                    if not already_in_layout:
                        source_dock.layout.addWidget(panel, 1)

                    if 0 <= source_dock.dockIndex < len(source_dock.panels):
                        if Dock._drag_window_index == source_dock.dockIndex:
                            pass
                        else:
                            source_dock.panels[source_dock.dockIndex].show()
                else:
                    panel.hide()

        for dw in self.panels:
            dw.hide()

        if len(self.panels) > 0 and 0 <= self.dockIndex < len(self.panels):
            if Dock._drag_source_dock == self and Dock._drag_window_index == self.dockIndex:
                pass
            else:
                self.panels[self.dockIndex].show()

        self.drop_insert_index = -1
        self.preview_active = False

        if Dock._preview_dock == self:
            Dock._preview_dock = None

    def remove_panel(self, index):
        if 0 <= index < len(self.panels):
            panel = self.panels.pop(index)
            button = self.tab_buttons.pop(index)

            panel.hide()
            self.layout.removeWidget(panel)
            panel.setParent(None)

            self.tab_bar.removeWidget(button)
            button.deleteLater()

            for i, btn in enumerate(self.tab_buttons):
                btn.index = i
                btn.clicked.disconnect()
                btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

            if self.panels:
                # If we removed a panel before the active one, adjust the index
                if index < self.dockIndex:
                    self.dockIndex -= 1
                # Make sure dockIndex is still valid
                self.dockIndex = min(self.dockIndex, len(self.panels) - 1)
                self.switch_tab(self.dockIndex)
            else:
                self.dockIndex = 0
                # If this is an external dock and it's now empty, close it
                if isinstance(self.parent, ExternalDock):
                    self.parent.close()

    def add_panel(self, panel, panel_name, insert_index=None, is_external=False):
        if insert_index is None:
            insert_index = len(self.panels)

        insert_index = max(0, min(insert_index, len(self.panels)))

        tab_button = DraggableTabButton(panel_name, self, insert_index)
        tab_button.setFlat(True)
        tab_button.setStyleSheet(f"background-color: {black}; color: white; border: none; padding: 5px 10px; margin: 0px;")
        tab_button.setContentsMargins(0, 0, 0, 0)
        tab_button.clicked.connect(lambda _, idx=insert_index: self.switch_tab(idx))
        self.tab_buttons.insert(insert_index, tab_button)
        self.tab_bar.insertWidget(insert_index, tab_button)

        panel.setParent(self)
        panel.hide()
        self.panels.insert(insert_index, panel)
        self.layout.addWidget(panel, 1)

        for i, btn in enumerate(self.tab_buttons):
            btn.index = i
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))

        self.switch_tab(insert_index)

