# CineFlow Movie Theater Web App

This project now includes a complete starter web app for movie theater operations:

- Beautiful, responsive operations dashboard
- Showings, films, customer booking, and recent order views
- Create ticket orders with optional concessions
- Local SQLite database for persistent storage
- Flask backend API

## Run Locally

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the app:

```powershell
python app.py
```

4. Open:

`http://127.0.0.1:5000`

## Local Database

- The SQLite database file is created automatically at `app/movie_theater.db`.
- The seed data follows your `cinema_up.sql` model (customers, films, showings, theatres, concessions, orders, tickets).

## Deploy on Vercel

This repo is configured for Vercel with:

- `api/index.py` as the serverless entrypoint
- `vercel.json` routing all requests to Flask

### Steps

1. Push this project to GitHub.
2. In Vercel, import the GitHub repository.
3. Keep default build settings and deploy.

### Important note about database on Vercel

The app uses SQLite. On Vercel, SQLite runs in an ephemeral serverless filesystem (`/tmp`) and does not persist long-term across cold starts.

For production persistent data, use a hosted database (Neon Postgres, Supabase, PlanetScale, etc.) and switch the Flask DB layer accordingly.
