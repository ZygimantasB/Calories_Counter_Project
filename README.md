# HealthTracker Pro
Your Comprehensive Fitness & Nutrition Dashboard

![HealthTracker Pro](https://via.placeholder.com/1200x400?text=HealthTracker+Pro)

<p align="center">
  <a href="https://www.python.org/downloads/release/python-380/"><img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white"></a>
  <a href="https://www.djangoproject.com/"><img alt="Django" src="https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white"></a>
  <a href="#license"><img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="#-contributing"><img alt="PRs Welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg"></a>
</p>

HealthTracker Pro is an all‑in‑one web app to monitor and optimize your health journey. Track nutrition, workouts, runs, weight, and body measurements with clear visuals and a clean, user‑friendly UI.

---

## Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Roadmap](#-roadmap)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

## ✨ Features

### 🍎 Nutrition Tracking
- Food Diary: log meals with detailed nutrition
- Macronutrient analysis: calories, protein, carbs, fat
- Quick‑add frequently eaten items
- Visual analytics for daily/weekly/monthly trends

### 💪 Workout Management
- Exercise library with descriptions
- Record sessions: sets, reps, weights
- Custom workout tables/routines
- Progress tracking for strength and frequency

### 🏃‍♂️ Running Tracker
- Log distance, duration, notes for each run
- Analytics for pace, distance, frequency
- Charts to visualize improvements over time

### ⚖️ Weight Tracking
- Weight journal with history
- Trend analysis via interactive charts
- Goal tracking and progress monitoring

### 📏 Body Measurements
- Track multiple body parts
- Symmetry comparisons (left vs right)
- Composition and measurement change visuals

## 🛠 Tech Stack
**Backend**
- Django 5.1
- SQLite
- python‑decouple for environment config
- Structured logging configuration

**Frontend**
- Bootstrap 5
- Chart.js
- Font Awesome

## 📋 Prerequisites
- Python 3.8+
- pip
- Virtual environment tool (recommended)

## ⚡ Quick Start
1) Clone the repository
   ```bash
   git clone https://github.com/ZygimantasB/Calories_Counter_Project.git
   cd Calories_Counter_Project
   ```
2) Create and activate a virtual environment
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3) Install dependencies
   ```bash
   # Note: The project currently doesn't include a requirements.txt file
   pip install django python-decouple
   ```
4) Create a .env file in the project root
   ```
   DJANGO_SECRET_KEY=your_secret_key_here
   ```
5) Apply migrations and run the server
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
6) Open http://127.0.0.1:8000/ in your browser

## 🚀 Usage
- Dashboard: overview of your current stats
- Food Tracking: log meals and review nutrition analytics
- Workout Tracking: record exercises and assess progress
- Body Stats: add weight and body measurements

Note: The Django admin is not configured in the current implementation; use the app’s built‑in UI to manage your data.

### Data Visualization
- Nutrition breakdowns (daily/weekly/monthly)
- Weight trends over time
- Workout frequency and progress
- Running performance metrics
- Body measurement changes

## 🔮 Roadmap
Planned enhancements include:
- AI‑powered insights for personalized recommendations
- Wearable integration (fitness trackers, smartwatches)
- Meal planning guided by your nutrition goals
- Social features (share achievements, friendly challenges)
- Voice input for hands‑free logging
- AR workout guidance
- Predictive analytics to forecast progress

## 🖼️ Screenshots
> Replace placeholders with real screenshots when available.

| Dashboard | Nutrition | Workouts |
| --- | --- | --- |
| ![Dashboard](https://via.placeholder.com/300x180?text=Dashboard) | ![Nutrition](https://via.placeholder.com/300x180?text=Nutrition) | ![Workouts](https://via.placeholder.com/300x180?text=Workouts) |

## 🤝 Contributing
Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "feat: add amazing feature"`
4. Push the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please follow the project’s coding style and include appropriate tests when applicable.

## 📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

## 📬 Contact
- Repository: https://github.com/ZygimantasB/Calories_Counter_Project
- Issues: https://github.com/ZygimantasB/Calories_Counter_Project/issues

---

<p align="center"><strong>Transform your health journey with data‑driven insights</strong></p>

<sub>Last updated: 2025-08-25</sub>
