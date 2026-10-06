# Kisan Budget Manager - Phase 1 (backend)
    cp .env.example .env
    docker compose up --build -d
    docker compose exec api python -m app.seed     # demo user ramesh@example.com / ramesh123
API docs: http://localhost:8000/docs  (login via POST /api/auth/login, then Authorize with the token)

Local without Docker: `cd backend && pip install -r requirements.txt`, set DATABASE_URL to a local Postgres, run `uvicorn app.main:app --reload`.
Note: farm sales are counted from Farm Income; Household Income rows with source "farming" are excluded from totals to avoid double counting.
