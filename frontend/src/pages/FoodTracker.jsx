import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Search,
  Flame,
  Beef,
  Wheat,
  Droplets,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Edit2,
  Clock,
  Sparkles,
  X,
  Loader2,
  Check,
  AlertCircle,
  Calendar,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { format, addDays, subDays, isToday, parseISO } from 'date-fns';
import { Card, Button, Badge, ProgressBar } from '../components/ui';
import { foodApi } from '../api';

const MACRO_COLORS = {
  protein: '#ef4444',
  carbs: '#f97316',
  fat: '#eab308',
};

export default function FoodTracker() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [foodItems, setFoodItems] = useState([]);
  const [totals, setTotals] = useState({ calories: 0, protein: 0, carbs: 0, fat: 0 });
  const [quickAddFoods, setQuickAddFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingFood, setEditingFood] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  // Form states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [aiQuery, setAiQuery] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const [showAiSearch, setShowAiSearch] = useState(false);

  // Add food form
  const [newFood, setNewFood] = useState({
    name: '',
    calories: '',
    protein: '',
    carbs: '',
    fat: '',
    weight: '100',
    date: format(new Date(), 'yyyy-MM-dd'),
  });
  const [addLoading, setAddLoading] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');

  // Database search states
  const [dbSearchQuery, setDbSearchQuery] = useState('');
  const [dbSearchResults, setDbSearchResults] = useState([]);
  const [dbSearchLoading, setDbSearchLoading] = useState(false);
  const [showDbSearch, setShowDbSearch] = useState(false);

  // Targets (can be made dynamic later)
  const targets = {
    calories: 2500,
    protein: 150,
    carbs: 300,
    fat: 70,
  };

  // Fetch food items
  const fetchFoodItems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const response = await foodApi.getFoodItems({ date: dateStr });
      setFoodItems(response.items || []);
      setTotals(response.totals || { calories: 0, protein: 0, carbs: 0, fat: 0 });
    } catch (err) {
      console.error('Error fetching food items:', err);
      setError('Failed to load food items');
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  // Fetch quick-add foods
  const fetchQuickAddFoods = async () => {
    try {
      const response = await foodApi.getQuickAddFoods();
      setQuickAddFoods(response.foods || []);
    } catch (err) {
      console.error('Error fetching quick-add foods:', err);
    }
  };

  useEffect(() => {
    fetchFoodItems();
  }, [fetchFoodItems]);

  useEffect(() => {
    fetchQuickAddFoods();
  }, []);

  // Database search function
  const handleDbSearch = async (query) => {
    setDbSearchQuery(query);
    try {
      setDbSearchLoading(true);
      const response = await foodApi.searchAllFoods(query, 15);
      setDbSearchResults(response.results || []);
    } catch (err) {
      console.error('Error searching foods:', err);
    } finally {
      setDbSearchLoading(false);
    }
  };

  // Quick add from database search
  const handleDbQuickAdd = async (food) => {
    try {
      await foodApi.addFood({
        name: food.name,
        calories: food.calories || 0,
        protein: food.protein || 0,
        carbs: food.carbs || 0,
        fat: food.fat || 0,
        weight: 100,
        date: format(selectedDate, 'yyyy-MM-dd'),
      });
      fetchFoodItems();
    } catch (err) {
      console.error('Error adding food:', err);
    }
  };

  // Edit from database search - opens form with prefilled values
  const handleDbEditAdd = (food) => {
    setNewFood({
      name: food.name,
      calories: food.calories?.toString() || '',
      protein: food.protein?.toString() || '',
      carbs: food.carbs?.toString() || '',
      fat: food.fat?.toString() || '',
      weight: '100',
      date: format(selectedDate, 'yyyy-MM-dd'),
    });
    setShowAddModal(true);
  };

  // Load initial database results when search panel opens
  useEffect(() => {
    if (showDbSearch && dbSearchResults.length === 0) {
      handleDbSearch('');
    }
  }, [showDbSearch]);

  // Totals now come from API (includes all items, not just paginated)

  const macrosPieData = [
    { name: 'Protein', value: totals.protein * 4, color: MACRO_COLORS.protein },
    { name: 'Carbs', value: totals.carbs * 4, color: MACRO_COLORS.carbs },
    { name: 'Fat', value: totals.fat * 9, color: MACRO_COLORS.fat },
  ];

  // Filter food items by search query
  const filteredFoodItems = foodItems.filter((item) =>
    item.name?.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const handleDateChange = (direction) => {
    setSelectedDate((prev) =>
      direction === 'next' ? addDays(prev, 1) : subDays(prev, 1)
    );
  };

  // Food search autocomplete
  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    try {
      setSearchLoading(true);
      const results = await foodApi.autocomplete(query);
      setSearchResults(results || []);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  // AI nutrition lookup
  const handleAiSearch = async () => {
    if (!aiQuery.trim()) return;
    try {
      setAiLoading(true);
      const result = await foodApi.getGeminiNutrition(aiQuery);
      if (result && result.success) {
        setAiResult(result);
        setNewFood({
          name: result.name || aiQuery,
          calories: result.calories?.toString() || '',
          protein: result.protein?.toString() || '',
          carbs: result.carbs?.toString() || '',
          fat: result.fat?.toString() || '',
          weight: result.weight?.toString() || '100',
          date: format(selectedDate, 'yyyy-MM-dd'),
        });
      }
    } catch (err) {
      console.error('AI search error:', err);
    } finally {
      setAiLoading(false);
    }
  };

  // Select from autocomplete
  const handleSelectFood = async (food) => {
    try {
      const nutrition = await foodApi.getNutritionData(food.name, 100);
      if (nutrition) {
        setNewFood({
          name: food.name,
          calories: nutrition.calories?.toString() || '',
          protein: nutrition.protein?.toString() || '',
          carbs: nutrition.carbs?.toString() || '',
          fat: nutrition.fat?.toString() || '',
          weight: '100',
          date: format(selectedDate, 'yyyy-MM-dd'),
        });
        setSearchQuery('');
        setSearchResults([]);
      }
    } catch (err) {
      console.error('Error getting nutrition data:', err);
    }
  };

  // Add food item
  const handleAddFood = async (e) => {
    e.preventDefault();
    try {
      setAddLoading(true);
      await foodApi.addFood({
        name: newFood.name,
        calories: parseInt(newFood.calories) || 0,
        protein: parseFloat(newFood.protein) || 0,
        carbs: parseFloat(newFood.carbs) || 0,
        fat: parseFloat(newFood.fat) || 0,
        weight: parseInt(newFood.weight) || 100,
        date: newFood.date,
      });
      setShowAddModal(false);
      setNewFood({
        name: '',
        calories: '',
        protein: '',
        carbs: '',
        fat: '',
        weight: '100',
        date: format(selectedDate, 'yyyy-MM-dd'),
      });
      setAiResult(null);
      setShowAiSearch(false);
      fetchFoodItems();
      fetchQuickAddFoods();
    } catch (err) {
      console.error('Error adding food:', err);
    } finally {
      setAddLoading(false);
    }
  };

  // Quick add food
  const handleQuickAdd = async (food) => {
    try {
      await foodApi.addFood({
        name: food.name,
        calories: food.calories || 0,
        protein: food.protein || 0,
        carbs: food.carbs || 0,
        fat: food.fat || 0,
        weight: food.weight || 100,
        date: format(selectedDate, 'yyyy-MM-dd'),
      });
      fetchFoodItems();
    } catch (err) {
      console.error('Error quick adding food:', err);
    }
  };

  // Delete food item
  const handleDeleteFood = async (foodId) => {
    try {
      await foodApi.deleteFood(foodId);
      setShowDeleteConfirm(null);
      fetchFoodItems();
    } catch (err) {
      console.error('Error deleting food:', err);
    }
  };

  // Edit food item
  const handleEditFood = async (e) => {
    e.preventDefault();
    if (!editingFood) return;
    try {
      setAddLoading(true);
      await foodApi.updateFood(editingFood.id, {
        name: editingFood.name,
        calories: parseInt(editingFood.calories) || 0,
        protein: parseFloat(editingFood.protein) || 0,
        carbs: parseFloat(editingFood.carbs) || 0,
        fat: parseFloat(editingFood.fat) || 0,
        weight: parseInt(editingFood.weight) || 100,
      });
      setShowEditModal(false);
      setEditingFood(null);
      fetchFoodItems();
    } catch (err) {
      console.error('Error updating food:', err);
    } finally {
      setAddLoading(false);
    }
  };

  const openEditModal = (food) => {
    setEditingFood({
      id: food.id,
      name: food.name,
      calories: food.calories?.toString() || '',
      protein: food.protein?.toString() || '',
      carbs: food.carbs?.toString() || '',
      fat: food.fat?.toString() || '',
      weight: food.weight?.toString() || '100',
    });
    setShowEditModal(true);
  };

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Food Tracker</h1>
          <p className="text-gray-400 mt-1">
            Track your daily nutrition intake
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showDbSearch ? 'primary' : 'ghost'}
            icon={Search}
            onClick={() => setShowDbSearch(!showDbSearch)}
          >
            {showDbSearch ? 'Close Search' : 'Search Foods'}
          </Button>
          <Button
            icon={Plus}
            onClick={() => setShowAddModal(true)}
          >
            Add Food
          </Button>
        </div>
      </div>

      {/* Database Search Section */}
      {showDbSearch && (
        <Card className="border-2 border-primary-500/50">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search all your foods..."
                value={dbSearchQuery}
                onChange={(e) => handleDbSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg"
                autoFocus
              />
              {dbSearchLoading && (
                <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary-500 animate-spin" />
              )}
            </div>

            {/* Search Results */}
            <div className="max-h-80 overflow-y-auto">
              {dbSearchResults.length > 0 ? (
                <div className="space-y-2">
                  {dbSearchResults.map((food, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg bg-gray-700/50 hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-100 truncate">
                          {food.name}
                        </div>
                        <div className="text-sm text-gray-400">
                          {food.calories} kcal · P: {food.protein}g · C: {food.carbs}g · F: {food.fat}g
                        </div>
                        {food.count > 1 && (
                          <div className="text-xs text-gray-500">
                            Logged {food.count} times
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDbEditAdd(food)}
                        >
                          <Edit2 className="w-4 h-4 mr-1" />
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleDbQuickAdd(food)}
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Add
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : dbSearchQuery && !dbSearchLoading ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No foods found for "{dbSearchQuery}"</p>
                  <Button
                    variant="ghost"
                    icon={Plus}
                    onClick={() => {
                      setNewFood({
                        ...newFood,
                        name: dbSearchQuery,
                        date: format(selectedDate, 'yyyy-MM-dd'),
                      });
                      setShowAddModal(true);
                    }}
                    className="mt-4"
                  >
                    Add "{dbSearchQuery}" as new food
                  </Button>
                </div>
              ) : !dbSearchLoading ? (
                <div className="text-center py-4 text-gray-500">
                  <p>Type to search your food history</p>
                </div>
              ) : null}
            </div>
          </div>
        </Card>
      )}

      {/* Date Selector */}
      <div className="flex flex-col items-center gap-3">
        {/* Quick Date Jump Buttons */}
        <div className="flex gap-1 p-1 bg-gray-700 rounded-lg">
          {[
            { label: 'Today', days: 0 },
            { label: 'Yesterday', days: 1 },
            { label: '3 Days Ago', days: 3 },
            { label: '1 Week Ago', days: 7 },
            { label: '2 Weeks Ago', days: 14 },
            { label: '1 Month Ago', days: 30 },
          ].map((item) => {
            const targetDate = subDays(new Date(), item.days);
            const isSelected = format(selectedDate, 'yyyy-MM-dd') === format(targetDate, 'yyyy-MM-dd');
            return (
              <button
                key={item.label}
                onClick={() => setSelectedDate(targetDate)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  isSelected
                    ? 'bg-gray-600 text-gray-100 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        {/* Day Navigation */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => handleDateChange('prev')}
            className="p-2 rounded-lg hover:bg-gray-700 text-gray-400 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="text-center min-w-[160px] relative">
            <label className="cursor-pointer group">
              <input
                type="date"
                value={format(selectedDate, 'yyyy-MM-dd')}
                onChange={(e) => {
                  if (e.target.value) {
                    setSelectedDate(new Date(e.target.value + 'T12:00:00'));
                  }
                }}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <h2 className="text-lg font-semibold text-gray-100 group-hover:text-primary-400 transition-colors flex items-center justify-center gap-2">
                {isToday(selectedDate) ? 'Today' : format(selectedDate, 'EEEE')}
                <Calendar className="w-4 h-4 opacity-50 group-hover:opacity-100" />
              </h2>
              <p className="text-sm text-gray-500 group-hover:text-gray-400">
                {format(selectedDate, 'MMMM d, yyyy')}
              </p>
            </label>
          </div>
          <button
            onClick={() => handleDateChange('next')}
            className="p-2 rounded-lg hover:bg-gray-700 text-gray-400 transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : error ? (
        <Card className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-400">{error}</p>
          <Button variant="ghost" onClick={fetchFoodItems} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Calories Summary */}
            <Card className="lg:col-span-2">
              <div className="flex flex-col md:flex-row gap-6">
                {/* Main Calorie Display */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-4">
                    <Flame className="w-5 h-5 text-orange-500" />
                    <span className="font-medium text-gray-300">
                      Daily Calories
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-4xl font-bold text-gray-100">
                      {Math.round(totals.calories)}
                    </span>
                    <span className="text-gray-500">
                      / {targets.calories} kcal
                    </span>
                  </div>
                  <ProgressBar
                    value={totals.calories}
                    max={targets.calories}
                    color={totals.calories > targets.calories ? 'red' : 'primary'}
                    size="lg"
                    showValue={false}
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    {targets.calories - totals.calories > 0
                      ? `${Math.round(targets.calories - totals.calories)} kcal remaining`
                      : `${Math.round(totals.calories - targets.calories)} kcal over target`}
                  </p>
                </div>

                {/* Macros Breakdown */}
                <div className="flex-1 grid grid-cols-3 gap-4">
                  <div className="text-center p-4 rounded-xl bg-red-500/10">
                    <Beef className="w-5 h-5 text-red-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-gray-100">
                      {Math.round(totals.protein)}g
                    </div>
                    <div className="text-sm text-gray-400">Protein</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round((totals.protein / targets.protein) * 100)}%
                    </div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-orange-500/10">
                    <Wheat className="w-5 h-5 text-orange-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-gray-100">
                      {Math.round(totals.carbs)}g
                    </div>
                    <div className="text-sm text-gray-400">Carbs</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round((totals.carbs / targets.carbs) * 100)}%
                    </div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-yellow-500/10">
                    <Droplets className="w-5 h-5 text-yellow-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-gray-100">
                      {Math.round(totals.fat)}g
                    </div>
                    <div className="text-sm text-gray-400">Fat</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round((totals.fat / targets.fat) * 100)}%
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Macro Pie Chart */}
            <Card title="Calorie Distribution">
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={macrosPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={70}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {macrosPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [`${Math.round(value)} kcal`, '']}
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-4 mt-2">
                {macrosPieData.map((entry) => (
                  <div key={entry.name} className="flex items-center gap-1.5">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-xs text-gray-400">{entry.name}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Quick Add */}
          {quickAddFoods.length > 0 && (
            <Card title="Quick Add" subtitle="Recently logged foods">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {quickAddFoods.slice(0, 6).map((food) => (
                  <button
                    key={food.id}
                    onClick={() => handleQuickAdd(food)}
                    className="p-4 rounded-xl border border-gray-700 hover:border-primary-500 hover:bg-gray-700/50 transition-all group"
                  >
                    <div className="text-sm font-medium text-gray-100 group-hover:text-primary-400 truncate">
                      {food.name}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{food.calories} kcal</div>
                    <div className="text-xs text-gray-600">
                      P: {food.protein}g · C: {food.carbs}g · F: {food.fat}g
                    </div>
                  </button>
                ))}
              </div>
            </Card>
          )}

          {/* Food Items List */}
          <Card title="Food Log" subtitle={`${foodItems.length} items`} padding={false}>
            {/* Search Filter */}
            <div className="p-4 border-b border-gray-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search foods..."
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                {filterQuery && (
                  <button
                    onClick={() => setFilterQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-gray-600 text-gray-400"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            {filteredFoodItems.length > 0 ? (
              <div className="divide-y divide-gray-700">
                {filteredFoodItems.map((item) => (
                  <div
                    key={item.id}
                    className="py-4 flex items-center justify-between hover:bg-gray-700/30 px-6 transition-colors group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-100 truncate">
                          {item.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <span>P: {Math.round(item.protein)}g</span>
                        <span>C: {Math.round(item.carbs)}g</span>
                        <span>F: {Math.round(item.fat)}g</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-gray-100">
                        {Math.round(item.calories)} kcal
                      </span>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        <button
                          onClick={() => openEditModal(item)}
                          className="p-1.5 rounded-lg hover:bg-gray-600 text-gray-400 hover:text-gray-200"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(item.id)}
                          className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : foodItems.length > 0 ? (
              <div className="py-12 text-center text-gray-500 px-6">
                <p>No foods matching "{filterQuery}"</p>
                <Button
                  variant="ghost"
                  onClick={() => setFilterQuery('')}
                  className="mt-4"
                >
                  Clear Search
                </Button>
              </div>
            ) : (
              <div className="py-12 text-center text-gray-500 px-6">
                <p>No foods logged for this day</p>
                <Button
                  variant="ghost"
                  icon={Plus}
                  onClick={() => setShowAddModal(true)}
                  className="mt-4"
                >
                  Add your first food
                </Button>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Add Food Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden animate-in border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-100">Add Food</h2>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setShowAiSearch(false);
                  setAiResult(null);
                  setSearchQuery('');
                  setSearchResults([]);
                }}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[calc(90vh-80px)]">
              {!showAiSearch ? (
                <>
                  {/* Search */}
                  <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Search foods..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      autoFocus
                    />
                    {searchLoading && (
                      <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 animate-spin" />
                    )}
                  </div>

                  {/* Search Results */}
                  {searchResults.length > 0 && (
                    <div className="mb-4 max-h-48 overflow-y-auto border border-gray-700 rounded-lg">
                      {searchResults.map((food, index) => (
                        <button
                          key={index}
                          onClick={() => handleSelectFood(food)}
                          className="w-full p-3 text-left hover:bg-gray-700 border-b border-gray-700 last:border-0"
                        >
                          <p className="text-gray-100">{food.name}</p>
                          {food.calories && (
                            <p className="text-sm text-gray-500">{food.calories} kcal per 100g</p>
                          )}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* AI Search Option */}
                  <button
                    onClick={() => setShowAiSearch(true)}
                    className="w-full p-4 mb-4 rounded-xl border border-dashed border-purple-500/50 bg-purple-500/10 hover:bg-purple-500/20 transition-colors flex items-center gap-3"
                  >
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-left">
                      <p className="font-medium text-purple-300">
                        AI Food Lookup
                      </p>
                      <p className="text-sm text-purple-400">
                        Describe your food and get nutrition info
                      </p>
                    </div>
                  </button>

                  {/* Manual Entry Form */}
                  <form onSubmit={handleAddFood} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Food Name
                      </label>
                      <input
                        type="text"
                        value={newFood.name}
                        onChange={(e) => setNewFood({ ...newFood, name: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Calories
                        </label>
                        <input
                          type="number"
                          value={newFood.calories}
                          onChange={(e) => setNewFood({ ...newFood, calories: e.target.value })}
                          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Weight (g)
                        </label>
                        <input
                          type="number"
                          value={newFood.weight}
                          onChange={(e) => setNewFood({ ...newFood, weight: e.target.value })}
                          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          required
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Protein (g)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newFood.protein}
                          onChange={(e) => setNewFood({ ...newFood, protein: e.target.value })}
                          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Carbs (g)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newFood.carbs}
                          onChange={(e) => setNewFood({ ...newFood, carbs: e.target.value })}
                          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Fat (g)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newFood.fat}
                          onChange={(e) => setNewFood({ ...newFood, fat: e.target.value })}
                          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Date
                      </label>
                      <input
                        type="date"
                        value={newFood.date}
                        onChange={(e) => setNewFood({ ...newFood, date: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full" disabled={addLoading}>
                      {addLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Plus className="w-4 h-4 mr-2" />
                      )}
                      Add Food
                    </Button>
                  </form>
                </>
              ) : (
                /* AI Search View */
                <div>
                  <button
                    onClick={() => {
                      setShowAiSearch(false);
                      setAiResult(null);
                    }}
                    className="mb-4 text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Back to search
                  </button>

                  <div className="relative mb-4">
                    <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400" />
                    <input
                      type="text"
                      placeholder="e.g., 200g chicken breast with rice..."
                      value={aiQuery}
                      onChange={(e) => setAiQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAiSearch()}
                      className="w-full pl-10 pr-4 py-3 rounded-lg border border-purple-500/50 bg-purple-500/10 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      autoFocus
                    />
                  </div>
                  <Button
                    onClick={handleAiSearch}
                    className="w-full mb-4 bg-gradient-to-r from-purple-500 to-pink-500 border-0"
                    disabled={aiLoading || !aiQuery.trim()}
                  >
                    {aiLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Sparkles className="w-4 h-4 mr-2" />
                    )}
                    Analyze with AI
                  </Button>

                  {aiResult && (
                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Check className="w-5 h-5 text-green-400" />
                        <span className="font-medium text-green-400">Found nutrition data</span>
                      </div>
                      <p className="text-gray-300">{aiResult.name}</p>
                      <div className="grid grid-cols-4 gap-2 mt-2 text-sm">
                        <div className="text-center p-2 rounded bg-gray-700">
                          <div className="text-gray-100 font-medium">{aiResult.calories}</div>
                          <div className="text-gray-500 text-xs">kcal</div>
                        </div>
                        <div className="text-center p-2 rounded bg-gray-700">
                          <div className="text-gray-100 font-medium">{aiResult.protein}g</div>
                          <div className="text-gray-500 text-xs">protein</div>
                        </div>
                        <div className="text-center p-2 rounded bg-gray-700">
                          <div className="text-gray-100 font-medium">{aiResult.carbs}g</div>
                          <div className="text-gray-500 text-xs">carbs</div>
                        </div>
                        <div className="text-center p-2 rounded bg-gray-700">
                          <div className="text-gray-100 font-medium">{aiResult.fat}g</div>
                          <div className="text-gray-500 text-xs">fat</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {aiResult && (
                    <form onSubmit={handleAddFood} className="space-y-4">
                      <input type="hidden" value={newFood.name} />
                      <Button type="submit" className="w-full" disabled={addLoading}>
                        {addLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Plus className="w-4 h-4 mr-2" />
                        )}
                        Add to Food Log
                      </Button>
                    </form>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Food Modal */}
      {showEditModal && editingFood && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-md overflow-hidden animate-in border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-100">Edit Food</h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingFood(null);
                }}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleEditFood} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Food Name
                </label>
                <input
                  type="text"
                  value={editingFood.name}
                  onChange={(e) => setEditingFood({ ...editingFood, name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Calories
                  </label>
                  <input
                    type="number"
                    value={editingFood.calories}
                    onChange={(e) => setEditingFood({ ...editingFood, calories: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Weight (g)
                  </label>
                  <input
                    type="number"
                    value={editingFood.weight}
                    onChange={(e) => setEditingFood({ ...editingFood, weight: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Protein (g)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingFood.protein}
                    onChange={(e) => setEditingFood({ ...editingFood, protein: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Carbs (g)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingFood.carbs}
                    onChange={(e) => setEditingFood({ ...editingFood, carbs: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Fat (g)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingFood.fat}
                    onChange={(e) => setEditingFood({ ...editingFood, fat: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  className="flex-1"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingFood(null);
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" disabled={addLoading}>
                  {addLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-sm overflow-hidden animate-in border border-gray-700">
            <div className="p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-100 mb-2">Delete Food Item?</h3>
              <p className="text-gray-400 mb-6">
                This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={() => setShowDeleteConfirm(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  className="flex-1 bg-red-500 hover:bg-red-600"
                  onClick={() => handleDeleteFood(showDeleteConfirm)}
                >
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
