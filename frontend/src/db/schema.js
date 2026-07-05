// SQLite schema mirroring the Django models 1:1.
// Datetimes: ISO-8601 TEXT (UTC). Decimals: REAL. JSON: TEXT. Booleans: INTEGER 0/1.
// PKs are AUTOINCREMENT to match Django `id`.

export const SCHEMA_VERSION = 1;

export const SCHEMA_STATEMENTS = [
  `CREATE TABLE IF NOT EXISTS food_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    calories REAL NOT NULL DEFAULT 0,
    fat REAL NOT NULL DEFAULT 0,
    carbohydrates REAL NOT NULL DEFAULT 0,
    protein REAL NOT NULL DEFAULT 0,
    consumed_at TEXT NOT NULL,
    hide_from_quick_list INTEGER NOT NULL DEFAULT 0
  );`,
  `CREATE INDEX IF NOT EXISTS ix_food_consumed ON food_item(consumed_at);`,

  `CREATE TABLE IF NOT EXISTS weight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weight REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    notes TEXT
  );`,
  `CREATE INDEX IF NOT EXISTS ix_weight_recorded ON weight(recorded_at);`,

  `CREATE TABLE IF NOT EXISTS running_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    distance REAL NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    notes TEXT
  );`,

  `CREATE TABLE IF NOT EXISTS exercise (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    muscle_group TEXT
  );`,

  `CREATE TABLE IF NOT EXISTS workout_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    name TEXT,
    notes TEXT
  );`,

  `CREATE TABLE IF NOT EXISTS workout_exercise (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL REFERENCES workout_session(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercise(id) ON DELETE CASCADE,
    sets INTEGER NOT NULL DEFAULT 1,
    reps INTEGER NOT NULL DEFAULT 1,
    weight REAL,
    notes TEXT
  );`,
  `CREATE INDEX IF NOT EXISTS ix_we_workout ON workout_exercise(workout_id);`,

  `CREATE TABLE IF NOT EXISTS workout_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    table_data TEXT NOT NULL
  );`,

  `CREATE TABLE IF NOT EXISTS body_measurement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    neck REAL, chest REAL, belly REAL,
    left_biceps REAL, right_biceps REAL,
    left_triceps REAL, right_triceps REAL,
    left_forearm REAL, right_forearm REAL,
    left_thigh REAL, right_thigh REAL,
    left_lower_leg REAL, right_lower_leg REAL,
    butt REAL,
    weight REAL,
    notes TEXT
  );`,

  `CREATE TABLE IF NOT EXISTS meal_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
  );`,
  `CREATE TABLE IF NOT EXISTS meal_template_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES meal_template(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    calories REAL DEFAULT 0,
    protein REAL DEFAULT 0,
    fat REAL DEFAULT 0,
    carbohydrates REAL DEFAULT 0
  );`,

  `CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT DEFAULT '',
    age INTEGER,
    height REAL,
    current_weight REAL,
    activity_level TEXT DEFAULT 'moderate',
    gender TEXT DEFAULT 'male',
    fitness_goal TEXT DEFAULT 'maintain',
    use_auto_macros INTEGER DEFAULT 1,
    daily_calorie_target INTEGER DEFAULT 2000,
    target_weight REAL,
    weekly_workout_goal INTEGER DEFAULT 3,
    protein_target INTEGER DEFAULT 150,
    carbs_target INTEGER DEFAULT 200,
    fat_target INTEGER DEFAULT 65,
    theme TEXT DEFAULT 'dark',
    chart_color TEXT DEFAULT 'blue',
    default_date_range INTEGER DEFAULT 30,
    meal_reminder_enabled INTEGER DEFAULT 0,
    meal_reminder_times TEXT DEFAULT '[]',
    workout_reminder_enabled INTEGER DEFAULT 0,
    workout_reminder_time TEXT,
    workout_reminder_days TEXT DEFAULT '[]',
    weight_reminder_enabled INTEGER DEFAULT 0,
    weight_reminder_time TEXT,
    created_at TEXT,
    updated_at TEXT
  );`,

  // Internal metadata (seed sentinel, schema bookkeeping).
  `CREATE TABLE IF NOT EXISTS app_meta (
    key TEXT PRIMARY KEY,
    value TEXT
  );`,
];

// Columns used when inserting seed rows (must match seed.json shape).
export const SEED_COLUMNS = {
  food_item: ['id', 'product_name', 'calories', 'fat', 'carbohydrates', 'protein', 'consumed_at', 'hide_from_quick_list'],
  weight: ['id', 'weight', 'recorded_at', 'notes'],
  running_session: ['id', 'date', 'distance', 'duration_seconds', 'notes'],
  exercise: ['id', 'name', 'description', 'muscle_group'],
  workout_session: ['id', 'date', 'name', 'notes'],
  workout_exercise: ['id', 'workout_id', 'exercise_id', 'sets', 'reps', 'weight', 'notes'],
  workout_table: ['id', 'name', 'created_at', 'table_data'],
  body_measurement: ['id', 'date', 'neck', 'chest', 'belly', 'left_biceps', 'right_biceps', 'left_triceps', 'right_triceps', 'left_forearm', 'right_forearm', 'left_thigh', 'right_thigh', 'left_lower_leg', 'right_lower_leg', 'butt', 'weight', 'notes'],
  meal_template: ['id', 'name', 'created_at'],
  meal_template_item: ['id', 'template_id', 'product_name', 'calories', 'protein', 'fat', 'carbohydrates'],
};
