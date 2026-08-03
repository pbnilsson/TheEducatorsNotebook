(function () {
  var input = document.getElementById("q");
  var results = document.getElementById("results");
  var index = null;

  fetch("search-index.json")
    .then(function (r) { return r.json(); })
    .then(function (data) { index = data; run(); });

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function run() {
    if (!index) return;
    var q = input.value.trim().toLowerCase();
    if (q.length < 2) { results.innerHTML = ""; return; }
    var terms = q.split(/\s+/);
    var hits = [];
    for (var i = 0; i < index.length && hits.length < 200; i++) {
      var a = index[i];
      var hay = (a.h + " " + a.p + " " + a.c).toLowerCase();
      var ok = true;
      for (var t = 0; t < terms.length; t++) {
        if (hay.indexOf(terms[t]) === -1) { ok = false; break; }
      }
      if (ok) hits.push(a);
    }
    hits.sort(function (x, y) { return x.d < y.d ? 1 : -1; });
    var out = ["<p class='meta'>" + hits.length + (hits.length === 200 ? "+" : "") + " results</p>"];
    for (var j = 0; j < hits.length; j++) {
      var a = hits[j];
      out.push("<div class='entry'><h4><a href='" + esc(a.l) + "'>" + esc(a.h) + "</a></h4>" +
        "<p class='hit-meta'>" + esc(a.p) + " &middot; <a href='../topics/" + esc(a.s) + "/index.html'>" + esc(a.c) + "</a>" +
        " &middot; <a href='../issues/" + esc(a.d) + "/index.html'>#" + a.n + "</a></p></div>");
    }
    results.innerHTML = out.join("");
  }

  var timer = null;
  input.addEventListener("input", function () {
    clearTimeout(timer); timer = setTimeout(run, 150);
  });
})();
