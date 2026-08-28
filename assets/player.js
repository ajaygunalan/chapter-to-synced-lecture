/* Audio-synced slides. audio.currentTime is the only clock; the current
 * frame is derived from it on every animation tick. With audio:null it is a
 * manual stepper. Contract: references/sync-architecture.md.
 *
 * Navigation moves the position; Play decides whether sound comes out:
 * ← → step frames (seek, never auto-play), Space play/pause, Shift+← → ±10 s,
 * F fullscreen, 1–9 parts. An ask pauses the audio; Play resumes. */
function createSyncedPlayer(o) {
  function nonEmpty(a) { return a && a.length ? a : null; }
  function lastAt(arr, t) {            // index of the last element with .t <= t
    var lo = 0, hi = arr.length - 1;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (arr[mid].t <= t) lo = mid; else hi = mid - 1; }
    return lo;
  }
  var frames = nonEmpty(o.frames) || [{}],
      audio  = o.audio || null,
      beats  = audio ? nonEmpty(o.beats) : null,
      subs   = audio ? nonEmpty(o.subs) : null,
      asks   = audio && nonEmpty(o.questions) ? o.questions.slice().sort(function (a, b) { return a.t - b.t; }) : null,
      timeline = !!beats,
      last   = frames.length - 1,
      single = frames.length <= 1,
      idx = -1, beatIdx = -1, litTick = null, rafId = null;

  // ---- derived timeline: one row per (beat, frame) with its start time ----
  // A beat runs from its start frame up to the next beat's start frame; a
  // beat with frame:null holds. Rows are sorted by time, so playback is a
  // cursor walk and seeking is a binary search.
  var rows = [];
  if (beats) {
    var cur = 0;
    beats.forEach(function (b, k) {
      var a, z;
      if (b.frame == null) { a = z = cur; }
      else {
        a = b.frame; z = last;
        for (var j = k + 1; j < beats.length; j++) if (beats[j].frame != null) { z = Math.max(a, beats[j].frame - 1); break; }
        if (z > last) { console.warn('beat ' + b.id + ' reaches frame ' + z + ' but only ' + frames.length + ' exist'); z = last; }
      }
      var n = z - a + 1, span = (b.end || b.t) - b.t;
      for (var s = a; s <= z; s++) rows.push({ t: b.t + span * (s - a) / n, frame: s, beat: k });
      cur = z;
    });
  }
  function rowAt(t) { return rows[lastAt(rows, t)]; }
  function timeOfFrame(i) {
    for (var r = 0; r < rows.length; r++) if (rows[r].frame === i) return rows[r].t;
    return 0;
  }
  function nameOf(i) { return frames[i].label || ('Step ' + (i + 1)); }

  // ---- transport --------------------------------------------------------
  function btn(label, fn, title) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'btn'; b.textContent = label; b.onclick = fn;
    if (title) b.title = title;
    o.mount.appendChild(b);
    return b;
  }
  function skip(d) { seek(Math.max(0, Math.min(audio.duration || 1e9, audio.currentTime + d))); }
  var prev = btn('◀', function () { step(-1); }, 'Previous slide (←)');
  if (audio) btn('−10s', function () { skip(-10); }, 'Shift+←');
  var play = btn(audio ? '▶ Play' : 'Next', toggle, 'Space');
  play.className = 'btn primary';
  if (audio) btn('+10s', function () { skip(10); }, 'Shift+→');
  var next = btn('▶', function () { step(1); }, 'Next slide (→)');
  var again = btn('Restart', function () { audio ? seek(0) : show(0); });
  var scrub = null, clock = null, scrubbing = false, lastClock = '', lastScrub = -1;
  if (audio) {
    scrub = document.createElement('input');
    scrub.type = 'range'; scrub.min = 0; scrub.max = 1000; scrub.value = 0; scrub.step = 1;
    scrub.className = 'scrub';
    scrub.setAttribute('aria-label', 'Seek');
    scrub.addEventListener('input', function () {
      scrubbing = true;
      if (audio.duration) seek(audio.duration * scrub.value / 1000);
    });
    scrub.addEventListener('change', function () { scrubbing = false; });
    clock = document.createElement('span');
    clock.className = 'clock';
    clock.textContent = '0:00 / –:––';
    var bar = document.createElement('div');
    bar.className = 'seekbar';
    bar.appendChild(scrub); bar.appendChild(clock);
    o.mount.parentNode.insertBefore(bar, o.mount);
    audio.addEventListener('loadedmetadata', function () { showClock(audio.currentTime); });
    var speed = document.createElement('select');
    speed.className = 'btn';
    speed.setAttribute('aria-label', 'Playback speed');
    [['0.85', 'Slow'], ['1', 'Steady'], ['1.25', 'Quick'], ['1.5', 'Fast']].forEach(function (s) {
      var op = document.createElement('option');
      op.value = s[0]; op.textContent = s[1]; op.selected = s[0] === '1';
      speed.appendChild(op);
    });
    speed.onchange = function () { audio.playbackRate = +speed.value; };
    o.mount.appendChild(speed);
  }
  function fmt(s) { s = Math.max(0, Math.round(s || 0)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function showClock(t) {
    if (!audio) return;
    if (audio.duration && !scrubbing) {
      var v = Math.round(1000 * t / audio.duration);
      if (v !== lastScrub) { lastScrub = v; scrub.value = v; }
    }
    var text = fmt(t) + ' / ' + fmt(audio.duration);
    if (text !== lastClock) { lastClock = text; clock.textContent = text; }
  }
  var counter = document.createElement('span');
  counter.className = 'counter';
  o.mount.appendChild(counter);
  if (single && !audio) { prev.hidden = next.hidden = again.hidden = play.hidden = true; counter.textContent = 'narration not built yet'; }

  // slide number, drawn on the slide itself (or, without a slide element, beside the transport)
  var frameNo = document.createElement('span');
  frameNo.className = 'frame-no';
  (o.slide || o.mount).appendChild(frameNo);

  var ribbon = o.ribbon || document.createElement('div');
  ribbon.className = 'ribbon';
  if (!o.ribbon) o.mount.parentNode.insertBefore(ribbon, o.mount.nextSibling);
  ribbon.hidden = single;
  var ticks = frames.map(function (s, i) {
    var t = document.createElement('button');
    t.type = 'button';
    t.className = 'tick' + (s.tone ? ' t-' + s.tone : '');
    t.title = nameOf(i);
    t.setAttribute('aria-label', nameOf(i) + ' (' + (i + 1) + ' of ' + frames.length + ')');
    t.onclick = function () { goto(i); };
    ribbon.appendChild(t);
    return t;
  });

  // ---- captions: caption bar under the slide, transcript given to the page -----
  // subs: [{t, end, text, words: [[t, word], …]}] from cues/<part>.json.
  var caption = null, transcript = null, subEls = [], subIdx = -1, wordIdx = -1, userScrolledAt = 0;
  if (subs) {
    caption = document.createElement('div');
    caption.className = 'caption';
    caption.setAttribute('aria-live', 'off');
    ribbon.parentNode.insertBefore(caption, ribbon.nextSibling);
    transcript = document.createElement('div');
    transcript.className = 'transcript';
    transcript.setAttribute('role', 'list');
    subEls = subs.map(function (s) {
      var p = document.createElement('p');
      p.className = 'sub';
      p.setAttribute('role', 'listitem');
      p.textContent = s.text;
      p.onclick = function () { seek(s.t); if (audio.paused) audio.play(); };
      transcript.appendChild(p);
      return p;
    });
    transcript.addEventListener('wheel', function () { userScrolledAt = Date.now(); }, { passive: true });
    transcript.addEventListener('touchmove', function () { userScrolledAt = Date.now(); }, { passive: true });
  }
  function showSub(t) {
    if (!subs) return;
    var i = lastAt(subs, t), s = subs[i];
    if (i !== subIdx) {
      if (subIdx >= 0) subEls[subIdx].classList.remove('is-now');
      subIdx = i; wordIdx = -1;
      subEls[i].classList.add('is-now');
      caption.innerHTML = '';
      s.words.forEach(function (w) {
        var span = document.createElement('span');
        span.className = 'w';
        span.textContent = w[1];
        caption.appendChild(span);
        caption.appendChild(document.createTextNode(' '));
      });
      if (transcript.offsetParent && Date.now() - userScrolledAt > 4000) {
        var el = subEls[i], top = el.offsetTop - transcript.offsetTop;
        if (top < transcript.scrollTop || top + el.offsetHeight > transcript.scrollTop + transcript.clientHeight)
          transcript.scrollTo({ top: top - transcript.clientHeight * 0.3, behavior: 'smooth' });
      }
    }
    var k = -1;
    for (var j = 0; j < s.words.length; j++) if (s.words[j][0] <= t) k = j;
    if (k !== wordIdx) {
      wordIdx = k;
      var ws = caption.children;
      for (var j2 = 0; j2 < ws.length; j2++) {
        ws[j2].classList.toggle('is-said', j2 < k);
        ws[j2].classList.toggle('is-cur', j2 === k);
      }
    }
  }

  // ---- asks: the audio stops on the question; the listener thinks; Play resumes -----
  var askCard = null, askOpen = null, asked = {}, lastT = 0;
  if (asks) {
    askCard = document.createElement('div');
    askCard.className = 'ask';
    askCard.hidden = true;
    (o.slide || o.mount).appendChild(askCard);   // on the slide, or beside the transport
  }
  function openAsk(q) {
    askOpen = q;
    audio.pause();
    askCard.textContent = q.prompt || '';
    askCard.hidden = false;
  }
  function closeAsk() {
    if (!askOpen) return;
    asked[askOpen.id] = true;
    askOpen = null;
    askCard.hidden = true;
  }
  function checkAsks(t) {              // called only while playing: crossing q.t forward opens it
    if (!asks || askOpen) { lastT = t; return; }
    for (var i = 0; i < asks.length; i++) {
      var q = asks[i];
      if (!asked[q.id] && lastT < q.t && t >= q.t) { lastT = t; openAsk(q); return; }
    }
    lastT = t;
  }

  // ---- rendering --------------------------------------------------------
  function show(i, b) {
    i = Math.max(0, Math.min(last, i));
    if (i !== idx) {
      idx = i;
      o.render(frames[i]);
      frameNo.textContent = (i + 1) + ' / ' + frames.length;
      if (!single) counter.textContent = nameOf(i);
      if (litTick) litTick.classList.remove('is-now');
      litTick = ticks[i]; litTick.classList.add('is-now');
      if (!audio) { prev.disabled = i === 0; next.disabled = i === last; }
    }
    if (o.onBeat && b !== undefined && b !== beatIdx) { beatIdx = b; o.onBeat(beats[b]); }
  }
  function sync(t) { if (timeline) { var r = rowAt(t); show(r.frame, r.beat); } showSub(t); showClock(t); }
  function seek(t) { closeAsk(); audio.currentTime = t; lastT = t; sync(t); }
  function goto(i) { timeline ? seek(timeOfFrame(i)) : show(i); }
  function step(dir) { goto(Math.max(0, Math.min(last, idx + dir))); }
  function toggle() {
    if (!audio) return show(idx + 1);
    if (askOpen) { closeAsk(); audio.play(); return; }   // Play after a question brings the answer
    audio.paused ? audio.play() : audio.pause();
  }
  function tick() { var t = audio.currentTime; sync(t); checkAsks(t); rafId = requestAnimationFrame(tick); }

  if (audio) {
    audio.addEventListener('play', function () { play.textContent = '❚❚ Pause'; if (!rafId) rafId = requestAnimationFrame(tick); });
    audio.addEventListener('pause', function () { play.textContent = askOpen ? '▶ Answer' : '▶ Resume'; cancelAnimationFrame(rafId); rafId = null; });
    audio.addEventListener('ended', function () { play.textContent = '▶ Play'; });
  }
  // keys act only while this part's panel is visible and focus is not in a field
  if (o.keys !== false) {
    document.addEventListener('keydown', function (ev) {
      if (o.mount.offsetParent === null) return;
      var tag = (ev.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || ev.metaKey || ev.ctrlKey || ev.altKey) return;
      if (ev.key === ' ') { ev.preventDefault(); toggle(); }
      else if (ev.key === 'ArrowLeft') { ev.preventDefault(); ev.shiftKey && audio ? skip(-10) : step(-1); }
      else if (ev.key === 'ArrowRight') { ev.preventDefault(); ev.shiftKey && audio ? skip(10) : step(1); }
    });
  }
  timeline ? sync(0) : show(0);

  return {
    stop: function () { if (audio) audio.pause(); cancelAnimationFrame(rafId); rafId = null; },
    goto: goto,       // frame index (a time on the timeline, a step without audio)
    seek: seek,
    step: step,       // ±1 frame
    toggle: toggle,   // play/pause (or next frame without audio)
    element: ribbon,
    transcript: transcript   // the page (createLecture) places it behind the Transcript tab
  };
}

/* The page: one player per part, the tabs (parts + Transcript), the
 * #part:frame hash, fullscreen, and the audio/cues wiring. Pages supply
 * frames and render only.
 *   createLecture({ parts: [{ key, frames, render, name?, tab?, onBeat? }, …],
 *                   tabs?: element (default .tabs; null for none) })
 *   -> { players: {key: player}, activate(key, frame?) } */
function createLecture(o) {
  var cues = (typeof window.LECTURE_CUES === 'object' && window.LECTURE_CUES) || {};
  var tabs = o.tabs === undefined ? document.querySelector('.tabs') : o.tabs;
  var players = {}, entries = [], active = null, reading = false;

  o.parts.forEach(function (m) {
    var section = document.querySelector('[data-part=' + JSON.stringify(m.key) + ']');
    if (!section) { console.warn('no panel for part ' + m.key); return; }
    var mount = section.querySelector('.transport');
    if (!mount) { mount = document.createElement('div'); mount.className = 'transport'; section.appendChild(mount); }
    var c = cues[m.key], audio = null;
    if (c && c.beats && c.beats.length) { audio = new Audio(c.audio || 'audio/' + m.key + '.mp3'); audio.preload = 'metadata'; }
    players[m.key] = createSyncedPlayer({
      frames: m.frames, render: m.render, onBeat: m.onBeat, mount: mount, audio: audio,
      slide: section.querySelector('.slide'),
      beats: c && c.beats, subs: c && c.subs, questions: c && c.questions
    });
    var tab = null;
    if (tabs) {
      tab = document.createElement('button');
      tab.type = 'button'; tab.setAttribute('role', 'tab'); tab.setAttribute('aria-selected', 'false');
      if (m.tab) tab.innerHTML = m.tab; else tab.textContent = m.name || m.key;
      tab.onclick = function () { activate(m.key); };
      tabs.appendChild(tab);
    }
    entries.push({ key: m.key, section: section, tab: tab });
  });

  // the Transcript tab: the active part's sentences, click to jump; audio keeps playing
  var panel = document.createElement('section');
  panel.className = 'transcript-panel';
  panel.hidden = true;
  var readTab = null;
  if (tabs && entries.some(function (e) { return players[e.key].transcript; })) {
    readTab = document.createElement('button');
    readTab.type = 'button'; readTab.className = 'tab-transcript'; readTab.setAttribute('role', 'tab'); readTab.textContent = 'Transcript';
    readTab.onclick = function () { showReading(!reading); };
    tabs.appendChild(readTab);
    tabs.parentNode.insertBefore(panel, tabs.nextSibling);
  }
  function showReading(on) {
    reading = on;
    entries.forEach(function (e) { e.section.classList.toggle('is-active', !on && e.key === active); });
    panel.hidden = !on;
    if (readTab) readTab.setAttribute('aria-selected', on ? 'true' : 'false');
    if (on) {
      panel.innerHTML = '';
      var tr = players[active] && players[active].transcript;
      if (tr) panel.appendChild(tr);
    }
  }

  function activate(key, frame) {
    if (active !== key) {
      entries.forEach(function (e) {
        var on = e.key === key;
        e.section.classList.toggle('is-active', on);
        if (e.tab) e.tab.setAttribute('aria-selected', on ? 'true' : 'false');
        if (!on) players[e.key].stop();
      });
      active = key;
      try { history.replaceState(null, '', '#' + key); } catch (e) {}
    }
    if (reading) showReading(false);
    if (frame != null && !isNaN(frame)) players[key].goto(+frame);
  }
  function fromHash() {
    var h = (location.hash || '').slice(1).split(':');
    var known = entries.some(function (e) { return e.key === h[0]; });
    if (entries.length) activate(known ? h[0] : entries[0].key, h[1] !== undefined && h[1] !== '' ? +h[1] : null);
  }
  function fullscreen(on) {
    document.body.classList.toggle('is-fullscreen', on);
    if (on && document.documentElement.requestFullscreen && !document.fullscreenElement) document.documentElement.requestFullscreen().catch(function () {});
    if (!on && document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
  }
  document.addEventListener('fullscreenchange', function () { if (!document.fullscreenElement) document.body.classList.remove('is-fullscreen'); });
  window.addEventListener('hashchange', fromHash);
  document.addEventListener('keydown', function (ev) {
    var tag = (ev.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || ev.metaKey || ev.ctrlKey || ev.altKey) return;
    var n = +ev.key;
    if (ev.key.length === 1 && n >= 1 && n <= entries.length) activate(entries[n - 1].key);
    else if (ev.key === 'f' || ev.key === 'F') fullscreen(!document.body.classList.contains('is-fullscreen'));
    else if (ev.key === 'Escape') fullscreen(false);
  });
  fromHash();
  return { players: players, activate: activate, fullscreen: fullscreen };
}

/* Syntax colouring without a library: keywords, types, strings, numbers,
 * comments, calls. highlightCode(text, lang?) -> HTML for a <pre>/<code>.
 * lang: 'cpp' (default) | 'java' | 'python' | 'js'. Teaching marks (.hl,
 * .bad, .good) are the page's own spans, wrapped around lines after this. */
var CODE_WORDS = {
  cpp: { kw: 'if else for while do return break continue switch case default new delete this class struct enum union namespace using template typename public private protected virtual override final const constexpr static inline auto void bool char int long short float double unsigned signed nullptr true false try catch throw operator sizeof friend explicit noexcept mutable',
         ty: 'string vector map set unordered_map unordered_set pair tuple optional array deque queue stack priority_queue function shared_ptr unique_ptr size_t int8_t int16_t int32_t int64_t uint8_t uint16_t uint32_t uint64_t Money Report' },
  java: { kw: 'if else for while do return break continue switch case default new this class interface enum extends implements public private protected static final abstract void boolean char int long short float double byte null true false try catch finally throw throws import package instanceof super synchronized',
          ty: 'String List ArrayList Map HashMap Set HashSet Integer Long Double Boolean Object' },
  python: { kw: 'if elif else for while return break continue def class lambda import from as pass yield with try except finally raise in is not and or None True False global nonlocal async await del assert',
            ty: 'int str list dict set tuple float bool bytes range len print self' },
  js: { kw: 'if else for while do return break continue switch case default new this class extends function var let const typeof instanceof in of null undefined true false try catch finally throw async await import export',
        ty: 'Array Object Map Set Promise Number String Boolean Math JSON console document window' }
};
function highlightCode(text, lang) {
  var w = CODE_WORDS[lang || 'cpp'] || CODE_WORDS.cpp;
  var kw = {}, ty = {};
  w.kw.split(' ').forEach(function (x) { kw[x] = 1; }); w.ty.split(' ').forEach(function (x) { ty[x] = 1; });
  var esc = function (t) { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
  var re = /(\/\/[^\n]*|#[^\n]*|\/\*[\s\S]*?\*\/)|("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(\b\d+(?:\.\d+)?[fFuUlL]*\b)|([A-Za-z_]\w*)(?=\s*\()|([A-Za-z_]\w*)/g;
  var out = '', last = 0, m;
  while ((m = re.exec(text))) {
    out += esc(text.slice(last, m.index));
    var t = m[0], cls = null;
    if (m[1]) cls = (t.charAt(0) === '#' && lang !== 'python') ? 'tok-pp' : 'tok-cm';
    else if (m[2]) cls = 'tok-str';
    else if (m[3]) cls = 'tok-num';
    else if (m[4]) cls = kw[t] ? 'tok-kw' : (ty[t] ? 'tok-ty' : 'tok-fn');
    else if (m[5]) cls = kw[t] ? 'tok-kw' : (ty[t] ? 'tok-ty' : null);
    out += cls ? '<span class="' + cls + '">' + esc(t) + '</span>' : esc(t);
    last = m.index + t.length;
  }
  return out + esc(text.slice(last));
}
