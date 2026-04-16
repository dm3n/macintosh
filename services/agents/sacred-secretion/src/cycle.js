/**
 * cycle.js — Postgres state management for the sacred secretion cycle
 *
 * Tracks the current cycle phase and which emails have been sent
 * so the agent never double-sends and can resume after a restart.
 */

const { query } = require('../../../lib/db');

/**
 * Returns the active (non-completed) cycle row, or null if none exists.
 */
async function getActiveCycle(db) {
  const res = await query(
    db,
    `SELECT * FROM sacred_secretion_cycles
     WHERE completed = false
     ORDER BY window_start DESC
     LIMIT 1`
  );
  return res.rows[0] || null;
}

/**
 * Creates a new cycle record when the window opens.
 */
async function createCycle(db, windowStart) {
  const res = await query(
    db,
    `INSERT INTO sacred_secretion_cycles (window_start, phase, emails_sent)
     VALUES ($1, 'window', '[]'::jsonb)
     RETURNING *`,
    [windowStart]
  );
  return res.rows[0];
}

/**
 * Returns true if a given email key has already been sent in this cycle.
 */
function emailAlreadySent(cycle, key) {
  const sent = cycle.emails_sent || [];
  return sent.includes(key);
}

/**
 * Records that an email was sent by appending its key to emails_sent.
 */
async function markEmailSent(db, cycleId, key) {
  await query(
    db,
    `UPDATE sacred_secretion_cycles
     SET emails_sent = emails_sent || $2::jsonb,
         updated_at  = now()
     WHERE id = $1`,
    [cycleId, JSON.stringify([key])]
  );
}

/**
 * Updates the phase label on the active cycle.
 */
async function updatePhase(db, cycleId, phase) {
  await query(
    db,
    `UPDATE sacred_secretion_cycles SET phase = $2, updated_at = now() WHERE id = $1`,
    [cycleId, phase]
  );
}

/**
 * Marks the cycle as complete (month done, next cycle will create a new row).
 */
async function completeCycle(db, cycleId) {
  await query(
    db,
    `UPDATE sacred_secretion_cycles
     SET completed = true, completed_at = now(), updated_at = now()
     WHERE id = $1`,
    [cycleId]
  );
}

/**
 * Returns how many calendar days have elapsed since a given date.
 */
function daysSince(date) {
  const ms = Date.now() - new Date(date).getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}

module.exports = { getActiveCycle, createCycle, emailAlreadySent, markEmailSent, updatePhase, completeCycle, daysSince };
