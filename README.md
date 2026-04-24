# 🔐 Dynamic Auth Framework (DAF)

> **A next-generation authentication infrastructure built on the Dynamic Password Protocol (DPP)**
>
> *Based on peer-reviewed research — H. Channabasava & S. Kanthimathi, CompCom 2019, Springer Nature*

#####  Official Website - **https://dynamic-app-framework.streamlit.app/**
---

## What is DAF?

The **Dynamic Auth Framework** evolves a published research concept into a modern, production-ready authentication system. Traditional passwords are static — once stolen, they remain valid forever. DAF changes this fundamentally.

A DAF password has two parts:

| Part | Description | Example |
|------|-------------|---------|
| 🟢 **Static** | Characters you remember | `Botnet` |
| 🔴 **Dynamic** | Filled by live UTC time at login | `2130` (at 21:30 UTC) |

**Registration password:** `Botxxnetxx` *(x marks dynamic positions)*
**Login at 21:30 UTC:** `Bot21net30`
**Login at 21:31 UTC:** `Bot21net31` ← previous password already invalid

> A stolen password is **useless within 60 seconds.**

---

## Architecture

```
┌─────────────────────────────────────┐
│         Streamlit Demo UI           │  ← Stakeholder-facing interface
│         localhost:8501              │
└────────────────┬────────────────────┘
                 │ HTTP
┌────────────────▼────────────────────┐
│         FastAPI REST API            │  ← Clean async API layer
│         localhost:8000              │
│   POST /v1/auth/register            │
│   POST /v1/auth/authenticate        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│         DPP Core Engine             │  ← Pure Python, zero dependencies
│         dpp_core.py                 │
│   • Parameter map construction      │
│   • Argon2id hashing                │
│   • Two-stage authentication        │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│      Service & Repository Layer     │  ← Clean architecture pattern
│      implementations.py             │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│         PostgreSQL (Docker)         │  ← Persistent storage
│         daf_users table             │
│   • Argon2id hash                   │
│   • Binary parameter map            │
└─────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Core Engine | Python | Original research language, clean logic |
| API | FastAPI | Modern, async, auto-documented |
| Validation | Pydantic v2 | Type-safe request/response schemas |
| Database | PostgreSQL | Async-native, scalable |
| ORM | SQLAlchemy 2.0 | Async support via asyncpg |
| Hashing | Argon2id | OWASP 2024 recommended — memory-hard |
| Demo UI | Streamlit | Rapid stakeholder-facing interface |
| Infrastructure | Docker | One-command PostgreSQL setup |

---

## Security Upgrades over Original Prototype

| Area | Original (2019) | DAF Phase 1 |
|------|----------------|-------------|
| Hash algorithm | bcrypt (cost=10) | **Argon2id** — memory-hard, OWASP 2024 |
| String comparison | Plain `==` operator | **hmac.compare_digest** — constant-time |
| Timezone | Hard-coded Asia/Kolkata | **UTC-normalised** globally |
| Error messages | Specific per failure | **Generic always** — prevents enumeration |
| Architecture | Monolithic PHP + Python | **Layered clean architecture** |
| Database driver | mysqli (synchronous) | **asyncpg** — fully async |

---

## Project Structure

```
daf/
├── main.py              ← FastAPI entry point
├── dpp_core.py          ← DPP core engine (standalone)
├── settings.py          ← Environment configuration
├── exceptions.py        ← Domain exceptions
├── user.py              ← Domain entity + interfaces
├── database.py          ← SQLAlchemy + ORM model
├── implementations.py   ← Repository + Service (concrete)
├── routes.py            ← API endpoints + Pydantic schemas
├── streamlit_app.py     ← Stakeholder demo UI
└── requirements.txt     ← All dependencies
```

---

## Quick Start

### Prerequisites
- Python 3.12+
- Docker

### 1. Clone the repo

```bash
git clone https://github.com/channachannu/dynamic-auth-framework.git
cd dynamic-auth-framework
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL

```bash
docker run --name daf-db \
  -e POSTGRES_USER=daf_user \
  -e POSTGRES_PASSWORD=daf_secure \
  -e POSTGRES_DB=daf \
  -p 5432:5432 \
  -d postgres:16
```

### 4. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://daf_user:daf_secure@localhost:5432/daf
APP_ENV=development
APP_NAME=Dynamic Auth Framework
VERSION=1.0.0
DEFAULT_PLACEHOLDER=x
```

### 5. Start the API

```bash
uvicorn main:app --reload
```

API live at: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

### 6. Start the Streamlit demo

```bash
streamlit run streamlit_app.py
```

Demo live at: **http://localhost:8501**

---

## API Reference

### Register

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "Botnet", "password": "Botxxnetxx", "placeholder": "x"}'
```

**Response:**
```json
{
  "message": "Registration successful.",
  "username": "Botnet",
  "parameter_map": "0001100011"
}
```

### Authenticate (at 21:30 UTC)

```bash
curl -X POST http://localhost:8000/v1/auth/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username": "Botnet", "password": "Bot21net30"}'
```

**Response:**
```json
{
  "success": true,
  "username": "Botnet",
  "message": "Authentication successful."
}
```

---

## How Authentication Works

```
Login input:    B  o  t  2  1  n  e  t  3  0
Parameter map:  0  0  0  1  1  0  0  0  1  1

Stage 1 — Dynamic:  positions [1] → "2130" == current UTC time ✅
Stage 2 — Static:   positions [0] → "Botnet" == Argon2id hash  ✅

Both stages must pass. Generic error always returned on failure.
```

---

## Attack Resistance

| Attack | Defence |
|--------|---------|
| Replay attack | Password changes every 60 seconds |
| Brute force | Argon2id — 64MB RAM per attempt, GPU cracking infeasible |
| Phishing | Stolen password is immediately stale |
| Database breach | Only hash + parameter map stored — raw password irrecoverable |
| Timing attack | `hmac.compare_digest` — constant-time comparison |
| Enumeration | All failures return identical generic message |

---

## Roadmap

### ✅ Phase 1 — Foundation (Complete)
- Core DPP logic modernised in Python
- FastAPI REST API
- PostgreSQL persistence
- Streamlit stakeholder demo

### 🔄 Phase 2 — Intelligence Layer (Upcoming)
- Event-driven trust scoring
- Behavioral signal collection
- Redis for real-time token management
- SDK for easy third-party integration

### 🔮 Phase 3 — Agentic Layer (Planned)
- AI agent identity and authority
- Three-tier trust chain: Human → Platform → Agent
- Dynamic trust tokens
- Agent behavioral integrity monitoring

---

## Research Foundation

This project is built on published academic research:

> **"Dynamic Password Protocol for User Authentication"**
> H. Channabasava & S. Kanthimathi
> PES Institute of Technology, Bangalore
> *Computational Intelligence and Communication Networks (CompCom) 2019*
> *Springer Nature — AISC 998, pp. 597–611*
> DOI: [10.1007/978-3-030-22868-2_43](https://doi.org/10.1007/978-3-030-22868-2_43)

---

## Author

**H. Channabasava**
- Research: CompCom 2019, Springer Nature
- GitHub: [@channachannu](https://github.com/channachannu)

---

*Dynamic Auth Framework — Building trust infrastructure for the agentic era.*
