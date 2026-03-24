from __future__ import annotations

_injector = None  # module-level singleton to prevent GC


def init_addon() -> None:
    """Called when Anki imports this package."""
    from aqt import gui_hooks
    gui_hooks.profile_did_open.append(_on_profile_open)


def _on_profile_open() -> None:
    global _injector
    try:
        from aqt import mw
        from aqt.qt import QAction
        from .db.schema import ensure_schema, AnkiDBAdapter
        from .db.repository import CRMRepository
        from .ui.injector import HUDInjector
        from .ui.entity_manager import EntityManager

        # Read user config (Anki provides mw.addonManager.getConfig)
        config = mw.addonManager.getConfig("anki_crm") or {}
        hud_height = int(config.get("hud_height", 48))
        link_shortcut = str(config.get("link_shortcut", "Ctrl+L"))

        # Wrap Anki's DB in our adapter (NO private API access)
        db = AnkiDBAdapter(mw.col.db)

        # Idempotent schema init
        ensure_schema(db)

        # Wire up
        repo = CRMRepository(db)
        _injector = HUDInjector(mw)
        _injector.setup(repo, hud_height=hud_height, link_shortcut=link_shortcut)

        # Tools menu entry
        action = QAction("CRM Entity Manager...", mw)
        action.triggered.connect(lambda: EntityManager(repo, mw).exec())
        mw.form.menuTools.addAction(action)

    except Exception as exc:
        # Never prevent Anki from loading
        print(f"[Anki-CRM] Failed to initialize: {exc}")
        import traceback
        traceback.print_exc()


try:
    init_addon()
except ImportError:
    pass  # aqt not available outside Anki (e.g., tests)
