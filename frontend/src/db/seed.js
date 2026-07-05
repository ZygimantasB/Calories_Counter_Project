// First-launch seed import: loads the user's existing data (bundled seed.json,
// generated from db.sqlite3 by scripts/build-seed.mjs) into the local database.
// Runs exactly once, guarded by an app_meta sentinel, inside a single transaction.
import seed from '../assets/seed/seed.json';
import { SEED_COLUMNS } from './schema';

const SEEDED_KEY = 'seeded';

async function isSeeded(conn) {
  const res = await conn.query(`SELECT value FROM app_meta WHERE key = ?;`, [SEEDED_KEY]);
  return (res.values ?? []).length > 0;
}

function buildInsertSet(table, columns, rows) {
  const placeholders = columns.map(() => '?').join(',');
  const statement = `INSERT INTO ${table} (${columns.join(',')}) VALUES (${placeholders});`;
  return rows.map((row) => ({
    statement,
    values: columns.map((c) => (row[c] === undefined ? null : row[c])),
  }));
}

/**
 * Seed the DB from the bundled snapshot if it has never been seeded.
 * @param {SQLiteDBConnection} conn
 */
export async function seedIfEmpty(conn) {
  if (await isSeeded(conn)) return false;

  const set = [];
  for (const [table, columns] of Object.entries(SEED_COLUMNS)) {
    const rows = seed[table] || [];
    if (rows.length) set.push(...buildInsertSet(table, columns, rows));
  }

  // user_settings singleton (pk=1) — always ensure a row exists.
  const settings = seed.user_settings;
  if (settings) {
    const cols = Object.keys(settings);
    set.push(...buildInsertSet('user_settings', cols, [settings]));
  } else {
    set.push({ statement: `INSERT INTO user_settings (id) VALUES (1);`, values: [] });
  }

  // Sentinel so we never re-seed.
  set.push({
    statement: `INSERT INTO app_meta (key, value) VALUES (?, ?);`,
    values: [SEEDED_KEY, new Date().toISOString()],
  });

  // executeSet wraps the whole batch in one transaction (fast + atomic).
  await conn.executeSet(set, true);
  return true;
}
