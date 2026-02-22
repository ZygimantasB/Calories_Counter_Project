<div align="center">

# HealthTracker Pro

### Your Comprehensive Fitness & Nutrition Dashboard

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-17-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

**HealthTracker Pro** is a powerful, all-in-one web application designed to help you monitor and optimize every aspect of your health journey. Track nutrition, workouts, running sessions, weight, and body measurements with beautiful visualizations and an intuitive user interface.

[Features](#-features) · [Analytics](#-analytics-dashboard) · [Quick Start](#-quick-start) · [React SPA](#-react-spa) · [Documentation](#-documentation)

</div>

---

## Table of Contents

- [Features](#-features)
- [Analytics Dashboard](#-analytics-dashboard)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [React SPA](#-react-spa)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Documentation](#-documentation)
- [License](#-license)

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🍎 Nutrition Tracking
- **Food Diary** — Log meals with comprehensive nutritional data
- **AI Food Assistant** — Instant macro lookup powered by Google Gemini AI
- **Macronutrient Analysis** — Track calories, protein, carbohydrates, and fat
- **Quick-Add Items** — Save and reuse frequently eaten foods (ordered by frequency)
- **Hide from Quick List** — Keep your quick-add list clean
- **Copy Previous Day** — Duplicate all meals from any past date to today
- **Visual Progress Bars** — Daily calorie and macro targets at a glance
- **Date Filtering** — Browse any date's food log

</td>
<td width="50%">

### 📋 Meal Templates
- **Save Templates** — Group any set of food items into a reusable template
- **One-Click Logging** — Add an entire template to today's log instantly
- **Template Management** — Edit and delete saved templates

</td>
</tr>
<tr>
<td width="50%">

### 💪 Workout Management
- **Exercise Library** — Custom exercise database with descriptions
- **Session Recording** — Log sets, reps, and weights per exercise
- **Personal Records** — Automatic PR detection with badge highlighting
- **Session Volume Summary** — Total volume per workout session
- **Progress Tracking Card** — Table-level progress overview
- **Workout Tables** — Custom grid-based workout planners
- **Google Sheets Import** — Import workout tables directly from Sheets
- **Column Date Picker** — Set dates per column in workout tables
- **Performance Charts** — Workout frequency and exercise progress over time

</td>
<td width="50%">

### 🏃‍♂️ Running Tracker
- **Run Logging** — Record distance, duration, and notes
- **Pace Analytics** — Auto-calculated pace (min/km) and trends
- **Distance Tracking** — Weekly and monthly summaries
- **Performance Charts** — Speed and endurance visualizations

</td>
</tr>
<tr>
<td width="50%">

### ⚖️ Weight & Body Stats
- **Weight Journal** — Daily weight log with trend analysis
- **Calories vs Weight Correlation** — Chart showing how intake affects weight
- **Stability Score** — Weight volatility analysis
- **Body Measurements** — Track neck, chest, waist, hips, biceps, thighs, and more
- **Measurement Charts** — Per-measurement trend charts
- **CSV Export** — Export all body measurement data

</td>
<td width="50%">

### ⚙️ Settings & Goals
- **Profile Setup** — Age, height, weight, gender, activity level
- **Fitness Goals** — Maintain / Bulk / Cut / Ripped
- **Auto Macro Targets** — Calculated via Mifflin-St Jeor TDEE formula
- **Manual Override** — Set custom macro targets
- **Theme** — Light / Dark / System default
- **Data Export** — Full JSON export of all your data

</td>
</tr>
</table>

---

## 📊 Analytics Dashboard

The analytics section has four views accessible from the same navigation tabs.

### Overview (`/analytics/`)
- Average daily calories and macros
- Calorie and macro trend charts (30 / 90 / 180 / 365 days / all time)
- Daily consistency score and logging streak
- Best & worst day highlights
- Weight stability analysis
- **24-hour meal timing** heatmap
- Top foods table (sortable by calories, protein, fat, carbs)
- Achievement badges and nutrition grade (A–F)
- Calorie distribution breakdown
- Intelligent insights (weight correlation, protein impact, consistency patterns)

### Month Comparison (`/analytics/month-compare/`)
- Pick any two calendar months and compare side by side
- Calories, macros, consistency, and weight breakdowns
- Calorie impact percentage insights
- **Weekly calorie vs weight trend** chart
- Auto-generated observation cards

### Yearly Trends (`/analytics/trends/`)
- Month-by-month overview for any year
- Toggle charts: calories / macros / consistency / weight
- Best and worst month highlighting (colour-coded table)
- 8-week consistency mini-bars per month
- **Weight prediction** based on current calorie trend
- Summary stats: total logged days, average calories, best month

### Product Compare (`/analytics/product-compare/`) *(new)*

Compare two or three food products from your personal log history.

| Feature | Description |
|---|---|
| **Autocomplete search** | Suggestions from your logged food history as you type |
| **2 or 3 products** | Optional third product (C) for 3-way comparison |
| **Radar chart** | 5-axis Chart.js radar — Calories, Protein, Fat, Carbs, Protein Efficiency |
| **Serving size scaler** | Slider (0.25×–4×) scales all values in real time |
| **Goal alignment** | Every macro shown as % of your daily target |
| **Protein efficiency** | Grams of protein per 100 kcal |
| **Diff column** | Shows A/B winner for each nutrient (2-product mode) |
| **Winner badges** | Highlighted in breakdown table for each category |
| **Sparkline** | 8-week usage frequency bar chart per product |
| **Last logged date** | When each product was most recently eaten |
| **Recent comparisons** | Last 5 pairs saved in localStorage as clickable chips |

---

## 🛠 Tech Stack

<table>
<tr>
<td width="50%">

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.12 | Runtime |
| **Django** | 5.2 | Web framework |
| **SQLite** | — | Database |
| **Google Gemini AI** | 0.8 | Nutrition lookup |
| **python-decouple** | 3.8 | `.env` config |
| **asgiref** | 3.9 | ASGI support |

</td>
<td width="50%">

### Frontend
| Technology | Purpose |
|---|---|
| **Bootstrap 5** | Responsive UI |
| **Chart.js 4** | Django-template charts |
| **Font Awesome** | Icons |
| **React 17** | SPA frontend |
| **Vite** | React build tool |
| **Tailwind CSS v4** | React component styling |
| **Recharts** | React charts |

</td>
</tr>
</table>

---

## 🏗 Architecture

```
/              → Django template views  (Bootstrap 5 + Chart.js)
/app/*         → React SPA             (Vite + Tailwind v4 + Recharts)
/api/react/*   → JSON API for React
/api/*         → JSON API for Django-template charts
```

Both frontends share the same Django backend.
The React app builds to `static/react/` and is served via a catch-all view for `/app/*`.

### Key Files

| File | Description |
|---|---|
| `count_calories_app/views.py` | All view logic (~5 500 lines) |
| `count_calories_app/models.py` | 11 database models |
| `count_calories_app/services.py` | `GeminiService` — AI nutrition lookup |
| `count_calories_app/urls.py` | URL routing |
| `frontend/src/` | React source (Vite + Tailwind v4) |
| `frontend/vite.config.js` | Build config: output → `static/react/` |
| `frontend/src/api/client.js` | Axios instance with CSRF interceptor |

### Data Models

| Model | Description |
|---|---|
| `FoodItem` | A single logged food entry (name, calories, protein, fat, carbs, timestamp) |
| `Weight` | Daily weight log |
| `RunningSession` | A run (distance, duration, date) |
| `Exercise` | Exercise definition |
| `WorkoutSession` | A workout session |
| `WorkoutExercise` | Sets / reps / weight within a session |
| `WorkoutTable` | Custom grid-based workout planner |
| `BodyMeasurement` | Body measurement snapshot |
| `UserSettings` | Singleton (pk=1) — profile, goal, macro targets, theme |
| `MealTemplate` | A saved group of food items |
| `MealTemplateItem` | Individual item within a template |

### Macro Calculation Formula

Uses Mifflin-St Jeor TDEE with goal offsets:

| Goal | Calorie offset | Use case |
|---|---|---|
| Maintain | +0 | Stay at current weight |
| Bulk | +300 | Lean muscle gain |
| Cut | −500 | Fat loss |
| Ripped | −750 | Aggressive cut |

Protein and fat are per-kg bodyweight. Carbs fill the remaining calories.

---

## 📋 Prerequisites

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/) *(React frontend only)*
- **Git** — [Download](https://git-scm.com/downloads)

---

## ⚡ Quick Start

### 1. Clone

```bash
git clone https://github.com/ZygimantasB/Calories_Counter_Project.git
cd Calories_Counter_Project
```

### 2. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.exemple .env   # or copy on Windows
```

Edit `.env`:

```env
DJANGO_SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here   # optional — needed for AI food lookup
```

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com/app/apikey).

### 5. Database

```bash
python manage.py migrate
```

### 6. Run

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/**

---

## ⚛️ React SPA

The React app lives in `frontend/` and is served at `/app/`.

```bash
cd frontend
npm install

# Development server (HMR on :5173, proxies API to Django :8000)
npm run dev

# Production build — required after any source change
npm run build

# Tests
npm test
```

> **Important:** `/app/` always serves the last *built* output in `static/react/`.
> Changes to `frontend/src/` have no effect until `npm run build` is run.

### React Pages

| Route | Page |
|---|---|
| `/app/` | Dashboard |
| `/app/food-tracker` | Food Tracker |
| `/app/weight` | Weight Tracker |
| `/app/running` | Running Tracker |
| `/app/workout` | Workout Tracker |
| `/app/body-measurements` | Body Measurements |
| `/app/top-foods` | Top Foods |
| `/app/analytics` | Analytics |
| `/app/settings` | Settings |

---

## ⚙️ Configuration

### CSRF

- **Django templates** — `getCookie('csrftoken')` in inline JS; `@ensure_csrf_cookie` on views that need it
- **React** — Axios interceptor in `frontend/src/api/client.js` auto-attaches `X-CSRFToken` on all mutations

### UserSettings Singleton

`UserSettings.get_settings()` returns the single settings row (pk=1). Latest weight is pulled from the `Weight` model, falling back to the `current_weight` field on the settings object.

---

## 📖 Usage Guide

### Food Tracking
1. Go to **Food Tracker**
2. Select a date (defaults to today)
3. Add items manually or click **AI Lookup** to auto-fill macros via Gemini
4. Use **Quick Add** to re-log previously eaten foods
5. Use **Copy Previous Day** to duplicate an entire day's meals

### Meal Templates
1. Go to **Meal Templates**
2. Name a template and add food items to it
3. Click **Log Template** from any date to add all items at once

### Analytics → Product Compare
1. Go to **Analytics → Product Compare**
2. Type a food name in field A — autocomplete shows items from your log
3. Type a food name in field B (and optionally C for 3-way)
4. Click **Search** to see the full comparison
5. Drag the **Serving Multiplier** slider to scale all values (e.g. 2× = double portion)
6. Previously compared pairs appear as chips above the form for quick re-use

### Workout Tracking
1. Go to **Workout Tracker**
2. Create a session and add exercises
3. Log sets, reps, and weight — PRs are highlighted automatically
4. Use **Workout Tables** for structured program planning

---

## 📚 Documentation

### Project Structure

```
Calories_Counter_Project/
├── count_calories_app/
│   ├── models.py            # 11 database models
│   ├── views.py             # All view logic & API endpoints (~5 500 lines)
│   ├── services.py          # GeminiService — AI nutrition lookup
│   ├── urls.py              # URL routing
│   ├── templates/           # Django HTML templates
│   └── tests/               # 369 unit tests (10 modules)
├── frontend/
│   ├── src/                 # React source (JSX, Tailwind v4)
│   ├── vite.config.js       # Builds to ../static/react/
│   └── package.json
├── templates/
│   └── base.html            # Global base template
├── static/
│   └── react/               # Built React app (git-ignored)
├── Calories_Counter_Project/
│   └── urls.py              # Root URL config with React catch-all
├── requirements.txt
└── .env                     # Secret keys (not committed)
```

### Running Tests

```bash
# All 369 Django tests
python manage.py test count_calories_app

# Single module
python manage.py test count_calories_app.tests.test_views

# With verbosity
python manage.py test count_calories_app --verbosity=2

# React tests
cd frontend && npm test
```

### URL Reference

| URL | Description |
|---|---|
| `/` | Home / dashboard |
| `/food_tracker/` | Food log |
| `/meal-templates/` | Meal templates |
| `/weight/` | Weight tracker |
| `/running/` | Running tracker |
| `/workout/` | Workout tracker |
| `/workout-table/` | Custom workout tables |
| `/exercise/` | Exercise library |
| `/body-measurements/` | Body measurements |
| `/analytics/` | Analytics overview |
| `/analytics/month-compare/` | Month comparison |
| `/analytics/trends/` | Yearly trends |
| `/analytics/product-compare/` | Product compare |
| `/settings/` | User settings & data export |
| `/app/` | React SPA entry point |
| `/api/react/*` | JSON API for React |
| `/api/*` | JSON API for Chart.js |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### Transform Your Health Journey with Data-Driven Insights

**[Get Started](#-quick-start)** · **[Features](#-features)** · **[Analytics](#-analytics-dashboard)**

---

Made with ❤️ for health enthusiasts

<sub>Last updated: 2026-02-22</sub>

</div>
