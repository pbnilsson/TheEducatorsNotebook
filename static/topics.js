/* Topic pages: show the first few articles in each group, then reveal the rest
   in batches. Everything is already in the HTML, so with JavaScript off the
   full list simply renders as normal. */
(function () {
  var INITIAL = 5, STEP = 20;

  document.querySelectorAll('section.group').forEach(function (group) {
    var entries = group.querySelectorAll(':scope > .entry');
    if (entries.length <= INITIAL) return;

    var shown = INITIAL, suffix = group.getAttribute('data-suffix') || 'articles';
    for (var i = INITIAL; i < entries.length; i++) entries[i].hidden = true;

    var line = document.createElement('p');
    line.className = 'more';
    var link = document.createElement('a');
    link.href = '#';
    line.appendChild(link);
    group.appendChild(line);

    function relabel() {
      var left = entries.length - shown;
      link.textContent = left > STEP
        ? 'See ' + STEP + ' more of ' + left + ' ' + suffix
        : 'See ' + left + ' more ' + suffix;
    }

    link.addEventListener('click', function (e) {
      e.preventDefault();
      var end = Math.min(shown + STEP, entries.length);
      for (var i = shown; i < end; i++) entries[i].hidden = false;
      shown = end;
      if (shown >= entries.length) line.remove();
      else relabel();
    });

    relabel();
  });
})();
