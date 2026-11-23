# Runback backend

## Local Docker stack

```sh
docker compose -f backend/docker-compose.yml up --build
```

The API is available at `http://localhost:8000/api/v1/health/live`.

## Supabase

Copy `backend/.env.supabase.example` to `backend/.env` and replace `[YOUR-DATABASE-PASSWORD]` with the percent-encoded database password stored in Supabase. The file is ignored by Git. Run Docker Compose from `backend/` so it loads the local `.env` file:

```sh
cd backend
docker compose up --build
```

The session-pooler URL uses SSL and works from IPv4-only Docker networks. The local PostgreSQL service still starts for development, but the API and worker use Supabase when `RUNBACK_DATABASE_URL` is set.
