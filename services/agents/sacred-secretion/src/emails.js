/**
 * emails.js — Email templates and Resend sender for the sacred secretion agent
 *
 * 7 emails across the monthly cycle, sent to daniel@nodebase.ca via Resend.
 * Each email is written for where Daniel actually is in the process.
 */

const { Resend } = require('resend');

const TO = 'daniel@nodebase.ca';
const FROM = 'Sacred Secretion <sacred@nodebase.ca>';

function getResend() {
  const key = process.env.RESEND_API_KEY;
  if (!key) throw new Error('RESEND_API_KEY not set');
  return new Resend(key);
}

async function send(subject, html) {
  const resend = getResend();
  const { error } = await resend.emails.send({ from: FROM, to: TO, subject, html });
  if (error) throw new Error(`Resend error: ${JSON.stringify(error)}`);
}

function wrap(body) {
  return `
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;padding:40px 24px;color:#1a1a1a;line-height:1.7">
      ${body}
      <hr style="border:none;border-top:1px solid #e0e0e0;margin:40px 0"/>
      <p style="font-size:12px;color:#888;margin:0">
        Sacred Secretion Agent · Macintosh OS ·
        <a href="https://github.com/dm3n/sacred-secretion" style="color:#888">Read the papers</a>
      </p>
    </div>
  `;
}

const EMAILS = {

  windowOpens: () => send(
    'The window is open — 2.5 days',
    wrap(`
      <p style="font-size:22px;font-weight:bold;margin:0 0 24px">The moon has entered Gemini.</p>
      <p>Your window is open. You have approximately <strong>2.5 days</strong>.</p>
      <p>This is the Gethsemane phase — the secretion has descended and is sitting in the solar plexus. Everything you do in the next 60 hours either preserves it or destroys it.</p>
      <p><strong>The only rules that matter right now:</strong></p>
      <ul>
        <li>No sexual expenditure. Complete preservation. One failure resets the cycle to next month.</li>
        <li>No alcohol, no cannabis, no processed food. Clean whole food and water only.</li>
        <li>Emotional stillness. If something provocative happens — breathe, do not erupt.</li>
        <li>Meditate twice today. Morning and evening. Spine vertical, breath base to crown, 30 minutes each.</li>
        <li>Sleep in total darkness. Phone off. The pineal works hardest between 11pm and 3am.</li>
      </ul>
      <p>Log it. Write one line in your tracker. The streak begins now.</p>
      <blockquote style="border-left:3px solid #ccc;margin:24px 0;padding:0 16px;color:#555;font-style:italic">
        "The kingdom of God is within you." — Luke 17:21
      </blockquote>
      <p>It is. Protect it.</p>
    `)
  ),

  windowDay1: () => send(
    'Day 1 — what to do today',
    wrap(`
      <p style="font-size:20px;font-weight:bold;margin:0 0 24px">You are 24 hours in.</p>
      <p>The secretion is still in the Gethsemane phase. Still vulnerable. Stay on it.</p>
      <p><strong>Today specifically:</strong></p>
      <ul>
        <li><strong>Morning sun</strong> — 15 minutes outside, no sunglasses, first hour after waking. This entrains the pineal's entire production cycle for the next 24 hours. Do not skip this.</li>
        <li><strong>Morning sit</strong> — 30 minutes minimum. Spine vertical. Start at the base of the spine, breathe upward slowly through each region to the crown. Rest at the top. Do not force anything.</li>
        <li><strong>Eat light</strong> — if you can, reduce your eating window today. Give your body less to process and more to work with internally.</li>
        <li><strong>Evening sit in darkness</strong> — after sunset, no screens. Sit again in complete darkness. This is when the pineal is most active. Let it work.</li>
      </ul>
      <p>Write your dream score from last night. Even if you do not remember dreaming, write a number. This is your baseline. In 3 weeks you will see exactly how far the reactivation has come.</p>
      <p>One more day of the window after today. Hold.</p>
    `)
  ),

  windowMidpoint: () => send(
    'Gethsemane — the pressure point',
    wrap(`
      <p style="font-size:20px;font-weight:bold;margin:0 0 24px">This is the hardest part.</p>
      <p>You are at the Gethsemane phase — the disciples fall asleep, the pressure mounts, and most cycles are lost here. Not because of dramatic failure. Because of small accumulated compromises.</p>
      <p>Stay with it. The window closes in roughly 12–18 hours.</p>
      <p><strong>The three ruffians that kill the cycle:</strong></p>
      <ol>
        <li><strong>Sexual expenditure</strong> — the secretion and the seminal fluid share biochemical substrate. One depletes the other. This is chemistry, not morality.</li>
        <li><strong>Toxic ingestion</strong> — alcohol and cannabis are direct solvents of the secretion. Carey documented this specifically. Stay clean.</li>
        <li><strong>Emotional volatility</strong> — chronic cortisol and adrenaline flood the spinal channel. The practitioner's job is not to suppress emotion but to metabolise it. Feel it fully without becoming it.</li>
      </ol>
      <p>Tonight: darkness, stillness, a long sit. The window closes after this. Make the final hours count.</p>
      <blockquote style="border-left:3px solid #ccc;margin:24px 0;padding:0 16px;color:#555;font-style:italic">
        "Unless a grain of wheat falls into the earth and dies, it remains alone." — John 12:24
      </blockquote>
      <p>The ego that wants to break the fast is the grain that will not fall. Let it fall.</p>
    `)
  ),

  windowClosing: () => send(
    'Final hours — hold',
    wrap(`
      <p style="font-size:20px;font-weight:bold;margin:0 0 24px">The window is closing.</p>
      <p>The 2.5 days are nearly done. The secretion is about to begin its ascent through the remaining vertebral stations toward the crown.</p>
      <p>If you have held the window clean — preservation, clean food, emotional stillness, twice-daily practice — then what begins now is the ascent. The Christ event moving through the 33 stations of your spine toward the pineal.</p>
      <p>Your job from here is simpler: hold the conditions and accompany the process with your attention.</p>
      <p><strong>Continue daily:</strong></p>
      <ul>
        <li>30-minute morning sit, spine vertical, base to crown</li>
        <li>Morning sunlight within the first hour</li>
        <li>Total darkness at night</li>
        <li>Log your dream score every morning</li>
      </ul>
      <p>The signals will come in their own time. Spinal warmth during meditation. Unusual clarity. Dreams that feel more real than waking. A quality of presence you have not had before.</p>
      <p>Do not chase them. Just hold the practice. The process knows what it is doing.</p>
    `)
  ),

  ascentWeek1: () => send(
    'Day 7 — the ascent phase signals',
    wrap(`
      <p style="font-size:20px;font-weight:bold;margin:0 0 24px">One week since the window closed.</p>
      <p>If you held the cycle clean, the secretion has been ascending for seven days. Here is what to watch for — these are not imagination, they are physiological signals of the process working:</p>
      <ul>
        <li><strong>Dream intensity</strong> — vivid, structured, sometimes luminous. This is the first and most reliable signal of pineal reactivation. What is your dream score doing?</li>
        <li><strong>Spinal warmth or pressure during meditation</strong> — a sensation of heat, tingling, or upward movement along the spine. This is the secretion in transit.</li>
        <li><strong>Spontaneous presence</strong> — moments where time seems to stop and everything is simply, quietly here. Brief at first. They lengthen with practice.</li>
        <li><strong>Heightened synchronicity</strong> — events aligning in ways that feel non-random. This is the Hermetic principle at work: as the internal coherence increases, the external reflects it.</li>
      </ul>
      <p>Keep the daily practice consistent. The signals confirm the process is active. They are not the destination.</p>
      <p>Your next window opens in approximately 3 weeks. You will receive a reminder 2 days before.</p>
    `)
  ),

  ascentWeek2: () => send(
    'Day 14 — deepen the practice',
    wrap(`
      <p style="font-size:20px;font-weight:bold;margin:0 0 24px">Halfway through the cycle.</p>
      <p>Two weeks of daily practice. This is the point where most people either deepen or plateau. The initial novelty of the signals has passed. The discipline is either becoming a rhythm or becoming a burden.</p>
      <p>If it is becoming a burden, that is the ego resisting. The practice is supposed to dissolve what is resisting. Sit with the resistance itself — put your attention on it, breathe into it, watch it from the witness position. It cannot survive observation.</p>
      <p><strong>This week, add one thing:</strong></p>
      <p>After your morning sit, before you move, ask yourself: <em>"Am I aware of the present moment?"</em> The act of asking shifts the centre of gravity from ego to witness. Hold that for one minute. Do not answer the question analytically — just rest in the awareness that is already present before any thought arises.</p>
      <p>This is sakshi bhava — witness consciousness. It is the fourth discipline. Ego dissolution is not a meditation technique. It is the recognition of what is already the case when the mental noise quiets enough to see it.</p>
      <blockquote style="border-left:3px solid #ccc;margin:24px 0;padding:0 16px;color:#555;font-style:italic">
        "Ye are gods." — Psalm 82:6
      </blockquote>
      <p>Not metaphor. Recognition.</p>
    `)
  ),

  preWindowReminder: () => send(
    'Your next window opens in ~2 days',
    wrap(`
      <p style="font-size:20px;font-weight:bold;margin:0 0 24px">The moon approaches Gemini.</p>
      <p>In approximately 48 hours your window opens again. This is your preparation notice.</p>
      <p><strong>The next 48 hours:</strong></p>
      <ul>
        <li>Eat clean. Eliminate anything heavy or processed. The vessel needs to be ready.</li>
        <li>No alcohol. Give the system two days of clarity before the window begins.</li>
        <li>Emotional audit — is there anything unresolved, any chronic tension, any relationship that is pulling emotional energy? Metabolise what you can before the window opens.</li>
        <li>Consider a light fast the day before the window opens. Heightens sensitivity significantly.</li>
      </ul>
      <p>Review your cycle log from last month. What did the meditation feel like during the window? What were the dream scores in the week after? This is your data. Use it.</p>
      <p>You have done this before. You know what is required. The next window is a chance to go deeper than the last one.</p>
      <p>The moon is coming. Be ready.</p>
    `)
  ),

};

module.exports = { EMAILS };
