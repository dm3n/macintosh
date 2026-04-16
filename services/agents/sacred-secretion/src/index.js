/**
 * Sacred Secretion Agent
 *
 * Tracks the monthly lunar Gemini transit and sends practice-guiding emails
 * to daniel@nodebase.ca at each phase of the sacred secretion cycle.
 *
 * Runs daily via cron. Uses astronomia for moon position, Resend for delivery,
 * Postgres for cycle state persistence.
 *
 * Email sequence (7 emails per cycle):
 *   1. windowOpens    — Moon enters Gemini
 *   2. windowDay1     — 24 hours in
 *   3. windowMidpoint — ~48 hours in (Gethsemane pressure point)
 *   4. windowClosing  — ~58 hours in (final hours)
 *   5. ascentWeek1    — Day 7 post-window
 *   6. ascentWeek2    — Day 14 post-window
 *   7. preWindow      — Day 26 post-window (~2 days before next window)
 */

const { createLogger } = require('../../../lib/logger');
const { createDb } = require('../../../lib/db');
const cron = require('node-cron');

const { geminiTransitOccurredToday, moonInGemini } = require('./lunar');
const { EMAILS } = require('./emails');
const {
  getActiveCycle,
  createCycle,
  emailAlreadySent,
  markEmailSent,
  updatePhase,
  completeCycle,
  daysSince,
} = require('./cycle');

const AGENT_ID = 'sacred-secretion';
const SCHEDULE = process.env.SACRED_SCHEDULE || '0 7 * * *'; // 7am daily

async function run(db, logger) {
  const now = new Date();
  logger.info({ now }, 'sacred secretion agent run started');

  let cycle = await getActiveCycle(db);

  // ── Window just opened (moon entered Gemini today) ──────────────────────────
  if (geminiTransitOccurredToday(now)) {
    logger.info('Gemini transit detected — window opening');

    if (!cycle) {
      cycle = await createCycle(db, now.toISOString());
    }

    if (!emailAlreadySent(cycle, 'windowOpens')) {
      await EMAILS.windowOpens();
      await markEmailSent(db, cycle.id, 'windowOpens');
      logger.info('sent: windowOpens');
    }
    return;
  }

  // ── No active cycle — nothing to do ─────────────────────────────────────────
  if (!cycle) {
    logger.info('no active cycle — waiting for next Gemini transit');
    return;
  }

  const daysSinceWindow = daysSince(cycle.window_start);

  // ── Within the 2.5-day window ────────────────────────────────────────────────
  if (moonInGemini(now)) {
    if (daysSinceWindow >= 1 && !emailAlreadySent(cycle, 'windowDay1')) {
      await EMAILS.windowDay1();
      await markEmailSent(db, cycle.id, 'windowDay1');
      await updatePhase(db, cycle.id, 'window-day1');
      logger.info('sent: windowDay1');
      return;
    }

    if (daysSinceWindow >= 2 && !emailAlreadySent(cycle, 'windowMidpoint')) {
      await EMAILS.windowMidpoint();
      await markEmailSent(db, cycle.id, 'windowMidpoint');
      await updatePhase(db, cycle.id, 'gethsemane');
      logger.info('sent: windowMidpoint');
      return;
    }

    return;
  }

  // ── Window just closed (moon left Gemini) ────────────────────────────────────
  if (!emailAlreadySent(cycle, 'windowClosing')) {
    await EMAILS.windowClosing();
    await markEmailSent(db, cycle.id, 'windowClosing');
    await updatePhase(db, cycle.id, 'ascent');
    logger.info('sent: windowClosing');
    return;
  }

  // ── Ascent phase — day 7 ─────────────────────────────────────────────────────
  if (daysSinceWindow >= 7 && !emailAlreadySent(cycle, 'ascentWeek1')) {
    await EMAILS.ascentWeek1();
    await markEmailSent(db, cycle.id, 'ascentWeek1');
    logger.info('sent: ascentWeek1');
    return;
  }

  // ── Ascent phase — day 14 ────────────────────────────────────────────────────
  if (daysSinceWindow >= 14 && !emailAlreadySent(cycle, 'ascentWeek2')) {
    await EMAILS.ascentWeek2();
    await markEmailSent(db, cycle.id, 'ascentWeek2');
    logger.info('sent: ascentWeek2');
    return;
  }

  // ── Pre-window reminder — day 26 (next window ~2 days away) ─────────────────
  if (daysSinceWindow >= 26 && !emailAlreadySent(cycle, 'preWindow')) {
    await EMAILS.preWindowReminder();
    await markEmailSent(db, cycle.id, 'preWindow');
    logger.info('sent: preWindow');
    return;
  }

  // ── Cycle complete — day 28+ and all emails sent ─────────────────────────────
  if (daysSinceWindow >= 28) {
    await completeCycle(db, cycle.id);
    logger.info('cycle completed — ready for next Gemini transit');
    return;
  }

  logger.info({ daysSinceWindow, phase: cycle.phase }, 'ascent phase — holding');
}

async function main() {
  const logger = createLogger('agent-sacred-secretion');
  const db = createDb(logger);

  logger.info({ schedule: SCHEDULE }, 'sacred secretion agent starting');

  cron.schedule(SCHEDULE, async () => {
    try {
      await run(db, logger);
    } catch (err) {
      logger.error({ err }, 'agent run failed');
    }
  });

  // Run once immediately on startup so we do not miss a transit on deploy day
  try {
    await run(db, logger);
  } catch (err) {
    logger.error({ err }, 'initial run failed');
  }
}

main();
