# B2B SaaS Backend API (Work in Progress)

A scalable, modern backend architecture for a B2B SaaS application. Built with FastAPI, SQLAlchemy 2.0, PostgreSQL, and Docker.

## 🚀 Tech Stack
- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL with SQLAlchemy 2.0 ORM
- **Migrations:** Alembic
- **Infrastructure:** Docker & Docker Compose
- **Validation:** Pydantic

## ⚙️ Core Features
- **Structured API Routing:** Versioned API endpoints (`api/v1/`).
- **Role-Based Access Control (RBAC):** Built-in models for `OWNER`, `ADMIN`, and `MEMBER` roles.
- **Database Models:** Advanced SQLAlchemy 2.0 mappings utilizing `UUID` and `JSONB`.
- **Environment Configuration:** Centralized settings management via `core/` modules.
- **Containerized DB:** Ready-to-use PostgreSQL environment via `docker-compose.yml`.

## 🚧 Roadmap / To-Do
- [ ] Complete JWT-based Authentication flow (`auth.py`).
- [ ] Implement Celery/Redis for background task execution.
- [ ] Add Pytest coverage for core API routes.

## 🛠️ Local Setup
1. Clone the repository: `git clone https://github.com/HazardKill/fastapi-b2b-saas-core.git`
2. Set up virtual environment: `python -m venv .venv`
3. Activate & install dependencies: `pip install -r requirements.txt`
4. Spin up DB: `docker-compose up -d`
5. Run migrations: `alembic upgrade head`
6. Start server: `uvicorn main:app --reload`
