// Single on-device SQLite connection (via @capacitor-community/sqlite).
// Works on Android natively and in a browser (jeep-sqlite web store) for `npm run dev`.
import { CapacitorSQLite, SQLiteConnection } from '@capacitor-community/sqlite';
import { Capacitor } from '@capacitor/core';
import { SCHEMA_STATEMENTS } from './schema';
import { seedIfEmpty } from './seed';

const DB_NAME = 'calories';
const sqlite = new SQLiteConnection(CapacitorSQLite);

let db = null;
let initPromise = null;

async function ensureWebStore() {
  if (Capacitor.getPlatform() !== 'web') return;

  console.log('[SQLite DB] Running on Web. Setting up WASM shim and custom elements...');
  // jeep-sqlite fetches the sql.js wasm from an absolute "/assets/sql-wasm.wasm",
  // but under Django it is served at BASE_URL + "assets/sql-wasm.wasm"
  // (e.g. /static/react/assets/…). Redirect just that one request so the
  // browser-side database can initialise.
  if (!window.__sqlWasmShim) {
    window.__sqlWasmShim = true;
    const wasmUrl = new URL(`${import.meta.env.BASE_URL}assets/sql-wasm.wasm`, window.location.origin).href;
    const origFetch = window.fetch.bind(window);
    window.fetch = (input, init) => {
      const url = typeof input === 'string' ? input : input?.url;
      if (url && url.includes('sql-wasm.wasm') && !url.includes(import.meta.env.BASE_URL)) {
        return origFetch(wasmUrl, init);
      }
      return origFetch(input, init);
    };
  }

  // jeep-sqlite provides a WASM SQLite + IndexedDB-backed store in the browser.
  const { JeepSqlite } = await import('jeep-sqlite/dist/components/jeep-sqlite');
  if (!customElements.get('jeep-sqlite')) {
    console.log('[SQLite DB] Defining custom element <jeep-sqlite>...');
    customElements.define('jeep-sqlite', JeepSqlite);
  }
  if (!document.querySelector('jeep-sqlite')) {
    console.log('[SQLite DB] Mounting <jeep-sqlite> host element...');
    const el = document.createElement('jeep-sqlite');
    document.body.appendChild(el);
  }
  await customElements.whenDefined('jeep-sqlite');
  console.log('[SQLite DB] Initializing SQLite Web Store...');
  await sqlite.initWebStore();
  console.log('[SQLite DB] SQLite Web Store initialized successfully.');
}

async function openConnection() {
  const consistency = (await sqlite.checkConnectionsConsistency()).result ?? false;
  const isConn = (await sqlite.isConnection(DB_NAME, false)).result ?? false;
  if (consistency && isConn) {
    return sqlite.retrieveConnection(DB_NAME, false);
  }
  return sqlite.createConnection(DB_NAME, false, 'no-encryption', SCHEMA_STATEMENTS.length, false);
}

async function runSchema(conn) {
  await conn.execute('PRAGMA foreign_keys = ON;');
  for (const stmt of SCHEMA_STATEMENTS) {
    await conn.execute(stmt);
  }
}

/**
 * Initialise the database exactly once. Safe to call repeatedly (React StrictMode).
 * Opens the connection, applies schema, and seeds the user's data on first launch.
 */
export function initDb() {
  if (initPromise) return initPromise;
  initPromise = (async () => {
    try {
      console.log('[SQLite DB] Beginning database initialization...');
      await ensureWebStore();
      
      console.log('[SQLite DB] Opening SQLite connection...');
      db = await openConnection();
      await db.open();
      console.log('[SQLite DB] SQLite connection opened successfully.');

      console.log('[SQLite DB] Applying schema statements...');
      await runSchema(db);
      console.log('[SQLite DB] Schema applied successfully.');

      console.log('[SQLite DB] Seeding default database data if empty...');
      await seedIfEmpty(db);
      console.log('[SQLite DB] Seeding checked/completed.');

      if (Capacitor.getPlatform() === 'web') {
        console.log('[SQLite DB] Saving IndexedDB SQLite state to store...');
        await sqlite.saveToStore(DB_NAME);
      }
      
      console.log('[SQLite DB] Database fully initialized and ready!');
      return db;
    } catch (err) {
      console.error('[SQLite DB] CRITICAL: Database initialization failed:', err);
      initPromise = null; // allow retry on subsequent calls
      throw err;
    }
  })();
  return initPromise;
}

export function getDb() {
  if (!db) throw new Error('Database not initialised — call initDb() first.');
  return db;
}

// On web, changes live in memory until flushed to the IndexedDB store.
export async function persist() {
  if (Capacitor.getPlatform() === 'web') {
    await sqlite.saveToStore(DB_NAME);
  }
}

// ---- Query helpers: normalise @capacitor-community/sqlite return shapes ----

/** Run a read query; returns an array of row objects. */
export async function dbAll(sql, params = []) {
  const res = await getDb().query(sql, params);
  return res.values ?? [];
}

/** Run a read query; returns the first row object or null. */
export async function dbGet(sql, params = []) {
  const rows = await dbAll(sql, params);
  return rows.length ? rows[0] : null;
}

/**
 * Run a write statement (INSERT/UPDATE/DELETE).
 * Returns { changes, lastId }.
 */
export async function dbRun(sql, params = []) {
  const res = await getDb().run(sql, params, false);
  const changes = res.changes ?? {};
  await persist();
  return { changes: changes.changes ?? 0, lastId: changes.lastId ?? null };
}
