from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtWidgets import QApplication
from tabdock.tab import Tab


class ConnectorManager(QObject):
    """Manages all HConnector and VConnector instances and handles mouse events via event filter."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.connectors: list = []
        self.active_connector = None
        self._override_active = False

        # Enable mouse tracking on parent
        parent.setMouseTracking(True)

        # Install event filter at the APPLICATION level so we see every event
        # regardless of which child widget the mouse is over.
        QApplication.instance().installEventFilter(self)

    def add_connector(self, connector):
        """Register a connector (HConnector or VConnector) with the manager."""
        self.connectors.append(connector)
        self._enable_tracking_on_children()

    def remove_connector(self, connector):
        """Unregister a connector."""
        if connector in self.connectors:
            self.connectors.remove(connector)

    def _enable_tracking_on_children(self):
        """Enable mouse tracking on all child widgets."""
        from PyQt6.QtWidgets import QWidget

        children = self.parent_widget.findChildren(QWidget)
        for child in children:
            if not child.hasMouseTracking():
                child.setMouseTracking(True)

    def _find_closest_connector(self, pos, current_tab=None):
        """Find the connector closest to the given position.

        If ``current_tab`` is provided, only consider connectors that belong to
        that :class:`Tab`. This avoids accidentally dragging connectors for a
        hidden tab, which would update invisible docks and appear to "do
        nothing" to the user.
        """

        closest_connector = None
        min_distance = float("inf")

        for connector in self.connectors:
            if current_tab is not None:
                connector_tab = getattr(connector, "tab", None)
                if connector_tab is not None and connector_tab is not current_tab:
                    continue

            if connector.is_near_connector(pos):
                distance = connector.get_distance_to_connector(pos)
                if distance < min_distance:
                    min_distance = distance
                    closest_connector = connector

        return closest_connector

    def _set_override_cursor(self, cursor_shape):
        """Set application-wide override cursor."""
        if self._override_active:
            QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(cursor_shape)
        self._override_active = True

    def _restore_cursor(self):
        """Remove the application-wide override cursor."""
        if self._override_active:
            QApplication.restoreOverrideCursor()
            self._override_active = False

    def _is_child_of_parent(self, widget):
        """Check if widget is the parent_widget or one of its descendants."""
        w = widget
        while w is not None:
            if w is self.parent_widget:
                return True
            w = w.parentWidget()
        return False

    def _get_current_tab(self, obj):
        """Walk up from obj to find the Tab ancestor, if any."""
        widget = obj
        while widget is not None:
            if isinstance(widget, Tab):
                return widget
            widget = widget.parentWidget()
        return None

    def eventFilter(self, obj, event):
        """Application-level event filter to handle connector interactions."""

        event_type = event.type()

        # Handle Leave — restore cursor if leaving our widget tree
        if event_type == QEvent.Type.Leave:
            if obj is self.parent_widget and not self.active_connector:
                self._restore_cursor()
            return False

        if event_type not in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
        ):
            return False

        # Only handle events from widgets inside our parent tree
        from PyQt6.QtWidgets import QWidget
        if not isinstance(obj, QWidget) or not self._is_child_of_parent(obj):
            return False

        if not hasattr(event, "pos"):
            return False

        # Map position to parent_widget coordinates
        if obj is self.parent_widget:
            pos = event.pos()
        else:
            pos = obj.mapTo(self.parent_widget, event.pos())

        current_tab = self._get_current_tab(obj)

        # Handle mouse press
        if event_type == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self.active_connector = closest
                    self.active_connector.start_drag(pos)
                    self._set_override_cursor(
                        self.active_connector.get_cursor_shape(is_dragging=True)
                    )
                    return True

        # Handle mouse move
        elif event_type == QEvent.Type.MouseMove:
            active = self.active_connector
            if active:
                active.update_drag(pos)
                self._set_override_cursor(active.get_cursor_shape(is_dragging=True))
                return True
            else:
                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self._set_override_cursor(closest.get_cursor_shape(is_dragging=False))
                else:
                    self._restore_cursor()

        # Handle mouse release
        elif event_type == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and self.active_connector:
                self.active_connector.end_drag(pos)

                closest = self._find_closest_connector(pos, current_tab)
                if closest:
                    self._set_override_cursor(closest.get_cursor_shape(is_dragging=False))
                else:
                    self._restore_cursor()

                self.active_connector = None
                return True

        return False
