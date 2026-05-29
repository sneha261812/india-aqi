# 🚀 Deployment Runbook — sneha261812/india-aqi

## Your Keys (already written into .env files)
- Supabase: duogtsfvbceggnncbgnm.supabase.co ✅
- WAQI: YOUR_WAQI_API_TOKEN ✅
- Gemini: YOUR_GEMINI_API_KEY ✅

---

## STEP 1 — Supabase Schema (do this FIRST)
1. Go to https://supabase.com/dashboard/project/duogtsfvbceggnncbgnm/sql/new
2. Paste the contents of data/schema.sql
3. Click Run → you should see: Schema installed successfully ✅

---

## STEP 2 — Push to GitHub

Run these commands from inside the unzipped india-aqi/ folder:

```bash
git init
git add .
git commit -m "Initial commit — India AQI Intelligence Platform"
git branch -M main
git remote add origin https://github.com/sneha261812/india-aqi.git
git push -u origin main
```

First go create the repo at:
https://github.com/new
- Repository name: india-aqi
- Visibility: Public (needed for free Render deploy)
- DO NOT initialise with README

---

## STEP 3 — Deploy Backend to Render

1. Go to https://render.com → New → Web Service
2. Connect GitHub → select sneha261812/india-aqi
3. Settings:
   - Root Directory:   backend
   - Build Command:    pip install -r requirements.txt
   - Start Command:    gunicorn app:app --workers 2 --timeout 120

4. Add these Environment Variables one by one:

   SUPABASE_URL         = https://duogtsfvbceggnncbgnm.supabase.co
   SUPABASE_SERVICE_KEY = YOUR_SUPABASE_SERVICE_KEY
   SUPABASE_ANON_KEY    = YOUR_SUPABASE_SERVICE_KEY
   WAQI_API_TOKEN       = YOUR_WAQI_API_TOKEN
   GEMINI_API_KEY       = YOUR_GEMINI_API_KEY
   FLASK_ENV            = production
   SECRET_KEY           = india-aqi-sneha-prod-2024-xK9mP2qR
   FRONTEND_URL         = https://india-aqi.vercel.app

5. Click Create Web Service — wait ~3 min
6. Your backend URL will be: https://india-aqi-backend.onrender.com
   (copy the exact URL Render gives you — it may differ slightly)

7. Test it: https://india-aqi-backend.onrender.com/ping
   Should return: {"status":"ok","service":"india-aqi-backend"}

---

## STEP 4 — Deploy Frontend to Vercel

1. Go to https://vercel.com → Add New → Project
2. Import sneha261812/india-aqi from GitHub
3. Settings:
   - Framework Preset: Vite
   - Root Directory:   frontend
4. Add Environment Variable:
   VITE_API_BASE_URL = https://india-aqi-backend.onrender.com
   (use your actual Render URL from Step 3)

5. Click Deploy — wait ~1 min
6. Your app will be live at: https://india-aqi.vercel.app

---

## STEP 5 — Keep Render Alive (free tier anti-sleep)

1. Go to https://cron-job.org → Register (free)
2. New Cron Job:
   - URL:      https://india-aqi-backend.onrender.com/ping
   - Schedule: Every 14 minutes
3. Save → Enable

---

## STEP 6 — Train ML Models (optional, do after 24h of data)

SSH into Render shell OR run locally with your .env:
```bash
cd backend
python ../ml/train_all.py
```

---

## STEP 7 — Rotate Your Keys (important!)
Since these keys were shared in a chat, regenerate them:
- Supabase: Settings → API → Regenerate service_role key
- WAQI:     https://aqicn.org/api/ → request new token
- Gemini:   https://aistudio.google.com/app/apikey → delete + new key

Then update Render environment variables with new values.
