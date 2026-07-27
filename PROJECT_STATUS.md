# ArecaAgent — Comprehensive Project Status & Roadmap

This document outlines the current progress, completed architectural components, and the pending features/modules remaining to be implemented in the **ArecaAgent** project.

---

## 🏗 System Architecture Overview

ArecaAgent is structured as a FastAPI monorepo utilizing a **single PostgreSQL database with 5 logical schemas** (`core`, `agronomy`, `env`, `market`, `logs`).

```
areca-agent/
├── backend/
│   ├── main.py                  # FastAPI monorepo entrypoint
│   ├── config.py                # Pydantic environment configuration
│   ├── auth/                    # JWT Authentication service & router
│   ├── core/                    # Farmer profile, farm, crop block, & activity CRUD APIs
│   ├── db/                      # SQLAlchemy 2.0 ORM models (5 schemas)
│   ├── schemas/                 # Pydantic request/response DTOs
│   ├── agents/                  # 8 specialized AI agent modules & routers
│   └── scripts/                 # Database seed & utility scripts
├── infra/                       # PostgreSQL schema initialization SQL
├── docs/                        # Architecture & schema documentation
└── docker-compose.yml           # Container orchestration
```

---

## ✅ Part 1: Completed Implementation (Things Done)

### 1. Repository & Infrastructure Setup
- [x] **Git Repository & Remote**: Initialized Git repository and pushed structural skeleton to GitHub (`https://github.com/Sathwik-Hebbar/Areca-Agent.git`).
- [x] **Python Environment**: Set up `backend/venv` with pinned dependencies in `requirements.txt` (`FastAPI`, `SQLAlchemy 2.0`, `Pydantic v2`, `psycopg2-binary`, `PyJWT`, `passlib`, `scikit-learn`, `pandas`, `google-generativeai`).
- [x] **Docker Integration**: Configured `docker-compose.yml` for PostgreSQL 16 and backend containerization.
- [x] **Database Initialization**: Created `infra/postgres_init.sql` script to set up logical schemas (`core`, `agronomy`, `env`, `market`, `logs`) and UUID extension.
- [x] **Configuration & Docs**: Created `.env.example`, `.gitignore`, `README.md`, and `docs/db_schema.md`.

### 2. Database Models (SQLAlchemy 2.0 ORM across 5 Schemas)
- [x] **`core` Schema**:
  - `User`: Credentials, bcrypt password hashing, roles (`farmer`, `admin`).
  - `FarmerProfile`: Name, village, taluk, district, state, pincode, language, preferred mandi.
  - `Farm`: Land plot metadata, GPS coordinates (lat/lon), acreage, soil type, irrigation method.
  - `CropBlock`: Perennial planting batch tracking with **derived tree age property** (`age_years = now() - planting_date`), variety, tree count, spacing.
  - `IoTDevice`: ESP32 device registration and auth tokens.
- [x] **`agronomy` Schema**:
  - `FarmActivity`: Timeline of farming activities (fertilizer, spray, harvest, pruning, soil test) with typed columns and JSONB details.
  - `DiseaseDetection`: Computer vision CNN output & Bayesian diagnostic posterior values per crop block.
- [x] **`env` Schema**:
  - `WeatherReading`: Temperature, humidity, rainfall, weather source (API vs forecast).
  - `SoilSensorReading`: Telemetry data from ESP32 soil moisture sensors.
- [x] **`market` Schema**:
  - `MarketPrice`: Mandi price history per kg for Arecanut varieties.
- [x] **`logs` Schema**:
  - `Advisory`: Generated advice with priority matrix, fallback flags, and `input_snapshot` JSON (used for Gemini caching and RL agent training).
  - `Feedback`: Farmer ratings (1–5 scale) and notes feeding Q-learning updates.
  - `Notification`: Queue for SMS, Push, and In-App delivery.
  - `SystemLog`: Service audit logs.

### 3. Pydantic Schemas & Data Transfer Objects (`backend/schemas/`)
- [x] Full request/response DTO validation for Auth, Farmer Profile, Farm, CropBlock, FarmActivity, DiseaseDetection, WeatherReading, MarketPrice, Advisory, and Feedback.

### 4. Auth & Core CRUD Services (`backend/auth/` & `backend/core/`)
- [x] **Authentication Service**: JWT Bearer token generation, verification middleware, password hashing (`/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`).
- [x] **Core Management API**: Endpoints for farmer profile updates, farm creation/listing, crop block creation/listing, and activity logging (`/api/v1/core/`).

### 5. Multi-Agent Router Endpoints (`backend/agents/`)
- [x] **Vision Agent** (`/api/v1/agents/vision/detect`): Image upload and disease prediction interface.
- [x] **Diagnosis Agent** (`/api/v1/agents/diagnosis/validate/{id}`): Bayesian probability update endpoint.
- [x] **Weather Agent** (`/api/v1/agents/weather/current/{id}`): Farm microclimate readings API.
- [x] **Market Agent** (`/api/v1/agents/market/prices`): Mandi price data feed API.
- [x] **Advisory Agent** (`/api/v1/agents/advisory/generate`): Prompt context builder and advisory persistence.
- [x] **Coordinator Agent** (`/api/v1/agents/coordinator/synthesize`): Weighted decision synthesis engine (35% Vision, 30% Diagnosis, 20% Weather, 15% Market).
- [x] **Learning Agent** (`/api/v1/agents/learning/feedback`): Farmer feedback ingestion and Q-learning update stub.
- [x] **Notifying Agent** (`/api/v1/agents/notifying/send`): Notification dispatch queue API.

### 6. Database Seeding Script (`backend/scripts/seed_db.py`)
- [x] Seeder script for bootstrapping sample farmer profile (*Ramesh Gowda*), farms, crop blocks, activity logs, weather data, and market prices.

---

## 📌 Part 2: Pending Implementation (Things Yet to be Done)

### 🧠 1. Machine Learning Models & Deep Intelligence Integrations
- [ ] **Vision Agent (`backend/agents/vision/`)**:
  - Integrate trained CNN model weights (`weights/best_model.pth`) for Arecanut leaf/fruit rot detection (Koleroga, Yellow Leaf Disease, Anabe Roga).
  - Add image preprocessing pipeline (`preprocess.py`).
- [ ] **Diagnosis Agent (`backend/agents/diagnosis/`)**:
  - Build complete Conditional Probability Tables (CPTs) for the Bayesian Belief Network in `bayesian.py`.
- [ ] **Weather Agent (`backend/agents/weather/`)**:
  - Implement 7-day ARIMA / Prophet rainfall and humidity forecasting models (`arima_model.py`).
  - Wire live OpenWeather / Tomorrow.io API client (`api_client.py`).
- [ ] **Market Agent (`backend/agents/market/`)**:
  - Build and train LSTM neural network for Arecanut price forecasting (`lstm_model.py`).
  - Integrate live Data.gov.in Mandi API connector (`data_gov_client.py`).
- [ ] **Advisory Agent (`backend/agents/advisory/`)**:
  - Deep integration with `google-generativeai` SDK for Gemini 1.5 Flash/Pro LLM advisory generation (`gemini_client.py`).
  - Implement rule-based fallback system (`rule_based_fallback.py`).
  - Implement prompt snapshot caching mechanism (`cache.py`).
- [ ] **Learning Agent (`backend/agents/learning/`)**:
  - Implement Q-learning table update algorithm to tune prompt strategies based on farmer ratings (`q_learning.py`).

### 💻 2. Frontend Web Dashboard (`frontend-web/`)
- [ ] Initialize Vite + React web application.
- [ ] Implement API client services for Auth, Farmer Profile, Crop Blocks, Activities, Disease Detection, Weather, Market, and Advisories.
- [ ] Build pages:
  - **Login / Register**: Authentication flow.
  - **Dashboard**: High-level farm overview & urgent alerts.
  - **Farmer Profile & Land Manager**: Crop block creation, variety tracking, tree age computation.
  - **Activity Timeline**: Interactive timeline of fertilizer/spray/harvest history.
  - **Disease Scanner**: Upload image & view CNN + Bayesian diagnostic results.
  - **Weather & Market Insights**: Real-time charts and forecasts.
  - **Advisory Hub**: Gemini-generated advice & rating feedback widget.

### 📱 3. Mobile Application (`mobile-app/`)
- [ ] Setup Flutter / React Native mobile project.
- [ ] Implement camera capture for instant disease detection.
- [ ] Implement offline-first activity logging and local storage.
- [ ] Push notification listener for urgent farm alerts.

### 🔌 4. Hardware / Firmware (`firmware/`)
- [ ] PlatformIO C++ setup for ESP32 microcontroller.
- [ ] ADC reader module for capacitive soil moisture sensors.
- [ ] MQTT / HTTP Client module (`wifi_mqtt_client.cpp`) to post telemetry data to `/api/v1/hardware/sensor-data`.

---

## 👥 Persona Ownership & Work Split

| Team Member | Domain / Focus | Key Responsibilities & Modules |
|---|---|---|
| **Person A** | Vision + Diagnosis Agents | `backend/agents/vision/`, `backend/agents/diagnosis/`, CNN weights training, Bayesian CPTs. |
| **Person B** | Weather + Market Agents | `backend/agents/weather/`, `backend/agents/market/`, ARIMA model, LSTM price forecasting, Data.gov.in integration. |
| **Person C** | Advisory + Coordinator + Gemini | `backend/agents/advisory/`, `backend/agents/coordinator/`, `backend/agents/learning/`, Gemini integration, Q-learning feedback. |
| **Person D** | Core Backend + Frontend + Mobile | `backend/core/`, `backend/auth/`, `frontend-web/`, `mobile-app/`, CRUD APIs & UI integration. |

---

## 📄 License & Maintainers
- **Repository**: [Sathwik-Hebbar/Areca-Agent](https://github.com/Sathwik-Hebbar/Areca-Agent)
- **Framework**: FastAPI (Python 3.11) + PostgreSQL 16
