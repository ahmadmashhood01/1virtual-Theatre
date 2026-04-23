# CineFlow Movie Theater Web App

Flask + SQLite application for movie theater operations aligned with the final database model in `cinema_final.sql` (SQL Server reference script). The app uses a **translated SQLite schema** and the same sample data (Section 3) as that script.

## Features

- **Multi-page UI**: Dashboard, New order, Customers, Data explorer (shared navigation in `app/templates/base.html`).
- **Point of sale**: Book showings, optional concessions, automatic seat updates.
- **Pricing**: 8% tax on pre-discount subtotal; **rewards members** get **10% off** the pre-tax subtotal on new app orders (stored in `orders.discount`).
- **Receipts**: After checkout, the browser opens a printable receipt (`/receipt/<order_number>`).
- **Quick add customer**: Name, email, rewards flag — creates the next `C0XX` id.
- **Management data**: API exposes full table views and aggregates (top films, concession units).

## SQL scripts

- **`cinema_final.sql`**: Authoritative **SQL Server** script (UP/DOWN, final `orders` with subtotal/tax/discount/total, no concession stock, `shift_department_id` NOT NULL, `home_city` on customers). Use for class submission in SSMS.
- **`app/movie_theater.db`**: **SQLite** database created at runtime with equivalent structure and seed (see `seed_data.py` + `init_db()` in `app.py`).

## Run locally

1. Create and activate a virtual environment (optional).

2. Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

3. Start the app:

```powershell
py app.py
```

4. Open `http://127.0.0.1:5000`

On first run with **schema version 2**, the app may reset an older SQLite file and reseed from `cinema_final` data. To force a clean database, delete `app/movie_theater.db` and restart.

## Deploy on Vercel

- `api/index.py` is the serverless entrypoint; `vercel.json` routes traffic to Flask.
- SQLite on Vercel uses `/tmp` and is **ephemeral**; cold starts re-run `init_db()` and reseed. For production persistence, use a hosted database.
