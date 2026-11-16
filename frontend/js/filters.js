/* EcoShield — panneau de filtres partagé (variable, échelle, région, période). */
(function () {
  const EC = (window.EC = window.EC || {});
  const boxes = [];
  const SCALES = [["national", "National"], ["province", "Provincial"], ["local", "Local"]];

  const opts = (list, sel) => list.map(([v, l]) => `<option value="${v}"${String(v) === String(sel) ? " selected" : ""}>${l}</option>`).join("");

  EC.clampPeriod = function (o, changed) {
    const [p0, p1] = EC.D.meta.period, min = EC.D.stats.min_years;
    if (o.y1 - o.y0 + 1 >= min) return;
    if (changed === "y0") { o.y1 = Math.min(p1, o.y0 + min - 1); o.y0 = o.y1 - min + 1; } else { o.y0 = Math.max(p0, o.y1 - min + 1); o.y1 = o.y0 + min - 1; }
  };

  function years(from, to) { const a = []; for (let y = from; y <= to; y++) a.push([y, y]); return a; }

  EC.buildFilters = function (container) {
    const D = EC.D, [p0, p1] = D.meta.period;
    container.innerHTML = `
      <div class="field"><label>Variable</label><select data-f="variable">${opts(Object.entries(D.variables).map(([k, v]) => [k, v.name]), EC.state.variable)}</select></div>
      <div class="field"><label>Échelle géographique</label><select data-f="scale">${opts(SCALES, EC.state.scale)}</select></div>
      <div class="field"><label>Région</label><select data-f="region"></select></div>
      <div class="field"><label>Période (années entières)</label><div class="period">
        <select data-f="y0" aria-label="Année de début">${opts(years(p0, p1), EC.state.y0)}</select>
        <select data-f="y1" aria-label="Année de fin">${opts(years(p0, p1), EC.state.y1)}</select></div></div>`;
    container.addEventListener("change", (e) => {
      const f = e.target.dataset.f; if (!f) return; const s = EC.state, val = e.target.value;
      if (f === "variable") s.variable = val;
      else if (f === "scale") { s.scale = val; s.region = EC.regionsOfScale(val)[0].id; }
      else if (f === "region") s.region = val;
      else { s[f] = +val; EC.clampPeriod(s, f); }
      EC.render();
    });
    boxes.push(container); EC.syncFilters();
  };

  EC.syncFilters = function () {
    const s = EC.state;
    boxes.forEach((c) => {
      const set = (f, v) => { const el = c.querySelector(`[data-f="${f}"]`); if (el) el.value = v; };
      set("variable", s.variable); set("scale", s.scale);
      const rs = c.querySelector('[data-f="region"]');
      rs.innerHTML = opts(EC.regionsOfScale(s.scale).map((r) => [r.id, r.name]), s.region);
      set("y0", s.y0); set("y1", s.y1);
    });
  };
})();
