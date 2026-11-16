/* EcoShield — graphiques (Chart.js) : série observée, moyenne mobile 12 mois, ligne de tendance (pente de Sen). */
(function () {
  const EC = (window.EC = window.EC || {});
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const C = { obs: "rgba(57,175,192,.55)", roll: "#173F35", trend: "#202B27", grid: "#E7ECE9", ink: "#66736D" };
  let charts = {};

  function base(unit, labels) {
    return {
      type: "line",
      options: {
        responsive: true, maintainAspectRatio: false, animation: reduce ? false : { duration: 200 },
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { family: "Inter", size: 12 }, color: C.ink } },
          tooltip: { callbacks: { label: (c) => (c.parsed.y == null ? null : `${c.dataset.label} : ${EC.fmt(c.parsed.y, 2)} ${unit}`) } },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: C.ink, maxRotation: 0, autoSkip: false,
                callback(v) { const l = labels[v]; return l && l.endsWith("-01") && +l.slice(0, 4) % 2 === 1 ? l.slice(0, 4) : ""; } } },
          y: { grid: { color: C.grid }, ticks: { color: C.ink }, title: { display: true, text: unit, color: C.ink, font: { family: "Inter", size: 12 } } },
        },
      },
    };
  }

  function mount(id, cfg) {
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(document.getElementById(id), cfg);
  }

  /** Série + tendance pour une variable et une région. */
  EC.trendLine = function (labels, vals, t) {
    if (!t) return labels.map(() => null);
    const ok = []; labels.forEach((l, i) => { if (vals[i] != null) ok.push([+l.slice(0, 4) + (+l.slice(5) - 1) / 12, vals[i]]); });
    const level = ok.reduce((s, p) => s + p[1], 0) / ok.length, tmid = ok.reduce((s, p) => s + p[0], 0) / ok.length;
    return labels.map((l) => level + t.slope * (+l.slice(0, 4) + (+l.slice(5) - 1) / 12 - tmid));
  };

  EC.drawTrend = function (id, o) {
    const cfg = base(o.unit, o.labels);
    cfg.data = { labels: o.labels, datasets: [
      { label: "Observé (mensuel)", data: o.vals, borderColor: C.obs, borderWidth: 1.2, pointRadius: 0, spanGaps: false },
      { label: "Moyenne mobile 12 mois", data: o.roll, borderColor: C.roll, borderWidth: 2.2, pointRadius: 0, spanGaps: false },
      { label: "Tendance (pente de Sen)", data: o.trend, borderColor: C.trend, borderWidth: 2, borderDash: [7, 5], pointRadius: 0 },
    ] };
    mount(id, cfg);
  };

  EC.drawCompare = function (id, o) {
    const cfg = base(o.unit, o.labels);
    cfg.data = { labels: o.labels, datasets: [
      { label: `${o.a.name} (moy. mobile 12 mois)`, data: o.a.roll, borderColor: "#173F35", borderWidth: 2.2, pointRadius: 0 },
      { label: `${o.b.name} (moy. mobile 12 mois)`, data: o.b.roll, borderColor: "#39AFC0", borderWidth: 2.2, pointRadius: 0 },
      { label: `${o.a.name} — tendance`, data: o.a.trend, borderColor: "#173F35", borderWidth: 1.6, borderDash: [7, 5], pointRadius: 0 },
      { label: `${o.b.name} — tendance`, data: o.b.trend, borderColor: "#39AFC0", borderWidth: 1.6, borderDash: [7, 5], pointRadius: 0 },
    ] };
    mount(id, cfg);
  };
})();
