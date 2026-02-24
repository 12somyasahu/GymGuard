let ws = null;
let sessionStart = null;
let sessionTimer = null;

function startStream() {
  var btn = document.getElementById('mainBtn');
  btn.textContent = 'CONNECTING...';
  btn.disabled = true;

  ws = new WebSocket('ws://' + location.host + '/ws');

  ws.onopen = function() {
    setStatus('LIVE', true);
    document.getElementById('placeholder').style.display = 'none';
    document.getElementById('feed').style.display = 'block';
    document.getElementById('gpuLabel').style.display = 'block';
    btn.textContent = 'STOP';
    btn.className = 'stop';
    btn.disabled = false;
    btn.onclick = stopStream;
    sessionStart = Date.now();
    sessionTimer = setInterval(tickTimer, 1000);
  };

  ws.onmessage = function(e) {
    var d = JSON.parse(e.data);
    document.getElementById('feed').src = 'data:image/jpeg;base64,' + d.frame;
    updateAnalysis(d.analysis);
    pushHistory(d.analysis);
    tickFPS();
  };

  ws.onclose = ws.onerror = function() {
    setStatus('OFFLINE', false);
    resetUI();
    clearInterval(sessionTimer);
    saveSession();
  };
}

function stopStream() {
  if (ws) { ws.close(); ws = null; }
}

function setStatus(txt, live) {
  document.getElementById('sTxt').textContent = txt;
  document.getElementById('sdot').className = live ? 'sdot live' : 'sdot';
}

function resetUI() {
  var btn = document.getElementById('mainBtn');
  btn.textContent = 'START ANALYSIS';
  btn.className = '';
  btn.disabled = false;
  btn.onclick = startStream;
  document.getElementById('feed').style.display = 'none';
  document.getElementById('placeholder').style.display = 'flex';
  document.getElementById('gpuLabel').style.display = 'none';
  document.getElementById('exLabel').textContent = '';
  document.getElementById('alertBar').className = '';
  document.getElementById('alertBar').textContent = '';
  document.getElementById('fpsPill').textContent = '-- FPS';
  document.getElementById('fpsPill').className = '';
}

function tickTimer() {
  if (!sessionStart) return;
  var s = Math.floor((Date.now() - sessionStart) / 1000);
  var m = Math.floor(s / 60);
  document.getElementById('sTime').textContent = m > 0 ? m + 'm' + (s % 60) + 's' : s + 's';
}

var frameCount = 0;
var lastFpsAt = Date.now();

function tickFPS() {
  frameCount++;
  var now = Date.now();
  if (now - lastFpsAt >= 1000) {
    var fps = frameCount;
    frameCount = 0;
    lastFpsAt = now;
    var pill = document.getElementById('fpsPill');
    pill.textContent = fps + ' FPS';
    pill.className = fps >= 22 ? 'fast' : fps >= 13 ? 'ok' : 'slow';
  }
}

function saveSession() {
  if (!HIST.length) return;
  try {
    var sessions = JSON.parse(localStorage.getItem('gg_sessions') || '[]');
    var scores = HIST.map(function(h) { return h.score; });
    sessions.push({
      date: new Date().toLocaleString(),
      avg: Math.round(scores.reduce(function(a, b) { return a + b; }, 0) / scores.length),
      peak: Math.max.apply(null, scores),
      dur: sessionStart ? Math.floor((Date.now() - sessionStart) / 1000) : 0,
    });
    if (sessions.length > 50) sessions.shift();
    localStorage.setItem('gg_sessions', JSON.stringify(sessions));
  } catch(e) {}
}