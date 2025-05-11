# HealthTracker Pro: Your Comprehensive Fitness & Nutrition Dashboard

![HealthTracker Pro](https://via.placeholder.com/1200x400?text=HealthTracker+Pro)

## 🚀 Next-Gen Health & Fitness Tracking

HealthTracker Pro is an all-in-one solution for monitoring and optimizing your health and fitness journey. This comprehensive web application provides powerful tools for tracking nutrition, workouts, body measurements, and more, all within a sleek, user-friendly interface.

## ✨ Key Features

### 🍎 Nutrition Tracking
- **Food Diary**: Log your meals with detailed nutritional information
- **Macronutrient Analysis**: Track calories, protein, carbs, and fat intake
- **Quick-Add Functionality**: Easily add frequently consumed items
- **Visual Analytics**: Interactive charts showing nutrition trends over time

### 💪 Workout Management
- **Exercise Library**: Comprehensive database of exercises with descriptions
- **Workout Sessions**: Record complete workout sessions with sets, reps, and weights
- **Workout Tables**: Create and save custom workout routines
- **Progress Tracking**: Monitor strength gains and workout frequency

### 🏃‍♂️ Running Tracker
- **Run Logging**: Record distance, duration, and notes for each run
- **Performance Analytics**: Track pace, distance, and frequency over time
- **Visual Progress**: Interactive charts showing running improvements

### ⚖️ Weight Tracking
- **Weight Journal**: Log your weight measurements over time
- **Trend Analysis**: Visualize weight changes with interactive charts
- **Goal Setting**: Monitor progress toward weight goals

### 📏 Body Measurements
- **Comprehensive Tracking**: Record measurements for multiple body parts
- **Symmetry Analysis**: Compare left and right side measurements
- **Progress Visualization**: Track changes in body composition over time

## 🔮 Future Enhancements

HealthTracker Pro is continuously evolving with planned features including:

- **AI-Powered Insights**: Personalized recommendations based on your data
- **Wearable Integration**: Sync with fitness trackers and smartwatches
- **Meal Planning**: AI-generated meal plans based on your nutritional goals
- **Social Features**: Share achievements and compete with friends
- **Voice Input**: Log meals and workouts using voice commands
- **AR Workout Guide**: Visual exercise guidance using augmented reality
- **Predictive Analytics**: Forecast your fitness progress based on current trends

## 🛠️ Technologies

### Backend
- **Django 5.1**: High-level Python web framework
- **SQLite**: Lightweight database for data storage
- **Python-Decouple**: Secure configuration management
- **Logging**: Comprehensive logging configuration for debugging and monitoring

### Frontend
- **Bootstrap 5**: Responsive design framework
- **Chart.js**: Interactive data visualization
- **Font Awesome**: Icon library

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment tool (recommended)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ZygimantasB/Calories_Counter_Project.git
   cd Calories_Counter_Project
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Note: The project currently doesn't include a requirements.txt file.
   # You'll need to install the following packages manually:
   pip install django python-decouple
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with:
   ```
   DJANGO_SECRET_KEY=your_secret_key_here
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

## 🚀 Usage

### Getting Started

1. **Dashboard**: View your health overview on the home page
2. **Food Tracking**: Log meals and view nutrition analytics
3. **Workout Tracking**: Record exercises and monitor progress
4. **Body Stats**: Track weight and body measurements

> **Note**: The Django admin interface is not configured in the current implementation. All data management is handled through the custom user interface.

### Data Visualization

HealthTracker Pro provides comprehensive analytics through interactive charts:
- Daily/weekly/monthly nutrition breakdowns
- Weight trends over time
- Workout frequency and progress
- Running performance metrics
- Body measurement changes

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's style guidelines and includes appropriate tests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

Project Link: [https://github.com/yourusername/Calories_Counter_Project](https://github.com/yourusername/Calories_Counter_Project)

---

<p align="center">
  <strong>Transform your health journey with data-driven insights</strong>
</p>
