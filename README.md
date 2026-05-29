# 🌬️ India AQI Intelligence Platform

A production-ready, zero-cost, full-stack air quality intelligence platform for India.

**Live AQI · 72-hour Forecasts · Gemini AI Chatbot · Health Risk Analyzer · Air Purifier Recommender**

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Frontend    | React + Vite + Tailwind CSS       |
| Backend     | Flask + APScheduler               |
| Database    | Supabase (PostgreSQL)             |
| ML          | Prophet (72h AQI forecasting)     |
| AI Chatbot  | Google Gemini 1.5 Flash           |
| Maps        | Leaflet + React-Leaflet           |
| Deployment  | Render (backend) + Vercel (frontend) |

---

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/your-username/india-aqi.git
cd india-aqi
```

### 2. Supabase setup

1. Create a project at [supabase.com](https://supabase.com)
2. Open **SQL Editor** and run `data/schema.sql`
3. Copy your **Project URL** and **service role key**

### 3. Backend

```bash
cd backend
cp .env.example .env
# Fill in your keys in .env

pip install -r requirements.txt
python app.py
```

### 4. Frontend

```bash
cd frontend
cp .env.example .env
# Set VITE_API_BASE_URL=http://localhost:5000

npm install
npm run dev
```

---

## API Keys Required

| Service  | Where to get                         | Env var            |
|----------|--------------------------------------|--------------------|
| WAQI     | https://aqicn.org/api/              | `WAQI_API_TOKEN`   |
| Gemini   | https://aistudio.google.com/        | `GEMINI_API_KEY`   |
| Supabase | Project settings → API              | `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` |

---

## Deployment

### Backend → Render.com

1. Push to GitHub
2. New Web Service → connect repo → root: `backend/`
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app --workers 2 --timeout 120`
5. Add environment variables from `.env`

### Frontend → Vercel

1. Import GitHub repo
2. Framework: **Vite**
3. Root: `frontend/`
4. Add `VITE_API_BASE_URL=https://your-backend.onrender.com`

### Keep Render alive (free tier)

Add a cron job at [cron-job.org](https://cron-job.org) to ping `https://your-backend.onrender.com/ping` every 14 minutes.

---

## Project Structure

```
india-aqi/
├── backend/
│   ├── app.py               # Flask entry point
│   ├── db.py                # Supabase singleton
│   ├── scheduler.py         # APScheduler (15-min pipeline)
│   ├── routes/
│   │   ├── aqi_routes.py
│   │   ├── forecast_routes.py
│   │   ├── chatbot_routes.py
│   │   ├── health_routes.py
│   │   ├── device_routes.py
│   │   └── state_routes.py
│   ├── services/
│   │   ├── pipeline.py      # WAQI → OpenAQ → Meteo → Supabase
│   │   ├── forecast.py      # Prophet training + inference
│   │   ├── chatbot.py       # Gemini integration
│   │   ├── anomaly.py       # Spike/surge detection
│   │   ├── risk_analyzer.py # Personalised health risk
│   │   └── devices.py       # Air purifier recommender
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── HomePage.jsx     # Leaflet map + alerts
│       │   ├── CityPage.jsx     # History + forecast charts
│       │   ├── HealthPage.jsx   # Risk analyzer
│       │   ├── ChatbotPage.jsx  # Gemini chatbot
│       │   ├── DevicesPage.jsx  # Purifier recommender
│       │   └── StatesPage.jsx   # State rankings
│       ├── components/
│       ├── api/index.js
│       └── utils/aqi.js
├── ml/
│   └── train_all.py         # Bulk model training
└── data/
    └── schema.sql           # Supabase schema
```

---

## Features

- ⚡ **Live AQI** updates every 15 minutes for 40 Indian cities
- 🗺️ **Interactive Leaflet map** with AQI colour markers
- 📈 **72-hour Prophet forecasts** with confidence intervals
- 🤖 **Gemini AI chatbot** with live AQI context injection
- 💊 **Health risk analyzer** personalised by age, conditions, activity
- 🌬️ **Air purifier recommender** matched by room size, AQI, budget
- 🇮🇳 **State-level dashboard** with AQI rankings
- 🚨 **Anomaly alerts** for pollution spikes and surges
- 🆓 **100% free tier** (Supabase free · Render free · Vercel free)

---

## License

MIT
