/**
 * lunar.js — Moon position and Gemini transit detection
 *
 * Uses the astronomia package to compute the moon's ecliptic longitude
 * and determine which zodiac sign it occupies.
 *
 * Gemini = ecliptic longitude 60°–90° (sign index 2)
 */

const { julian, moonposition } = require('astronomia');

const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
];

/**
 * Returns the moon's ecliptic longitude in degrees [0, 360) for a given Date.
 */
function moonLongitude(date = new Date()) {
  const jd = julian.DateToJD(date);
  const pos = moonposition.position(jd);
  // pos.lon is in radians
  const deg = (pos.lon * 180) / Math.PI;
  return ((deg % 360) + 360) % 360;
}

/**
 * Returns the zodiac sign index (0=Aries … 11=Pisces) for a given Date.
 */
function moonSignIndex(date = new Date()) {
  return Math.floor(moonLongitude(date) / 30);
}

/**
 * Returns the zodiac sign name for a given Date.
 */
function moonSign(date = new Date()) {
  return SIGNS[moonSignIndex(date)];
}

/**
 * Returns true if the moon is currently in Gemini (sign index 2).
 */
function moonInGemini(date = new Date()) {
  return moonSignIndex(date) === 2;
}

/**
 * Checks whether the moon has just entered Gemini between yesterday and today.
 * Used by the daily cron to detect the window opening.
 */
function geminiTransitOccurredToday(now = new Date()) {
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  return !moonInGemini(yesterday) && moonInGemini(now);
}

/**
 * Returns an ISO date string (YYYY-MM-DD) for a given Date.
 */
function toDateString(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

module.exports = { moonLongitude, moonSignIndex, moonSign, moonInGemini, geminiTransitOccurredToday, toDateString };
