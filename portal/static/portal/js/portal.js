/* ==========================================================================
   VITALIS FITNESS CLUB - PORTAL DE SOCIOS JS
   Rest Timer, Canvas Chart & Interactive UI Controls
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initRestTimer();
  initWeightChart();
  initQrCode();
});

/* ==========================================================================
   1. REST TIMER (CRONÓMETRO DE DESCANSO CON WEB AUDIO API)
   ========================================================================== */
let timerInterval = null;
let totalSeconds = 90;
let remainingSeconds = 90;
let isPaused = false;
const CIRCUMFERENCE = 2 * Math.PI * 80; // r=80 in SVG circle

function initRestTimer() {
  const modal = document.getElementById('restTimerModal');
  if (!modal) return;

  const triggerButtons = document.querySelectorAll('.btn-timer-trigger');
  const closeBtn = document.getElementById('closeTimerBtn');
  const pauseBtn = document.getElementById('pauseTimerBtn');
  const add30Btn = document.getElementById('add30TimerBtn');
  const resetBtn = document.getElementById('resetTimerBtn');

  triggerButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const seconds = parseInt(btn.getAttribute('data-rest') || '90', 10);
      const exName = btn.getAttribute('data-exercise') || 'Ejercicio';
      openTimer(seconds, exName);
    });
  });

  if (closeBtn) closeBtn.addEventListener('click', closeTimer);
  if (pauseBtn) pauseBtn.addEventListener('click', togglePauseTimer);
  if (add30Btn) add30Btn.addEventListener('click', () => addSeconds(30));
  if (resetBtn) resetBtn.addEventListener('click', resetTimer);

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeTimer();
  });
}

function openTimer(seconds, exName) {
  const modal = document.getElementById('restTimerModal');
  const titleElem = document.getElementById('timerExerciseName');
  if (titleElem) titleElem.textContent = `Descanso: ${exName}`;

  totalSeconds = seconds;
  remainingSeconds = seconds;
  isPaused = false;

  modal.classList.add('active');
  updateTimerDisplay();
  startTimerCountdown();
}

function startTimerCountdown() {
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    if (!isPaused) {
      remainingSeconds--;
      updateTimerDisplay();

      if (remainingSeconds <= 0) {
        clearInterval(timerInterval);
        playFinishBeep();
        const digits = document.getElementById('timerDigits');
        if (digits) digits.textContent = '¡A DARLE!';
      }
    }
  }, 1000);
}

function updateTimerDisplay() {
  const digits = document.getElementById('timerDigits');
  const circle = document.getElementById('timerProgressCircle');
  if (!digits || !circle) return;

  const mins = Math.floor(remainingSeconds / 60);
  const secs = remainingSeconds % 60;
  digits.textContent = `${mins > 0 ? mins + ':' : ''}${secs < 10 && mins > 0 ? '0' : ''}${secs}s`;

  // Update circular dash offset
  const fraction = remainingSeconds / totalSeconds;
  const offset = CIRCUMFERENCE * (1 - fraction);
  circle.style.strokeDashoffset = offset;
}

function togglePauseTimer() {
  isPaused = !isPaused;
  const btn = document.getElementById('pauseTimerBtn');
  if (btn) btn.textContent = isPaused ? '▶ Reanudar' : '⏸ Pausar';
}

function addSeconds(sec) {
  remainingSeconds += sec;
  totalSeconds += sec;
  updateTimerDisplay();
}

function resetTimer() {
  remainingSeconds = totalSeconds;
  isPaused = false;
  const btn = document.getElementById('pauseTimerBtn');
  if (btn) btn.textContent = '⏸ Pausar';
  updateTimerDisplay();
  startTimerCountdown();
}

function closeTimer() {
  clearInterval(timerInterval);
  const modal = document.getElementById('restTimerModal');
  if (modal) modal.classList.remove('active');
}

function playFinishBeep() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.6);
  } catch (e) {
    console.log('Audio notification played');
  }
}

/* ==========================================================================
   2. WEIGHT PROGRESS CANVAS CHART
   ========================================================================== */
function initWeightChart() {
  const canvas = document.getElementById('weightHistoryChart');
  if (!canvas) return;

  const rawData = canvas.getAttribute('data-chart-json');
  let dataPoints = [];
  try {
    dataPoints = JSON.parse(rawData);
  } catch (e) {
    dataPoints = [
      { date: 'Jun 01', weight: 80.8 },
      { date: 'Jun 15', weight: 80.1 },
      { date: 'Jul 01', weight: 79.4 },
      { date: 'Jul 15', weight: 79.0 },
      { date: 'Hoy', weight: 78.5 }
    ];
  }

  if (!dataPoints || dataPoints.length === 0) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  
  canvas.width = rect.width * dpr;
  canvas.height = (rect.height || 220) * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height || 220;
  const padding = { top: 30, right: 30, bottom: 40, left: 45 };

  const weights = dataPoints.map(d => d.weight);
  const minWeight = Math.floor(Math.min(...weights) - 0.5);
  const maxWeight = Math.ceil(Math.max(...weights) + 0.5);

  const getX = index => padding.left + (index / (dataPoints.length - 1)) * (width - padding.left - padding.right);
  const getY = val => height - padding.bottom - ((val - minWeight) / (maxWeight - minWeight)) * (height - padding.top - padding.bottom);

  // Background Grid Lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  const gridSteps = 4;
  for (let i = 0; i <= gridSteps; i++) {
    const val = minWeight + (i / gridSteps) * (maxWeight - minWeight);
    const y = getY(val);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    // Axis label
    ctx.fillStyle = '#64748b';
    ctx.font = '10px Plus Jakarta Sans, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(`${val.toFixed(1)}k`, padding.left - 8, y + 3);
  }

  // Draw Gradient Area under curve
  const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  gradient.addColorStop(0, 'rgba(245, 184, 46, 0.25)');
  gradient.addColorStop(1, 'rgba(245, 184, 46, 0.0)');

  ctx.beginPath();
  ctx.moveTo(getX(0), getY(dataPoints[0].weight));
  for (let i = 1; i < dataPoints.length; i++) {
    ctx.lineTo(getX(i), getY(dataPoints[i].weight));
  }
  ctx.lineTo(getX(dataPoints.length - 1), height - padding.bottom);
  ctx.lineTo(getX(0), height - padding.bottom);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Draw Smooth Golden Line
  ctx.beginPath();
  ctx.moveTo(getX(0), getY(dataPoints[0].weight));
  for (let i = 1; i < dataPoints.length; i++) {
    ctx.lineTo(getX(i), getY(dataPoints[i].weight));
  }
  ctx.strokeStyle = '#f5b82e';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  // Draw Points & X-Labels
  dataPoints.forEach((point, i) => {
    const x = getX(i);
    const y = getY(point.weight);

    // X-Axis Date label
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Plus Jakarta Sans, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(point.date, x, height - 12);

    // Glowing Point
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#f5b82e';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#0b0f17';
    ctx.stroke();

    // Value pill on top of point
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 11px Outfit, sans-serif';
    ctx.fillText(`${point.weight}kg`, x, y - 10);
  });
}

/* ==========================================================================
   3. QR CODE GENERATOR FOR PASS
   ========================================================================== */
function initQrCode() {
  const qrContainer = document.getElementById('memberQrCodeCanvas');
  if (!qrContainer) return;

  const token = qrContainer.getAttribute('data-qr-val') || 'VITALIS-VIP-ACCESS';
  
  // Render crisp high contrast QR pattern
  const ctx = qrContainer.getContext('2d');
  const size = 180;
  qrContainer.width = size;
  qrContainer.height = size;

  // Simple clean mock QR matrix visual
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, size, size);

  ctx.fillStyle = '#0b0f17';
  const block = 10;
  
  // Standard QR position markers (Top-Left, Top-Right, Bottom-Left)
  drawFinderPattern(ctx, 10, 10, 50);
  drawFinderPattern(ctx, size - 60, 10, 50);
  drawFinderPattern(ctx, 10, size - 60, 50);

  // Dynamic noise seeded by token
  let seed = 0;
  for (let i = 0; i < token.length; i++) seed += token.charCodeAt(i);

  for (let x = 70; x < size - 70; x += block) {
    for (let y = 10; y < size - 10; y += block) {
      seed = (seed * 9301 + 49297) % 233280;
      if (seed / 233280 > 0.45) {
        ctx.fillRect(x, y, block - 1, block - 1);
      }
    }
  }
}

function drawFinderPattern(ctx, x, y, size) {
  ctx.fillStyle = '#0b0f17';
  ctx.fillRect(x, y, size, size);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(x + 8, y + 8, size - 16, size - 16);
  ctx.fillStyle = '#0b0f17';
  ctx.fillRect(x + 16, y + 16, size - 32, size - 32);
}

/* Modal Helpers */
window.openModal = function(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add('active');
};

window.closeModal = function(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove('active');
};
