# Smarix

Smarix is an internal RAG (Retrieval-Augmented Generation) assistant and onboarding/offboarding management system. It combines a FastAPI backend, a Next.js frontend, and optional Docker orchestration to collect repository data, process it, build embeddings, and provide manager/admin workflows for onboarding and offboarding employees.

## Features
- Manager and Admin dashboards for onboarding/offboarding
- Data collection from GitHub and other sources
- Processing, chunking and embedding generation
- Vector DB indexes for retrieval-based QA
- Lightweight auth and per-user project schemas

## Repository Layout (top-level)
- `backend/` — FastAPI backend, auth, data processing, and scripts
- `frontend/chatBot/` — Next.js frontend (React) for dashboards and user flows
- `data/` — local data store used in development (e.g. `Admin/users.json`)
- `Dockerfile.*`, `docker-compose.yml` — container definitions

## Prerequisites
- Node.js (recommended v18+)
- Python 3.10+ and virtualenv
- PostgreSQL (if using `MEMORY_DB_URL` PostgreSQL mode)
- Docker & Docker Compose (optional, for full stack)

## Environment variables
Create a `.env` file in the project root or set environment variables before running.
- `MEMORY_DB_URL` — PostgreSQL connection string (e.g. `postgresql://user:pass@host:5432/dbname`). If not set, the app can fall back to SQLite for local dev.
- `NEXT_PUBLIC_API_URL` — Frontend API base (e.g. `http://localhost:8000`)
- `OPENAI_API_KEY` — (optional) API key for LLM providers if used
- Other keys used by pipeline scripts: check `backend/` for required env vars

## Quickstart — Local (development)
1. Create and activate Python venv

```bash
python -m venv venv
source venv/bin/activate
# (Windows) venv\Scripts\activate
```

2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

3. Install frontend dependencies and run Next.js

```bash
cd frontend/chatBot
npm install
npm run dev
```

4. Run backend

```bash
cd /path/to/smarix/backend
# ensure environment variables are set (e.g. MEMORY_DB_URL)
uvicorn routes.api.chatbot_api:app --reload --host 0.0.0.0 --port 8000
```

5. Open the frontend at `http://localhost:3000` and the API at `http://localhost:8000`.

## Database initialization
- SQL schema and initial seed data are in `backend/scripts/init_db.sql`.
- If you use PostgreSQL, ensure `MEMORY_DB_URL` points to your DB and run the SQL script (or re-run docker-compose so init scripts apply).

Example (psql):

```bash
psql "$MEMORY_DB_URL" -f backend/scripts/init_db.sql
```

## Docker (optional)
To run everything with Docker Compose (recommended for parity with production):

```bash
docker compose up --build
# To stop:
docker compose down
```

## Data files
- `backend/data/Admin/users.json` — development users list used by some frontend endpoints (`/api/users`).
Note: production flows use PostgreSQL via `/auth/users`; keep `users.json` and DB in sync for consistent behavior.

## Running pipeline tasks
- There are helper scripts in `backend/scripts/` and top-level scripts for data collection and embedding generation. Example:

```bash
python backend/scripts/generateOffboardingData.py
python backend/core/DataProcessing/generate_embeddings.py --batch
```

Read individual script headers for required env vars and usage.

## Development tips
- If managers report missing employees in their dashboard, verify that the users exist in the database (`/auth/users`) and that each employee has the `managers` array containing the manager's `employee_id`.
- The frontend `UnifiedDashboard` expects `employee_id` and `status` fields to be present in the `/auth/users` payload.

## Contributing
- Fork the repo, create a feature branch, and open a PR with a description of your changes.

---
## Maintainers

| Name           | Contact                                                                                         |
| -------------- | ----------------------------------------------------------------------------------------------- |
| Shlok Upadhyay | linkedin.com/in/shlok-upadhyay-521065104                                                        |
| Vishal Keshari | [kesharivishal611@gmail.com](mailto:kesharivishal611@gmail.com) | linkedin.com/in/kesharivishal |

For questions, suggestions, or collaboration opportunities, please contact the maintainers.


