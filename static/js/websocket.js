let ws = null;
let sessionStart = null;
let sessionTimer = null;
let videoAnalyzing = false;

function startStream() {
  var btn = document.getElementById('mainBtn');
  btn.textContent = 'CONNECTING...';
  btn.disabled = true;

  ws = new WebSocket('ws://' + location.host + '/ws');

  ws.onopen = function() {
    setStatus('LIVE', true);
    document.getElementById('placeholder').style.display = 'none';
    document.getElementById('feed').style.display        = 'block';
    document.getElementById('gpuLabel').style.display    = 'block';
    btn.textContent = 'STOP';
    btn.className   = 'stop';
    btn.disabled    = false;
    btn.onclick     = stopStream;
    sessionStart    = Date.now();
    sessionTimer    = setInterval(tickTimer, 1000);
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

function analyzeVideo(input) {
  var file = input.files[0];
  if (!file) return;
  if (videoAnalyzing) return;

  // Stop webcam if running
  if (ws) { ws.close(); ws = null; }

  videoAnalyzing = true;
  var btn        = document.getElementById('mainBtn');
  btn.textContent = 'ANALYZING...';
  btn.disabled    = true;

  document.getElementById('placeholder').style.display    = 'none';
  document.getElementById('feed').style.display           = 'block';
  document.getElementById('gpuLabel').style.display       = 'block';
  document.getElementById('videoProgress').style.display  = 'block';
  setStatus('VIDEO MODE', false);

  var formData = new FormData();
  formData.append('file', file);

  fetch('/analyze-video', { method: 'POST', body: formData })
    .then(function(r) {
      var reader  = r.body.getReader();
      var decoder = new TextDecoder();
      var buffer  = '';
      var frames  = 0;

      function read() {
        reader.read().then(function(result) {
          if (result.done) {
            // Video finished
            videoAnalyzing = false;
            document.getElementById('videoProgress').style.display = 'none';
            document.getElementById('progressBar').style.width     = '100%';
            setStatus('VIDEO DONE', false);
            btn.textContent = 'START ANALYSIS';
            btn.className   = '';
            btn.disabled    = false;
            btn.onclick     = startStream;
            // reset file input so same file can be loaded again
            input.value = '';
            return;
          }

          buffer += decoder.decode(result.value, { stream: true });
          var lines = buffer.split('\n');
          buffer    = lines.pop(); // keep incomplete line

          lines.forEach(function(line) {
            if (!line.trim()) return;
            try {
              var d = JSON.parse(line);
              frames++;
              document.getElementById('feed').src        = 'data:image/jpeg;base64,' + d.frame;
              document.getElementById('progressTxt').textContent = frames + ' frames processed';
              updateAnalysis(d.analysis);
              pushHistory(d.analysis);
            } catch(e) {}
          });

          read();
        });
      }

      read();
    })
    .catch(function(err) {
      console.error('Video analysis error:', err);
      videoAnalyzing  = false;
      btn.textContent = 'START ANALYSIS';
      btn.className   = '';
      btn.disabled    = false;
      btn.onclick     = startStream;
    });
}

function setStatus(txt, live) {
  document.getElementById('sTxt').textContent = txt;
  document.getElementById('sdot').className   = live ? 'sdot live' : 'sdot';
}

function resetUI() {
  var btn         = document.getElementById('mainBtn');
  btn.textContent = 'START ANALYSIS';
  btn.className   = '';
  btn.disabled    = false;
  btn.onclick     = startStream;
  document.getElementById('feed').style.display           = 'none';
  document.getElementById('placeholder').style.display    = 'flex';
  document.getElementById('gpuLabel').style.display       = 'none';
  document.getElementById('exLabel').textContent          = '';
  document.getElementById('alertBar').className           = '';
  document.getElementById('alertBar').textContent         = '';
  document.getElementById('fpsPill').textContent          = '-- FPS';
  document.getElementById('fpsPill').className            = '';
  document.getElementById('videoProgress').style.display  = 'none';
}

function tickTimer() {
  if (!sessionStart) return;
  var s = Math.floor((Date.now() - sessionStart) / 1000);
  var m = Math.floor(s / 60);
  document.getElementById('sTime').textContent = m > 0 ? m + 'm' + (s % 60) + 's' : s + 's';
}

var frameCount = 0;
var lastFpsAt  = Date.now();

function tickFPS() {
  frameCount++;
  var now = Date.now();
  if (now - lastFpsAt >= 1000) {
    var fps    = frameCount;
    frameCount = 0;
    lastFpsAt  = now;
    var pill   = document.getElementById('fpsPill');
    pill.textContent = fps + ' FPS';
    pill.className   = fps >= 22 ? 'fast' : fps >= 13 ? 'ok' : 'slow';
  }
}

function saveSession() {
  if (!HIST.length) return;
  try {
    var sessions = JSON.parse(localStorage.getItem('gg_sessions') || '[]');
    var scores   = HIST.map(function(h) { return h.score; });
    sessions.push({
      date: new Date().toLocaleString(),
      avg:  Math.round(scores.reduce(function(a, b) { return a + b; }, 0) / scores.length),
      peak: Math.max.apply(null, scores),
      dur:  sessionStart ? Math.floor((Date.now() - sessionStart) / 1000) : 0,
    });
    if (sessions.length > 50) sessions.shift();
    localStorage.setItem('gg_sessions', JSON.stringify(sessions));
  } catch(e) {}
}