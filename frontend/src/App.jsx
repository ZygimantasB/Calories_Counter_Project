import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import {
  Dashboard,
  FoodTracker,
  WeightTracker,
  WorkoutTracker,
  RunningTracker,
  BodyMeasurements,
  Analytics,
  TopFoods,
} from './pages';

function App() {
  return (
    <Router basename="/app">
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="food" element={<FoodTracker />} />
          <Route path="weight" element={<WeightTracker />} />
          <Route path="workout" element={<WorkoutTracker />} />
          <Route path="running" element={<RunningTracker />} />
          <Route path="body-measurements" element={<BodyMeasurements />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="top-foods" element={<TopFoods />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
