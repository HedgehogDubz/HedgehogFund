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

    def delete_dock(self, dock):
        """Delete a dock and redistribute its space to neighbors"""
        if dock not in self.docks:
            return

        # Find horizontal and vertical neighbors
        dock_left = dock.x_ratio
        dock_right = dock.x_ratio + dock.w_ratio
        dock_top = dock.y_ratio
        dock_bottom = dock.y_ratio + dock.h_ratio

        # Find connectors associated with this dock
        connectors_to_remove = []
        for connector in self.connectors:
            if hasattr(connector, 'left_dock') and hasattr(connector, 'right_dock'):
                # Horizontal connector
                if connector.left_dock == dock or connector.right_dock == dock:
                    connectors_to_remove.append(connector)
            elif hasattr(connector, 'top_dock') and hasattr(connector, 'bottom_dock'):
                # Vertical connector
                if connector.top_dock == dock or connector.bottom_dock == dock:
                    connectors_to_remove.append(connector)

        # Find neighbors to expand
        left_neighbor = None
        right_neighbor = None
        top_neighbor = None
        bottom_neighbor = None

        for other_dock in self.docks:
            if other_dock == dock:
                continue

            # Check for left neighbor (dock to the left that shares the left edge)
            if abs((other_dock.x_ratio + other_dock.w_ratio) - dock_left) < 0.01:
                if not (other_dock.y_ratio >= dock_bottom or (other_dock.y_ratio + other_dock.h_ratio) <= dock_top):
                    left_neighbor = other_dock

            # Check for right neighbor (dock to the right that shares the right edge)
            if abs(other_dock.x_ratio - dock_right) < 0.01:
                if not (other_dock.y_ratio >= dock_bottom or (other_dock.y_ratio + other_dock.h_ratio) <= dock_top):
                    right_neighbor = other_dock

            # Check for top neighbor (dock above that shares the top edge)
            if abs((other_dock.y_ratio + other_dock.h_ratio) - dock_top) < 0.01:
                if not (other_dock.x_ratio >= dock_right or (other_dock.x_ratio + other_dock.w_ratio) <= dock_left):
                    top_neighbor = other_dock

            # Check for bottom neighbor (dock below that shares the bottom edge)
            if abs(other_dock.y_ratio - dock_bottom) < 0.01:
                if not (other_dock.x_ratio >= dock_right or (other_dock.x_ratio + other_dock.w_ratio) <= dock_left):
                    bottom_neighbor = other_dock

        # Expand neighbors to fill the gap
        if left_neighbor:
            left_neighbor.w_ratio += dock.w_ratio
        elif right_neighbor:
            right_neighbor.x_ratio = dock.x_ratio
            right_neighbor.w_ratio += dock.w_ratio

        if top_neighbor:
            top_neighbor.h_ratio += dock.h_ratio
        elif bottom_neighbor:
            bottom_neighbor.y_ratio = dock.y_ratio
            bottom_neighbor.h_ratio += dock.h_ratio

        # Remove connectors
        for connector in connectors_to_remove:
            connector.hide()
            connector.deleteLater()
            self.remove_connector(connector)

        # Remove the dock
        dock.hide()
        dock.deleteLater()
        self.remove_dock(dock)

        # Update geometry of all remaining docks
        for remaining_dock in self.docks:
            remaining_dock.update_geometry()