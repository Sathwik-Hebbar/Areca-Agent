# ArecaAgent — AI-Driven Arecanut Farming Assistant

ArecaAgent is an end-to-end multi-agent AI system designed for Arecanut (Betelnut) farmers. It combines computer vision disease detection, Bayesian diagnostic validation, weather and market price forecasting, LLM advisory generation (powered by Google Gemini), and reinforcement learning for personalized farming guidance.

## System Architecture Overview

- **FastAPI Monorepo Backend**: Modular service-oriented backend hosting all AI agent logic and core CRUD APIs.
- **PostgreSQL Multi-Schema Database**: Single PostgreSQL instance using 5 logical schemas (`core`, `agronomy`, `env`, `market`, `logs`) to maintain clean domain boundaries while preserving foreign key integrity.
- **Frontend & Mobile**: Web dashboard and mobile application interface.
- **IoT Firmware**: ESP32 integration for live soil moisture and environmental monitoring.

## Database Schemas

- **`core`**: Users, farmer profiles, farms/plots, perennial crop blocks (variety, planting date, tree count), and registered IoT devices.
- **`agronomy`**: Farm activity history (fertilizers, sprays, irrigation, harvests) and computer vision disease detection records.
- **`env`**: Microclimate weather history and soil moisture sensor telemetry.
- **`market`**: Regional Mandi prices for Arecanut commodities.
- **`logs`**: Advisory logs, farmer RL feedback, SMS/push notification queues, and system audit logs.

## Quickstart

### Prerequisites
- Python 3.11+
- PostgreSQL 16 or Docker & Docker Compose

### 1. Environment Configuration
Copy `.env.example` to `.env` and fill in your configuration:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
```bash
docker-compose up -d --build
```
This spins up PostgreSQL on port `5432` with all schemas pre-created, along with the FastAPI backend on port `8000`.

### 3. Local Development (Without Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Interactive API documentation is available at `http://localhost:8000/docs`.

### 4. Seed Test Data
To populate sample farmers, crop blocks, and activity logs:
```bash
cd backend
python -m scripts.seed_db
```

## Project Folder Structure

```
areca-agent/
├── backend/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # Pydantic Settings
│   ├── auth/                    # JWT Authentication
│   ├── core/                    # Farmer profile, farm, crop block & activity APIs
│   ├── db/                      # SQLAlchemy models split by 5 schemas
│   ├── schemas/                 # Pydantic DTOs
│   ├── agents/                  # Vision, Diagnosis, Weather, Market, Advisory, etc.
│   └── scripts/                 # Database seed & utility scripts
├── infra/                       # PostgreSQL initialization SQL
├── docs/                        # DB schema & architecture specs
└── docker-compose.yml
```
