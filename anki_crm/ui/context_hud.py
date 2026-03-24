from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from ..models import Entity


TYPE_STYLES: dict[str, tuple[str, str]] = {
    "stakeholder": ("#1a1a2e", "#e94560"),
    "project":     ("#1a1a2e", "#0f3460"),
}
DEFAULT_STYLE = ("#1a1a2e", "#888888")


class EntityChip(QFrame):
    """
    Compact read-only chip displaying one entity.
    Emits clicked(entity_id: int) on mouse press.
    Color-coded by entity_type.
    """
    clicked = pyqtSignal(int)

    def __init__(self, entity: Entity, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entity_id = entity.id
        bg, accent = TYPE_STYLES.get(entity.entity_type, DEFAULT_STYLE)
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-left: 3px solid {accent};
                border-radius: 4px;
                padding: 2px 8px;
                margin: 2px 3px;
            }}
            QFrame:hover {{
                background: #2a2a3e;
            }}
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        type_badge = QLabel(entity.entity_type[:2].upper())
        type_badge.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        type_badge.setStyleSheet(f"color: {accent}; background: transparent;")

        name_label = QLabel(entity.name)
        name_label.setFont(QFont("system-ui", 10))
        name_label.setStyleSheet("color: #e0e0e0; background: transparent;")

        layout.addWidget(type_badge)
        layout.addWidget(name_label)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._entity_id)
        super().mousePressEvent(event)


class ContextHUD(QWidget):
    """
    Horizontal strip of EntityChip widgets shown during review.
    Call refresh(entities) to update. Call clear() to reset.
    chip_clicked(entity_id) signal fired when user clicks a chip.
    """
    chip_clicked = pyqtSignal(int)

    def __init__(self, max_height: int = 48, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumHeight(max_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QWidget {
                background-color: #0d1117;
                border-top: 1px solid #30363d;
            }
        """)
        self._build_layout()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 2, 6, 2)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._chip_widget = QWidget()
        self._chip_widget.setStyleSheet("background: transparent;")
        self._chip_layout = QHBoxLayout(self._chip_widget)
        self._chip_layout.setContentsMargins(0, 0, 0, 0)
        self._chip_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._scroll.setWidget(self._chip_widget)
        root.addWidget(self._scroll)

    def refresh(self, entities: list[Entity]) -> None:
        """Rebuild all chips from entity list. Immutable update — always clears first."""
        self._clear_chips()
        if not entities:
            placeholder = QLabel("No context linked  —  press Ctrl+L to link this card")
            placeholder.setStyleSheet(
                "color: #484f58; font-style: italic; font-size: 10px; background: transparent;"
            )
            self._chip_layout.addWidget(placeholder)
        else:
            for entity in entities:
                chip = EntityChip(entity, self._chip_widget)
                chip.clicked.connect(self.chip_clicked)
                self._chip_layout.addWidget(chip)
        self._chip_layout.addStretch()

    def clear(self) -> None:
        """Remove all chips and hide."""
        self._clear_chips()
        self.hide()

    def _clear_chips(self) -> None:
        while self._chip_layout.count():
            item = self._chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
