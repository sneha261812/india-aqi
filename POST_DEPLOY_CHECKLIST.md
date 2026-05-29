# Post-Deployment Verification Checklist

## Backend Health Checks (run these in browser or curl)

### 1. Ping
GET /ping
Expected: {"status":"ok","service":"india-aqi-backend"}

### 2. All cities AQI (first data arrives after 15min scheduler tick)
GET /api/aqi/all
Expected: JSON array of city objects

### 3. Single city
GET /api/aqi/current/Delhi
Expected: {"city":"Delhi","aqi":...}

### 4. Forecast (needs 48h of data to train model)
GET /api/forecast/Delhi
Expected: {"city":"Delhi","forecast":[...72 items...]}

### 5. States
GET /api/states/
Expected: Array of state AQI objects

### 6. Health risk
POST /api/health/risk
Body: {"aqi":185,"age":30}
Expected: {"category":"Moderate","risk_level":"Moderate",...}

### 7. Chatbot
POST /api/chat/message
Body: {"message":"What is the AQI in Delhi today?"}
Expected: {"response":"...Gemini reply..."}

### 8. Device recommender
POST /api/devices/recommend
Body: {"room_sqft":250,"aqi":200}
Expected: {"devices":[...],"count":N}

## Common Issues & Fixes

### Scheduler not firing?
Check Render logs → "APScheduler started" should appear at boot.
First data arrives within 15 minutes of deploy.

### Supabase CORS error?
Ensure SUPABASE_SERVICE_KEY (not anon key) is set in Render env vars.

### Gemini 403?
Gemini API key may need billing enabled in Google Cloud Console.
Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com

### Frontend shows blank map?
Check browser console for CORS errors.
Ensure FRONTEND_URL in Render matches your exact Vercel URL.

### Forecast returns flat-fallback?
Normal for first 48 hours — not enough data to train model yet.
Model auto-trains once 48+ hourly readings exist for a city.
