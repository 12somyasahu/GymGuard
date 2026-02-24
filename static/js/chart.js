var HIST     = [];
var HIST_MAX = 120;

var EX_COL = {
  'Squat':          '#448aff',
  'Deadlift':       '#aa00ff',
  'Bench Press':    '#ff6d00',
  'Lunge':          '#00bcd4',
  'Bicep Curl':     '#76ff03',
  'Overhead Press': '#ff4081',
  'Standing':       '#78909c',
  'Detecting...':   '#37474f',
  'No person detected': '#263238',
};

function pushHistory(a) {
  HIST.push({ ts: Date.now(), score: a.risk_score || 0, exercise: a.exercise_detected || '' });
  if (HIST.length > HIST_MAX) HIST.shift();
  drawChart();
  updateLegend();
}

function drawChart() {
  var canvas = document.getElementById('histChart');
  var ctx    = canvas.getContext('2d');
  var dpr    = window.devicePixelRatio || 1;
  var W      = canvas.clientWidth;
  var H      = canvas.clientHeight;
  canvas.width  = W * dpr;
  canvas.height = H * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);
  if (!HIST.length || H <= 0) return;

  // grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth   = 1;
  [25, 50, 65, 100].forEach(function(v) {
    var y = H - (v / 100) * H;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,.18)';
    ctx.font      = '9px Space Mono, monospace';
    ctx.fillText(v, 3, y - 2);
  });

  var xStep = W / Math.max(HIST_MAX - 1, 1);

  // area fill
  ctx.beginPath();
  HIST.forEach(function(h, i) {
    var x = i * xStep;
    var y = H - (h.score / 100) * H;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo((HIST.length - 1) * xStep, H);
  ctx.lineTo(0, H);
  ctx.closePath();
  var ag = ctx.createLinearGradient(0, 0, 0, H);
  ag.addColorStop(0, 'rgba(68,138,255,.35)');
  ag.addColorStop(1, 'rgba(68,138,255,0)');
  ctx.fillStyle = ag;
  ctx.fill();

  // score line
  ctx.beginPath();
  ctx.strokeStyle = '#448aff';
  ctx.lineWidth   = 2;
  ctx.lineJoin    = 'round';
  HIST.forEach(function(h, i) {
    var x = i * xStep;
    var y = H - (h.score / 100) * H;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  // exercise color bar at bottom
  HIST.forEach(function(h, i) {
    ctx.fillStyle = EX_COL[h.exercise] || '#607d8b';
    ctx.fillRect(i * xStep, H - 4, xStep + 1, 4);
  });

  // current dot
  var last = HIST[HIST.length - 1];
  var lx   = (HIST.length - 1) * xStep;
  var ly   = H - (last.score / 100) * H;
  ctx.beginPath();
  ctx.arc(lx, ly, 4, 0, Math.PI * 2);
  ctx.fillStyle   = scoreCol(last.score);
  ctx.fill();
  ctx.strokeStyle = '#000';
  ctx.lineWidth   = 1.5;
  ctx.stroke();
}

function scoreCol(s) {
  return s < 30 ? '#00e676' : s < 65 ? '#ffd600' : '#ff1744';
}

function updateLegend() {
  var seen = {};
  HIST.forEach(function(h) { if (h.exercise) seen[h.exercise] = true; });
  document.getElementById('exLegend').innerHTML = Object.keys(seen).map(function(ex) {
    return '<div class="exdot"><span style="background:' + (EX_COL[ex] || '#607d8b') + '"></span>' + ex + '</div>';
  }).join('');
}

function clearHistory() {
  HIST.length = 0;
  var canvas  = document.getElementById('histChart');
  var ctx     = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  document.getElementById('exLegend').innerHTML  = '';
  document.getElementById('sAvg').textContent    = '--';
  document.getElementById('sPeak').textContent   = '--';
}

function exportCSV() {
  if (!HIST.length) { alert('No data yet.'); return; }
  var csv = 'Timestamp,Score,Exercise\n';
  HIST.forEach(function(h) {
    csv += new Date(h.ts).toISOString() + ',' + h.score + ',"' + h.exercise + '"\n';
  });
  var a    = document.createElement('a');
  a.href   = 'data:text/csv,' + encodeURIComponent(csv);
  a.download = 'gymguard_' + Date.now() + '.csv';
  a.click();
}

window.addEventListener('resize', function() { if (HIST.length) drawChart(); });