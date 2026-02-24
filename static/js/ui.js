var ANG_LABEL = {
  left_knee:      'L KNEE',
  right_knee:     'R KNEE',
  left_elbow:     'L ELBOW',
  right_elbow:    'R ELBOW',
  spine:          'SPINE',
  hip_hinge:      'HIP',
  neck_offset:    'NECK',
  L_elbow_flare:  'L FLARE',
  R_elbow_flare:  'R FLARE',
  left_curl:      'L CURL',
  right_curl:     'R CURL',
};

// ── Voice Alerts ─────────────────────────────────────────────────────────────
var _lastSpoken   = '';
var _lastSpokenAt = 0;

function speak(msg) {
  var now = Date.now();
  if (msg === _lastSpoken && now - _lastSpokenAt < 5000) return;
  _lastSpoken   = msg;
  _lastSpokenAt = now;
  var utterance    = new SpeechSynthesisUtterance(msg);
  utterance.rate   = 1;
  utterance.volume = 1;
  utterance.pitch  = 1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

// ── Main update ───────────────────────────────────────────────────────────────
function updateAnalysis(a) {
  var score = a.risk_score || 0;
  updateGauge(score);
  updateIssues(a.issues || []);
  updateAngles(a.angles || {});
  updateAlert(score, a.issues || []);
  updateStats();
  document.getElementById('exLabel').textContent = a.exercise_detected || '';
}

function updateGauge(score) {
  var CIRC  = 251.3;
  var fill  = document.getElementById('gFill');
  var num   = document.getElementById('gNum');
  var level = document.getElementById('rLevel');
  var desc  = document.getElementById('rDesc');

  fill.style.strokeDashoffset = CIRC - (score / 100) * CIRC;
  num.textContent = score;

  var col, lv, dv;
  if (score < 30) {
    col = '#00e676';
    lv  = 'SAFE';
    dv  = score === 0 ? 'Form looks good -- keep it up.' : 'Minor adjustments may help.';
  } else if (score < 65) {
    col = '#ffd600';
    lv  = 'WARNING';
    dv  = 'Form deviations detected. Reduce load or correct posture.';
  } else {
    col = '#ff1744';
    lv  = 'HIGH RISK';
    dv  = 'Stop and correct your form to prevent injury.';
  }

  fill.style.stroke = col;
  num.style.color   = col;
  level.style.color = col;
  level.textContent = lv;
  desc.textContent  = dv;
}

function updateIssues(issues) {
  var list = document.getElementById('issuesList');
  if (!issues.length) {
    list.innerHTML = '<div class="okMsg">&#10003; No issues detected -- good form</div>';
    return;
  }
  list.innerHTML = issues.map(function(i) {
    return '<div class="issCard">' +
      '<div class="issName">' + i.name + '</div>' +
      '<div class="issMsg">'  + i.message + '</div>' +
      '<div class="sevBar"><div class="sevFill" style="width:' + Math.round(i.severity * 100) + '%"></div></div>' +
      '</div>';
  }).join('');
}

function updateAngles(angles) {
  var grid    = document.getElementById('angleGrid');
  var entries = Object.entries(angles);
  if (!entries.length) {
    grid.innerHTML = '<div class="angleItem"><div class="angleKey">AWAITING</div><div class="angleVal">--</div></div>';
    return;
  }
  grid.innerHTML = entries.slice(0, 6).map(function(kv) {
    return '<div class="angleItem">' +
      '<div class="angleKey">' + (ANG_LABEL[kv[0]] || kv[0].toUpperCase()) + '</div>' +
      '<div class="angleVal">' + Math.round(kv[1]) + '<small>&deg;</small></div>' +
      '</div>';
  }).join('');
}

function updateAlert(score, issues) {
  var bar = document.getElementById('alertBar');

  if (score >= 65 && issues.length) {
    bar.className   = 'danger';
    bar.textContent = '! ' + issues[0].name.toUpperCase() + ' -- ' + issues[0].message;
    speak('Warning. ' + issues[0].name + '. ' + issues[0].message);

  } else if (score >= 30 && issues.length) {
    bar.className   = 'warn';
    bar.textContent = issues[0].name + ' -- Check your form';
    speak('Check your form. ' + issues[0].name);

  } else {
    bar.className   = '';
    bar.textContent = '';
    _lastSpoken     = '';
  }
}

function updateStats() {
  if (!HIST.length) return;
  var scores = HIST.map(function(h) { return h.score; });
  var avg    = Math.round(scores.reduce(function(a, b) { return a + b; }, 0) / scores.length);
  var peak   = Math.max.apply(null, scores);
  document.getElementById('sAvg').textContent  = avg;
  document.getElementById('sPeak').textContent = peak;
}