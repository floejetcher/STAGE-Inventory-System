# STAGE Inventory System (Streamlit)

A simple, local, Streamlit-based inventory app for the STAGE Theatre Department to track props, costumes, set pieces, lighting and sound gear across locations.

- Local app (runs on http://localhost:8501)
- SQLite database file saved locally (`stage_inventory.db`)
- Add items, edit items, filter by crew tag/location, and generate location reports

## Quick start

1. Create and activate a Python 3.10+ environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app locally:

```bash
streamlit run app.py --server.port=8501
```

4. Open your browser at: http://localhost:8501

## Folders & files

- `app.py` — Streamlit UI
- `inventory_db.py` — SQLite data layer
- `.streamlit/config.toml` — Streamlit config for local host/port
- `stage_inventory.db` — The SQLite DB (auto-created)

## Notes

- This app is designed for a single user on one machine. To share, copy the folder including the DB file.
- Back up `stage_inventory.db` periodically.
