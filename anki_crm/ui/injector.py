from __future__ import annotations
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtGui import QKeySequence, QShortcut
from .context_hud import ContextHUD
from .link_editor import LinkEditor
from ..db.repository import CRMRepository


class HUDInjector:
    """
    Wires ContextHUD into Anki's reviewer lifecycle.
    Call setup(repo, config) once after profile loads.
    """

    def __init__(self, mw) -> None:
        self._mw = mw
        self._hud: ContextHUD | None = None
        self._repo: CRMRepository | None = None
        self._shortcut: QShortcut | None = None

    def setup(self, repo: CRMRepository, hud_height: int = 48, link_shortcut: str = "Ctrl+L") -> None:
        from aqt import gui_hooks
        self._repo = repo
        self._hud = ContextHUD(max_height=hud_height)
        self._inject_hud_into_reviewer()

        gui_hooks.reviewer_did_show_question.append(self._on_show_question)
        gui_hooks.reviewer_did_show_answer.append(self._on_show_answer)
        gui_hooks.reviewer_will_end.append(self._on_reviewer_end)

        self._shortcut = QShortcut(QKeySequence(link_shortcut), self._mw)
        self._shortcut.setEnabled(False)  # only active during review
        self._shortcut.activated.connect(self._open_link_editor)

    def _inject_hud_into_reviewer(self) -> None:
        """Insert HUD below the reviewer web view. Robust across Anki versions."""
        try:
            reviewer_widget = self._mw.reviewer.web.parentWidget()
            layout = reviewer_widget.layout()
            if isinstance(layout, QVBoxLayout):
                layout.addWidget(self._hud)
                return
        except Exception:
            pass
        # Fallback: dock below centralWidget
        try:
            central = self._mw.centralWidget()
            layout = central.layout()
            if layout is None:
                from PyQt6.QtWidgets import QVBoxLayout as _QVBoxLayout
                layout = _QVBoxLayout(central)
            if isinstance(layout, QVBoxLayout):
                layout.addWidget(self._hud)
        except Exception:
            # If all else fails, show as a floating child of mw
            self._hud.setParent(self._mw)
            self._hud.show()

    def _on_show_question(self, card) -> None:
        if self._repo is None or self._hud is None:
            return
        try:
            entities = self._repo.get_links_for_card(card.id)
            self._hud.refresh(entities)
            self._hud.show()
            if self._shortcut:
                self._shortcut.setEnabled(True)
        except Exception as exc:
            # Never crash Anki's reviewer
            print(f"[Anki-CRM] HUD refresh error: {exc}")

    def _on_show_answer(self, card) -> None:
        # HUD is already visible from question; no action needed
        pass

    def _on_reviewer_end(self) -> None:
        if self._hud:
            self._hud.clear()
        if self._shortcut:
            self._shortcut.setEnabled(False)

    def _open_link_editor(self) -> None:
        if self._repo is None:
            return
        card = getattr(self._mw.reviewer, "card", None)
        if card is None:
            return
        dlg = LinkEditor(card.id, self._repo, self._mw)
        dlg.links_changed.connect(lambda: self._on_show_question(card))
        dlg.exec()
