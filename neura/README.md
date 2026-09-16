# NEURA — Adaptive Focus Intelligence

A unified login + adaptive mood-based dashboard for students and professionals.

## What changed
- Neura login/landing and the MoodStudy Planner are merged into one product.
- The supplied hero video and hero background image are used as layered visual media.
- Removed SQLite completely.
- Authentication is designed for Supabase Auth.
- Mood signals, tasks and focus sessions are designed for Supabase Postgres with Row Level Security.
- Added an adaptive plan engine, mood memory, focus lab, cloud task storage, insights view and Neura Copilot chatbot.
- AI provider URL/key/model are placeholders in `.env.example` and are never hard-coded into the frontend.

## Setup
1. Create a Supabase project.
2. Open Supabase SQL Editor and run `supabase_schema.sql`.
3. Copy `.env.example` to `.env` and fill in `SUPABASE_URL`, `SUPABASE_ANON_KEY` and `NEURA_SECRET_KEY`.
4. Optional: add an OpenAI-compatible endpoint, API key and model for the chatbot.
5. Install dependencies: `pip install -r requirements.txt`
6. Run: `python app.py`
7. Open `http://localhost:5000`.

### Supabase Auth
Enable email/password authentication in Supabase Auth. If email confirmation is enabled, a new user may need to verify email before signing in.

### AI security
Keep AI API keys server-side in `.env`. Do not put secret AI keys into HTML or JavaScript. The browser only calls `/api/chat`.

## Deployment
This Flask app can be deployed to Render, Railway, Fly.io or another Python host. Set the same environment variables in the host dashboard and use the provided `PORT` value.

## Product direction
The differentiator is **adaptive capacity planning**: mood/energy is treated as a planning signal, not merely a mood tracker. The future version can add a personal Focus Twin, calendar/deadline context, workload prediction, recovery recommendations, privacy controls and richer longitudinal analytics.
