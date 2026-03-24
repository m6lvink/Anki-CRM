from __future__ import annotations
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QLineEdit, QLabel, QComboBox, QMessageBox, QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..models import Entity, ENTITY_TYPES
from ..db.repository import CRMRepository


class EntityManager(QDialog):
    """
    Tabbed CRUD manager for all entity types.
    Each tab: searchable table + Add / Edit / Delete buttons.
    """

    def __init__(self, repo: CRMRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repo = repo
        self.setWindowTitle("CRM Entity Manager")
        self.setMinimumSize(700, 500)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Entity Manager")
        title.setFont(QFont("system-ui", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        self._tabs = QTabWidget()
        for entity_type in sorted(ENTITY_TYPES):
            tab = EntityTab(entity_type, self._repo, self)
            self._tabs.addTab(tab, entity_type.title() + "s")

        layout.addWidget(self._tabs)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


class EntityTab(QWidget):
    """Single tab managing one entity_type."""

    COLUMNS = ["ID", "Name", "Metadata", "Created"]

    def __init__(self, entity_type: str, repo: CRMRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entity_type = entity_type
        self._repo = repo
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Search bar
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText(f"Search {self._entity_type}s...")
        self._search.textChanged.connect(self._on_search)
        search_row.addWidget(self._search)
        layout.addLayout(search_row)

        # Table
        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # Action buttons
        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add New")
        add_btn.clicked.connect(self._on_add)
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._on_edit)
        del_btn = QPushButton("Delete Selected")
        del_btn.setStyleSheet("color: #e94560;")
        del_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load(self, filter_text: str = "") -> None:
        self._table.setRowCount(0)
        entities = self._repo.list_entities(self._entity_type)
        for entity in entities:
            if filter_text and filter_text.lower() not in entity.name.lower():
                continue
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(entity.id)))
            self._table.setItem(row, 1, QTableWidgetItem(entity.name))
            # Pretty-print metadata JSON
            try:
                pretty = json.dumps(json.loads(entity.metadata_json), ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                pretty = entity.metadata_json
            self._table.setItem(row, 2, QTableWidgetItem(pretty))
            self._table.setItem(row, 3, QTableWidgetItem(entity.created_at[:10]))
            # Store entity id for later retrieval
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, entity.id)

    def _on_search(self, text: str) -> None:
        self._load(filter_text=text)

    def _selected_entity_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_add(self) -> None:
        dlg = EntityEditDialog(self._entity_type, self._repo, parent=self)
        if dlg.exec():
            self._load()

    def _on_edit(self) -> None:
        entity_id = self._selected_entity_id()
        if entity_id is None:
            QMessageBox.information(self, "Select Row", "Please select an entity to edit.")
            return
        entity = self._repo.get_entity(entity_id)
        if entity is None:
            QMessageBox.warning(self, "Not Found", "Entity no longer exists.")
            self._load()
            return
        dlg = EntityEditDialog(self._entity_type, self._repo, entity=entity, parent=self)
        if dlg.exec():
            self._load()

    def _on_delete(self) -> None:
        entity_id = self._selected_entity_id()
        if entity_id is None:
            QMessageBox.information(self, "Select Row", "Please select an entity to delete.")
            return
        linked_count = len(self._repo.get_cards_for_entity(entity_id))
        msg = "Delete this entity?"
        if linked_count > 0:
            msg += (
                f"\n\nWarning: it is currently linked to {linked_count} card(s). "
                "Those links will be removed."
            )
        result = QMessageBox.question(
            self, "Confirm Delete", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            try:
                self._repo.delete_entity(entity_id)
                self._load()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {e}")


class EntityEditDialog(QDialog):
    """Small dialog for creating or editing a single entity."""

    def __init__(
        self,
        entity_type: str,
        repo: CRMRepository,
        entity: Entity | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._entity_type = entity_type
        self._repo = repo
        self._entity = entity
        self.setWindowTitle("Edit Entity" if entity else "New Entity")
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Name:"))
        self._name_input = QLineEdit(self._entity.name if self._entity else "")
        layout.addWidget(self._name_input)

        layout.addWidget(QLabel("Metadata (JSON):"))
        self._meta_input = QTextEdit()
        self._meta_input.setMaximumHeight(100)
        self._meta_input.setPlaceholderText('e.g. {"title": "部長", "company": "Tanaka Corp"}')
        if self._entity:
            self._meta_input.setPlainText(self._entity.metadata_json)
        layout.addWidget(self._meta_input)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name cannot be empty.")
            return
        meta = self._meta_input.toPlainText().strip() or "{}"
        try:
            json.loads(meta)  # validate JSON before saving
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Invalid JSON", f"Metadata must be valid JSON:\n{e}")
            return
        try:
            if self._entity:
                self._repo.update_entity(self._entity.id, name=name, metadata_json=meta)
            else:
                self._repo.create_entity(name, self._entity_type, meta)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save: {e}")
