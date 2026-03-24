# Anki-CRM: Relational Knowledge Graph

Link your Anki cards to people, projects, and other context so you remember *why* you're studying something, not just *what* it is.

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![Anki 23.10+](https://img.shields.io/badge/anki-23.10%2B-teal)
![License MIT](https://img.shields.io/badge/license-MIT-green)

---

## What it does

Anki treats every card as a standalone fact. That works fine for general vocab, but if you're studying material tied to a specific job, client, or project, the context matters. Knowing that 稟議 is the approval process used by the Tanaka Corp. procurement team makes it stick better than a plain definition.

Anki-CRM lets you define **entities** (stakeholders and projects) and link them to cards. During review, a **Context HUD** bar appears at the bottom of the reviewer showing every entity linked to the current card as color-coded chips.

Good for: Japanese business vocab, legal terms tied to specific cases, technical concepts tied to active projects, or anything where the "who" and "what" behind a card matters.

---

## Features

- **Context HUD**: a slim bar at the bottom of the reviewer showing linked entities as chips; scrolls horizontally when the list is long
- **Ctrl+L shortcut**: opens the Link Editor during a review session without leaving the reviewer; configurable to any key combo
- **Entity Manager**: full CRUD dialog under Tools > CRM Entity Manager; supports search and inline JSON metadata editing
- **Stakeholder and Project types**: each has its own accent color; two-letter badge (ST / PR) identifies the type at a glance
- **Configurable**: HUD height, position, accent colors, max chips, and link shortcut are all set in `config.json`

---

## Installation

### AnkiWeb (recommended)

Open Anki > Tools > Add-ons > Get Add-ons and enter code **992441620**.

> Requires Anki 2.1.1 or later.

### Manual

1. Close Anki.
2. Copy the `anki_crm` folder into your add-ons directory:

   **Linux / macOS**
   ```
   ~/.local/share/Anki2/addons21/anki_crm/
   ```

   **Windows**
   ```
   %APPDATA%\Anki2\addons21\anki_crm\
   ```

3. Restart Anki.

### Compatibility

| Requirement | Version |
|-------------|---------|
| Anki | 23.10+ (`min_point_version` 231000) |
| Python | 3.9+ |
| Qt binding | PyQt6 (bundled with Anki 23.x) |

No third-party Python packages needed at runtime. Uses only the standard library, Anki's built-in DB API, and PyQt6.

---

## Usage

### Creating entities

Open **Tools > CRM Entity Manager**. Pick the Stakeholders or Projects tab and click **+ Add New**. Enter a name and optionally a JSON metadata blob, then save. Names must be unique within each type.

### Linking a card during review

Press **Ctrl+L** (or your configured shortcut) while reviewing. The Link Editor opens as a modal with two panels:

- **Left panel**: entities already linked to the current card. Click "Remove Selected" to unlink.
- **Right panel**: all entities, filterable by name and type. Select one and click "Link Selected" to add it. Use the "Create & Link" form at the bottom to create a new entity and link it in one step.

The HUD updates right away after any change.

### The Context HUD

A narrow strip at the bottom of the reviewer (or top, if configured). It shows up automatically when a card is displayed and clears when the session ends.

Each chip shows:
- A two-letter type badge (e.g. **ST** for stakeholder, **PR** for project) in the entity's accent color
- The entity name in light text on a dark background

If nothing is linked, the HUD shows: *No context linked - press Ctrl+L to link this card.*

When there are more chips than fit on screen, the bar scrolls horizontally. `max_chips_displayed` sets the cap.

### Metadata field

Each entity has an optional JSON metadata field for any extra attributes. Must be valid JSON; the UI checks before saving.

Examples:

```json
{"title": "部長", "company": "Tanaka Corp", "keigo": "尊敬語"}
```

```json
{"status": "active", "deadline": "2025-Q3", "lead": "Watanabe-san"}
```

Metadata shows up in the Entity Manager table.

---

## Configuration

Edit via **Tools > Add-ons > Anki-CRM > Config**, or edit `anki_crm/config.json` directly and restart Anki.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `hud_height` | integer | `48` | HUD bar height in pixels (32-120) |
| `hud_auto_show` | boolean | `true` | Show HUD automatically when a card appears |
| `hud_position` | string | `"bottom"` | Where to dock the HUD: `"top"` or `"bottom"` |
| `link_shortcut` | string | `"Ctrl+L"` | Shortcut to open the Link Editor |
| `max_chips_displayed` | integer | `20` | Max chips shown before truncating (1-100) |
| `chip_colors` | object | see below | Background and accent color per entity type |

Default `chip_colors`:

```json
{
    "stakeholder": {"bg": "#1a1a2e", "accent": "#e94560"},
    "project":     {"bg": "#1a1a2e", "accent": "#0f3460"}
}
```

Both `bg` and `accent` must be six-digit CSS hex strings.

---

## Development

```bash
git clone https://github.com/m6lvink/Anki-CRM.git
cd Anki-CRM
pip install -r requirements.txt
pytest tests/ -v --cov=anki_crm
```

Tests use an in-memory SQLite database and don't require Anki to be installed.

---

## Project structure

```
Anki-CRM/
├── anki_crm/
│   ├── __init__.py
│   ├── manifest.json
│   ├── config.json
│   ├── config.schema.json
│   ├── models.py
│   ├── db/
│   │   ├── schema.py
│   │   └── repository.py
│   └── ui/
│       ├── context_hud.py
│       ├── link_editor.py
│       ├── entity_manager.py
│       └── injector.py
└── requirements.txt
```

---

## License

MIT. See [LICENSE](LICENSE) for the full text.
