from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QWidget, QSplitter, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from ..models import Entity, ENTITY_TYPES
from ..db.repository import CRMRepository


class LinkEditor(QDialog):
    """
    Two-panel dialog: left = currently linked entities, right = all entities (searchable).
    Emits links_changed() on any modification so HUD can refresh.
    """
    links_changed = pyqtSignal()

    def __init__(self, card_id: int, repo: CRMRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._card_id = card_id
        self._repo = repo
        self._all_available: list[Entity] = []
        self.setWindowTitle(f"Link Card to Entities — Card {card_id}")
        self.setMinimumSize(640, 420)
        self.setModal(True)
        self._build_ui()
        self._refresh_both_panels()

        close_shortcut = QShortcut(QKeySequence("Escape"), self)
        close_shortcut.activated.connect(self.close)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Link Card to Entities")
        title.setFont(QFont("system-ui", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        # Splitter: linked (left) | available (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: Linked entities
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Linked to this card:"))
        self._linked_list = QListWidget()
        self._linked_list.setAlternatingRowColors(True)
        left_layout.addWidget(self._linked_list)
        self._unlink_btn = QPushButton("Remove Selected")
        self._unlink_btn.clicked.connect(self._on_unlink)
        left_layout.addWidget(self._unlink_btn)

        # RIGHT: All entities (searchable)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("All entities:"))

        search_row = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Filter by name...")
        self._search_box.textChanged.connect(self._filter_available)
        self._type_filter = QComboBox()
        self._type_filter.addItem("All types", None)
        for t in sorted(ENTITY_TYPES):
            self._type_filter.addItem(t.title(), t)
        self._type_filter.currentIndexChanged.connect(self._filter_available)
        search_row.addWidget(self._search_box)
        search_row.addWidget(self._type_filter)
        right_layout.addLayout(search_row)

        self._available_list = QListWidget()
        self._available_list.setAlternatingRowColors(True)
        right_layout.addWidget(self._available_list)

        link_btn = QPushButton("Link Selected →")
        link_btn.clicked.connect(self._on_link)
        right_layout.addWidget(link_btn)

        # New entity inline form
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        right_layout.addWidget(sep)
        right_layout.addWidget(QLabel("Create new entity:"))
        new_row = QHBoxLayout()
        self._new_name = QLineEdit()
        self._new_name.setPlaceholderText("Entity name")
        self._new_type = QComboBox()
        for t in sorted(ENTITY_TYPES):
            self._new_type.addItem(t.title(), t)
        create_btn = QPushButton("Create & Link")
        create_btn.clicked.connect(self._on_create_and_link)
        new_row.addWidget(self._new_name)
        new_row.addWidget(self._new_type)
        new_row.addWidget(create_btn)
        right_layout.addLayout(new_row)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([280, 360])
        layout.addWidget(splitter)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _refresh_both_panels(self) -> None:
        self._refresh_linked()
        self._refresh_available()

    def _refresh_linked(self) -> None:
        self._linked_list.clear()
        try:
            entities = self._repo.get_links_for_card(self._card_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load links: {e}")
            return
        for entity in entities:
            item = QListWidgetItem(f"[{entity.entity_type.upper()}] {entity.name}")
            item.setData(Qt.ItemDataRole.UserRole, entity.id)
            self._linked_list.addItem(item)

    def _refresh_available(self) -> None:
        self._available_list.clear()
        try:
            entities = self._repo.list_entities()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load entities: {e}")
            return
        self._all_available = entities
        self._apply_filter(entities)

    def _filter_available(self) -> None:
        self._apply_filter(self._all_available)

    def _apply_filter(self, entities: list[Entity]) -> None:
        self._available_list.clear()
        query = self._search_box.text().lower()
        type_filter = self._type_filter.currentData()
        for entity in entities:
            if type_filter and entity.entity_type != type_filter:
                continue
            if query and query not in entity.name.lower():
                continue
            item = QListWidgetItem(f"[{entity.entity_type.upper()}] {entity.name}")
            item.setData(Qt.ItemDataRole.UserRole, entity.id)
            self._available_list.addItem(item)

    def _on_link(self) -> None:
        item = self._available_list.currentItem()
        if not item:
            return
        entity_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            self._repo.link_card(self._card_id, entity_id)
            self.links_changed.emit()
            self._refresh_linked()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not link: {e}")

    def _on_unlink(self) -> None:
        item = self._linked_list.currentItem()
        if not item:
            return
        entity_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            self._repo.unlink_card(self._card_id, entity_id)
            self.links_changed.emit()
            self._refresh_linked()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not unlink: {e}")

    def _on_create_and_link(self) -> None:
        name = self._new_name.text().strip()
        entity_type = self._new_type.currentData()
        if not name:
            QMessageBox.warning(self, "Validation", "Entity name cannot be empty.")
            return
        try:
            entity = self._repo.create_entity(name, entity_type)
            self._repo.link_card(self._card_id, entity.id)
            self._new_name.clear()
            self.links_changed.emit()
            self._refresh_both_panels()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create entity: {e}")
