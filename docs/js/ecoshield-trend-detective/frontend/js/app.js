/* EcoShield — application : état, données, navigation et rendu des vues. Aucun résultat statistique n'est calculé ici :
   toutes les tendances proviennent du pipeline Python (results/trends/trends.json). */
(function () {
  const EC = (window.EC = window.EC || {});
  const D = (EC.D = window.ECOSHIELD_DATA);
  const $ = (s, el = document) => el.querySelector(s);
  const [P0, P1] = D.meta.period;
  EC.state = { variable: "T2M", scale: "national", region: "gabon", y0: P0, y1: P1 };
  const cmp = { variable: "T2M", a: "estuaire", b: "haut-ogooue", y0: P0, y1: P1 };
  const MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
  const SUBJ = { T2M: ["la température moyenne", "présente"], PRECTOTCORR: ["les précipitations", "présentent"], BURNED_AREA: ["la surface brûlée", "présente"] };

  /* ── Utilitaires de données ─────────────────────────────────────────── */
  EC.fmt = (x, d = 2) => (x == null || isNaN(x) ? "—" : Number(x).toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d }));
  EC.fmtS = (x, d = 2) => (x == null ? "—" : (x > 0 ? "+" : x < 0 ? "−" : "") + EC.fmt(Math.abs(x), d));
  const fmtP = (p) => (p < 0.001 ? "< 0,001" : EC.fmt(p, 3));
  const pTxt = (p) => (p < 0.001 ? "p < 0,001" : "p = " + EC.fmt(p, 3));
  EC.regionById = (id) => D.regions.find((r) => r.id === id);
  EC.regionsOfScale = (s) => D.regions.filter((r) => r.level === (s === "province" ? "province" : s));
  EC.trend = (v, r, a, b) => {
    const x = D.trends.data[`${v}|${r}|${a}|${b}`]; if (!x) return null;
    const o = {}; D.trends.fields.forEach((k, i) => (o[k] = x[i]));
    return { slope: o.sen_slope, lo: o.ci_low, hi: o.ci_high, z: o.mk_z, p: o.p_value, total: o.total_change, dir: o.direction, r1: o.autocorr_r1, n: o.n_obs, sig: o.p_value < D.stats.alpha };
  };
  EC.series = (v, r, a, b) => {
    const s = D.series[`${v}|${r}`], y0 = +s.start.slice(0, 4), m0 = +s.start.slice(5) - 1, labels = [], vals = [];
    s.v.forEach((x, i) => { const k = i + m0, y = y0 + Math.floor(k / 12), m = (k % 12) + 1; if (y >= a && y <= b) { labels.push(`${y}-${String(m).padStart(2, "0")}`); vals.push(x); } });
    return { labels, vals };
  };
  const rolling = (vals, w = 12) => vals.map((_, i) => { if (i < w - 1) return null; let s = 0, c = 0; for (let k = i - w + 1; k <= i; k++) if (vals[k] != null) { s += vals[k]; c++; } return c >= Math.ceil(w * 0.8) ? s / c : null; });
  const annual = (v, r, y) => {
    const ok = EC.series(v, r, y, y).vals.filter((x) => x != null); const sum = ok.reduce((a, b) => a + b, 0);
    if (v === "T2M") return ok.length >= 10 ? sum / ok.length : null; return ok.length === 12 ? sum : null;
  };
  const annualUnit = (v) => (v === "T2M" ? "°C" : D.variables[v].unit.replace("/mois", "") + "/an");
  const sd = (v) => D.variables[v].decimals;
  const dirChip = (t) => !t ? "" : t.dir === 1 ? '<span class="chip up">↗ Tendance à la hausse</span>' : t.dir === -1 ? '<span class="chip down">↘ Tendance à la baisse</span>' : '<span class="chip none">→ Non détectable</span>';
  const sigChip = (t) => !t ? "" : t.sig ? '<span class="chip sig">Significatif à 5 %</span>' : '<span class="chip nosig">Non significatif à 5 %</span>';
  const resNote = (rid, v) => EC.regionById(rid).reliable[v] ? "" :
    `<div class="info-box warn"><b>Résolution insuffisante pour cette zone.</b> La grille de ${D.variables[v].short.toLowerCase()} (≈ 55 × 70 km) est plus large que la zone : le résultat reflète la maille qui la contient, pas la zone elle-même. Ne pas l'interpréter comme une mesure locale.</div>`;
  const latestLabel = () => { const s = D.series["T2M|gabon"]; const k = (+s.start.slice(5) - 1) + s.v.length - 1; return `${MONTHS[k % 12]} ${+s.start.slice(0, 4) + Math.floor(k / 12)}`; };
  const download = (name, text, type) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000); };

  function interpretation(v, rid, t, a, b) {
    const V = D.variables[v], R = EC.regionById(rid), [subj, verb] = SUBJ[v], d = sd(v);
    const dir = t.dir === 1 ? "une tendance à la hausse" : t.dir === -1 ? "une tendance à la baisse" : "aucune tendance détectable";
    const first = t.dir === 0
      ? `Pour « ${R.name} », sur la période ${a}–${b}, ${subj} ${verb === "présente" ? "ne présente" : "ne présentent"} pas de tendance détectable au seuil de 5 %.`
      : `Pour « ${R.name} », sur la période ${a}–${b}, ${subj} ${verb} ${dir}.`;
    const test = t.sig
      ? `Le test de Mann-Kendall saisonnier indique que cette tendance est significative au seuil de 5 % (${pTxt(t.p)}). La pente de Sen estime l'évolution médiane à ${EC.fmtS(t.slope, d + 1)} ${V.trend_unit} (intervalle de confiance à 95 % : ${EC.fmtS(t.lo, d + 1)} à ${EC.fmtS(t.hi, d + 1)}), soit environ ${EC.fmtS(t.total, d)} ${V.unit} cumulés sur la période.`
      : `Le test de Mann-Kendall saisonnier ne détecte pas de tendance significative au seuil de 5 % (${pTxt(t.p)}). Ce résultat ne prouve pas l'absence de changement : la série peut être trop variable ou trop courte pour le révéler. La pente de Sen reste de ${EC.fmtS(t.slope, d + 1)} ${V.trend_unit} (intervalle de confiance à 95 % : ${EC.fmtS(t.lo, d + 1)} à ${EC.fmtS(t.hi, d + 1)}).`;
    const ac = t.r1 > 1.96 / Math.sqrt(t.n) ? ` Les mois successifs étant corrélés (r₁ = ${EC.fmt(t.r1, 2)}), la variance du test a été corrigée pour éviter de surestimer la significativité.` : "";
    const caveat = `Direction et significativité sont deux informations distinctes ; une hausse n'est pas nécessairement une amélioration, et une corrélation n'est pas une causalité.`;
    return `<p>${first}</p><p>${test}${ac}</p><p class="muted small">${caveat}</p>`;
  }

  function reportText(v, rid, t, a, b) {
    const V = D.variables[v], R = EC.regionById(rid), d = sd(v), m = D.series_meta[`${v}|${rid}`];
    const dir = t.dir === 1 ? "à la hausse" : t.dir === -1 ? "à la baisse" : "non détectable";
    return [`EcoShield — Résumé scientifique simplifié`, D.meta.demo ? `⚠ DONNÉES DE DÉMONSTRATION (synthétiques) — ne pas citer comme mesures` : ``,
      `Variable : ${V.name} (${V.unit})`, `Région : ${R.name} — échelle ${R.level === "province" ? "provinciale" : R.level === "local" ? "locale" : "nationale"}`,
      `Période : ${a}–${b}`, `Source : ${m ? m.source : V.source} — produit ${V.product}`,
      `Tendance : ${dir}`, `Taux d'évolution (pente de Sen) : ${EC.fmtS(t.slope, d + 1)} ${V.trend_unit} (IC 95 % : ${EC.fmtS(t.lo, d + 1)} à ${EC.fmtS(t.hi, d + 1)})`,
      `Variation estimée sur la période : ${EC.fmtS(t.total, d)} ${V.unit}`,
      `Significativité : Mann-Kendall saisonnier, Z = ${EC.fmt(t.z, 2)}, ${pTxt(t.p)} → ${t.sig ? "significatif" : "non significatif"} au seuil de 5 %`,
      `Limites : résolution spatiale : ${V.spatial_resolution} ; la significativité statistique n'est pas l'importance environnementale ; p > 0,05 n'est pas une preuve d'absence de changement ; tests multiples non corrigés.`,
      `Méthode : ${D.stats.method}`, `Généré le ${new Date().toLocaleDateString("fr-FR")}`].filter(Boolean).join("\n");
  }

  /* ── Vues ───────────────────────────────────────────────────────────── */
  function renderOverview() {
    const kp = [["T2M", "Température"], ["PRECTOTCORR", "Précipitations"], ["BURNED_AREA", "Surface brûlée"]].map(([v, l]) => {
      const t = EC.trend(v, "gabon", P0, P1), V = D.variables[v];
      return `<div class="kpi"><div class="v">${t ? EC.fmtS(t.slope, sd(v) + 1) : "—"}<small>${V.trend_unit}</small></div><div class="l">${l}, Gabon, ${P0}–${P1}</div><div class="chips">${dirChip(t)}${sigChip(t)}</div></div>`;
    }).join("");
    const provs = EC.regionsOfScale("province"), up = provs.filter((r) => { const t = EC.trend("T2M", r.id, P0, P1); return t && t.dir === 1; }).length;
    $("#ovKpis").innerHTML = kp + `<div class="kpi"><div class="v">${up}<small>sur ${provs.length}</small></div><div class="l">provinces en hausse significative de température</div></div>`;
    $("#ovMapPeriod").textContent = `${P0}–${P1}`;
    $("#ovLegend").innerHTML = EC.legendHTML();
    $("#ovProvinces").innerHTML = provs.map((r) => `<button class="chip" data-region="${r.id}">${r.name}</button>`).join("");
    $("#ovVars").innerHTML = Object.entries(D.variables).map(([k, V]) => `<div class="var-item"><i data-lucide="${V.icon}"></i><div><b>${V.name}</b><span>${V.unit} · ${V.source}</span></div></div>`).join("");
    $("#ovLatest").textContent = `Dernier mois de données disponible : ${latestLabel()}.`;
    if (!EC.maps.overview) EC.maps.overview = EC.createMap("mapOverview", { fixedVar: "T2M", onSelect: (id) => { EC.state.scale = "province"; EC.state.region = id; location.hash = "explore"; } });
    EC.maps.overview.update(); EC.maps.overview.fit();
  }

  function renderExplore() {
    const s = EC.state, V = D.variables[s.variable], R = EC.regionById(s.region), t = EC.trend(s.variable, s.region, s.y0, s.y1);
    $("#varCard").innerHTML = `<b>${V.name}</b><br>${V.definition}<br><span class="muted">Unité : ${V.unit} · Source : ${V.source} (${V.product}) · Résolution spatiale : ${V.spatial_resolution} · Résolution temporelle : ${V.temporal_resolution} · Disponible : ${P0}–${P1}</span>`;
    $("#regionInfo").innerHTML = `<b>${R.name}</b> <span class="muted">· ≈ ${R.area_km2_approx.toLocaleString("fr-FR")} km²</span><div class="chips" style="margin-top:8px">${t ? dirChip(t) + sigChip(t) : '<span class="chip none">Série insuffisante</span>'}</div>${t ? `<div style="margin-top:8px">${EC.fmtS(t.slope, sd(s.variable) + 1)} ${V.trend_unit}</div>` : ""}`;
    $("#regionInfo").insertAdjacentHTML("beforeend", resNote(s.region, s.variable));
    $("#legend").innerHTML = EC.legendHTML();
    $("#exMapTitle").textContent = `${V.short} — tendance par province`; $("#exMapSub").textContent = `${s.y0}–${s.y1} · cliquez sur une province ou une zone`;
    if (!EC.maps.explore) EC.maps.explore = EC.createMap("mapExplore", { showLocal: true, onSelect: (id, lvl) => { EC.state.scale = lvl; EC.state.region = id; EC.render(); } });
    EC.maps.explore.map.invalidateSize(); EC.maps.explore.update(); if (!EC.maps.explore._fit) { EC.maps.explore.fit(); EC.maps.explore._fit = true; }
  }

  function renderTrends() {
    const s = EC.state, v = s.variable, V = D.variables[v], R = EC.regionById(s.region), d = sd(v), t = EC.trend(v, s.region, s.y0, s.y1), body = $("#trendBody");
    const m = D.series_meta[`${v}|${s.region}`], ser = EC.series(v, s.region, s.y0, s.y1), missing = ser.vals.filter((x) => x == null).length;
    const head = `<div class="t-head"><h1>${V.name} — ${R.name}</h1><div class="t-meta"><span>Échelle : <b>${R.level === "province" ? "provinciale" : R.level === "local" ? "locale" : "nationale"}</b></span><span>Période : <b>${s.y0}–${s.y1}</b></span><span>Source : <b>${V.source}</b></span><span>Unité : <b>${V.unit}</b></span></div></div>`;
    if (!t) { body.innerHTML = head + `<div class="card empty"><h3>Tendance non calculable</h3><p>La série est trop courte ou trop incomplète sur cette période (minimum ${D.stats.min_years} ans avec des mois valides). Élargissez la période.</p></div>`; return; }
    const a0 = annual(v, s.region, s.y0), a1 = annual(v, s.region, s.y1), au = annualUnit(v), lab = v === "T2M" ? "Moyenne annuelle" : "Cumul annuel";
    const kpi = (val, small, l, extra = "") => `<div class="kpi"><div class="v">${val}${small ? `<small>${small}</small>` : ""}</div><div class="l">${l}</div>${extra}</div>`;
    const kpis = `<div class="kpis kpis-5">${kpi(EC.fmt(a0, d), au, `${lab} ${s.y0}` + (a0 == null ? " (année incomplète)" : ""))}${kpi(EC.fmt(a1, d), au, `${lab} ${s.y1}` + (a1 == null ? " (année incomplète)" : ""))}${kpi(EC.fmtS(t.total, d), V.unit, "Variation estimée sur la période (pente de Sen × durée)")}${kpi(EC.fmtS(t.slope, d + 1), V.trend_unit, "Taux de changement (pente de Sen)")}<div class="kpi"><div class="l" style="margin:0 0 6px">Direction et significativité</div><div class="chips">${dirChip(t)}${sigChip(t)}</div></div></div>`;
    const infl = t.r1 > 1.96 / Math.sqrt(t.n) ? ` — variance corrigée (×${EC.fmt((1 + t.r1) / (1 - t.r1), 1)})` : " — pas de correction nécessaire";
    const stats = `<table><tbody>
      <tr><th>Test</th><td>Mann-Kendall saisonnier</td></tr><tr><th>Statistique Z</th><td class="n">${EC.fmt(t.z, 2)}</td></tr><tr><th>P-value</th><td class="n">${fmtP(t.p)}</td></tr>
      <tr><th>Pente de Sen</th><td class="n">${EC.fmtS(t.slope, d + 1)} ${V.trend_unit}</td></tr><tr><th>Intervalle de confiance 95 %</th><td class="n">${EC.fmtS(t.lo, d + 1)} à ${EC.fmtS(t.hi, d + 1)}</td></tr>
      <tr><th>Autocorrélation r₁</th><td>${EC.fmt(t.r1, 2)}${infl}</td></tr><tr><th>Observations valides</th><td class="n">${t.n} sur ${ser.vals.length}</td></tr>
      <tr><th>Seuil</th><td class="n">5 %</td></tr></tbody></table>
      <div class="chips" style="margin-top:12px">${t.sig ? "<span class='chip sig'>Conclusion : tendance significative</span>" : "<span class='chip nosig'>Conclusion : non significatif — pas une preuve d'absence de changement</span>"}</div>`;
    const missTxt = missing ? `${missing} mois manquant${missing > 1 ? "s" : ""} sur ${ser.vals.length} (interruptions de la courbe : non comptés comme zéro).` : "Aucun mois manquant sur la période.";
    const src = `Source : ${m ? m.source : V.source} · produit ${V.product} · ${V.spatial_resolution} · agrégation : ${V.aggregation} ${missTxt}`;
    body.innerHTML = head + `<div class="stack">${resNote(s.region, v)}</div>${kpis}
      <div class="t-grid"><div class="card"><h3>Évolution dans le temps</h3><div class="chart-wrap"><canvas id="trendCanvas" role="img" aria-label="Série temporelle de ${V.name} pour ${R.name}"></canvas></div><p class="foot">${src}</p></div>
      <div class="card"><h3>Résultats statistiques</h3>${stats}</div></div>
      <div class="card interp" style="margin-bottom:24px"><h3>Interprétation</h3>${interpretation(v, s.region, t, s.y0, s.y1)}</div>
      <div class="card report"><h3>Résumé scientifique simplifié</h3><pre id="reportTxt"></pre><div class="hero-actions"><button class="btn btn-secondary btn-sm" id="cpBtn">Copier le résumé</button><button class="btn btn-secondary btn-sm" id="dlTxt">Télécharger (.txt)</button><button class="btn btn-secondary btn-sm" id="dlCsv">Télécharger la série (.csv)</button></div></div>`;
    $("#reportTxt").textContent = reportText(v, s.region, t, s.y0, s.y1);
    $("#cpBtn").onclick = () => navigator.clipboard && navigator.clipboard.writeText($("#reportTxt").textContent);
    $("#dlTxt").onclick = () => download(`ecoshield_${v}_${s.region}_${s.y0}-${s.y1}.txt`, $("#reportTxt").textContent, "text/plain");
    $("#dlCsv").onclick = () => download(`ecoshield_${v}_${s.region}_${s.y0}-${s.y1}.csv`, "date,value\n" + ser.labels.map((l, i) => `${l}-01,${ser.vals[i] == null ? "" : ser.vals[i]}`).join("\n"), "text/csv");
    EC.drawTrend("trendCanvas", { labels: ser.labels, vals: ser.vals, roll: rolling(ser.vals), trend: EC.trendLine(ser.labels, ser.vals, t), unit: V.unit });
  }

  function buildCompareControls() {
    const el = $("#compareControls"), all = D.regions.map((r) => `<option value="${r.id}">${r.name}</option>`).join("");
    const yrs = (sel) => { let o = ""; for (let y = P0; y <= P1; y++) o += `<option${y === sel ? " selected" : ""}>${y}</option>`; return o; };
    el.innerHTML = `<div class="field"><label>Variable</label><select data-c="variable">${Object.entries(D.variables).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join("")}</select></div>
      <div class="field"><label>Territoire A</label><select data-c="a">${all}</select></div><div class="field"><label>Territoire B</label><select data-c="b">${all}</select></div>
      <div class="field"><label>Période commune</label><div class="period"><select data-c="y0">${yrs(cmp.y0)}</select><select data-c="y1">${yrs(cmp.y1)}</select></div></div>`;
    const sync = () => Object.keys(cmp).forEach((k) => { const e = el.querySelector(`[data-c="${k}"]`); if (e) e.value = cmp[k]; });
    el.addEventListener("change", (e) => { const k = e.target.dataset.c; if (!k) return; cmp[k] = isNaN(+e.target.value) || ["variable", "a", "b"].includes(k) ? e.target.value : +e.target.value; if (k === "y0" || k === "y1") EC.clampPeriod(cmp, k); sync(); renderCompare(); });
    sync();
  }

  function renderCompare() {
    const v = cmp.variable, V = D.variables[v], d = sd(v), A = EC.regionById(cmp.a), B = EC.regionById(cmp.b), body = $("#compareBody");
    if (cmp.a === cmp.b) { body.innerHTML = `<div class="card empty"><h3>Choisissez deux territoires différents</h3><p>La comparaison porte sur une même variable, sur une période commune.</p></div>`; return; }
    const tA = EC.trend(v, cmp.a, cmp.y0, cmp.y1), tB = EC.trend(v, cmp.b, cmp.y0, cmp.y1), sA = EC.series(v, cmp.a, cmp.y0, cmp.y1), sB = EC.series(v, cmp.b, cmp.y0, cmp.y1);
    const card = (R, t, col) => `<div class="card"><div class="name"><span class="dot" style="background:${col}"></span><h3 style="margin:0">${R.name}</h3></div>${t ? `<div class="kpi" style="box-shadow:none;margin-bottom:12px"><div class="v">${EC.fmtS(t.slope, d + 1)}<small>${V.trend_unit}</small></div><div class="l">Pente de Sen · IC 95 % : ${EC.fmtS(t.lo, d + 1)} à ${EC.fmtS(t.hi, d + 1)}</div></div>
      <table><tbody><tr><th>Variation estimée</th><td class="n">${EC.fmtS(t.total, d)} ${V.unit}</td></tr><tr><th>P-value</th><td class="n">${fmtP(t.p)}</td></tr></tbody></table><div class="chips" style="margin-top:12px">${dirChip(t)}${sigChip(t)}</div>` : "<p class='muted'>Série insuffisante.</p>"}${resNote(R.id, v)}</div>`;
    let synth = "<p>Comparaison impossible : une des séries est insuffisante.</p>";
    if (tA && tB) {
      const diff = tA.slope - tB.slope, overlap = !(tA.hi < tB.lo || tB.hi < tA.lo);
      synth = `<p>Pente de Sen : <b>${A.name}</b> ${EC.fmtS(tA.slope, d + 1)} contre <b>${B.name}</b> ${EC.fmtS(tB.slope, d + 1)} ${V.trend_unit}, soit un écart A − B de ${EC.fmtS(diff, d + 1)} ${V.trend_unit}.</p>
        <p>${overlap ? "Les intervalles de confiance à 95 % se recouvrent : l'écart entre les deux territoires n'est pas établi." : "Les intervalles de confiance à 95 % sont disjoints : les deux pentes diffèrent nettement (lecture indicative)."}</p>
        <p class="muted small">Même variable, même période, même méthode d'agrégation et mêmes unités pour les deux territoires. Les p-values ne sont pas corrigées des tests multiples : plusieurs comparaisons augmentent le risque de faux positifs.${v === "BURNED_AREA" ? " La surface brûlée est un total : elle dépend aussi de la taille du territoire." : ""}</p>`;
    }
    body.innerHTML = `<div class="card" style="margin-bottom:24px"><h3>${V.name} — ${A.name} et ${B.name}, ${cmp.y0}–${cmp.y1}</h3><div class="chart-wrap"><canvas id="cmpCanvas" role="img" aria-label="Comparaison de ${V.name}"></canvas></div><p class="foot">Source : ${V.source} (${V.product}) · ${V.spatial_resolution} · unité : ${V.unit}</p></div>
      <div class="cmp-grid">${card(A, tA, "#173F35")}${card(B, tB, "#39AFC0")}</div><div class="card interp"><h3>Synthèse des différences</h3>${synth}</div>`;
    EC.drawCompare("cmpCanvas", { labels: sA.labels, unit: V.unit, a: { name: A.name, roll: rolling(sA.vals), trend: EC.trendLine(sA.labels, sA.vals, tA) }, b: { name: B.name, roll: rolling(sB.vals), trend: EC.trendLine(sB.labels, sB.vals, tB) } });
  }

  function renderMethods() {
    const vars = Object.values(D.variables).map((V) => `<div class="card" style="margin-bottom:16px"><h3>${V.name}</h3><table><tbody>
      <tr><th>Définition</th><td>${V.definition}</td></tr><tr><th>Unité</th><td>${V.unit}</td></tr><tr><th>Source / produit</th><td>${V.source} — ${V.product}</td></tr>
      <tr><th>Résolution temporelle</th><td>${V.temporal_resolution}</td></tr><tr><th>Résolution spatiale</th><td>${V.spatial_resolution}</td></tr><tr><th>Période</th><td>${P0}–${P1}</td></tr>
      <tr><th>Agrégation</th><td>${V.aggregation}</td></tr><tr><th>Priorité MVP</th><td>${V.priority === 1 ? "Priorité 1" : "Priorité 2 (après validation de la chaîne de traitement)"}</td></tr></tbody></table></div>`).join("");
    const rows = Object.values(D.series_meta).map((m) => `<tr><td>${m.variable}</td><td>${EC.regionById(m.region).name}</td><td>${m.product}</td><td>${m.period[0]} → ${m.period[1]}</td><td>${new Date(m.retrieved_at).toLocaleDateString("fr-FR")}</td><td class="n">${m.n_missing}</td></tr>`).join("");
    const geo = Object.entries(D.meta.geo_provenance).map(([k, p]) => `<tr><td>${k}</td><td>${p ? p.source : "—"}</td><td>${p ? p.crs : "—"}</td><td>${p && p.demo ? "démonstration (schématique)" : "officielle"}</td></tr>`).join("");
    $("#methodsBody").innerHTML = `<div class="card" style="margin-bottom:16px"><h1>Data &amp; Methods</h1>
      <p class="lead">Chaque graphique renvoie à sa source et à sa méthode. Statut des données : <b>${D.meta.demo ? "démonstration (synthétiques)" : "réelles"}</b>. Dernière actualisation : ${new Date(D.meta.generated_at).toLocaleString("fr-FR")}.</p>
      <h3>Méthodes statistiques</h3><ul><li><b>Mann-Kendall saisonnier</b> : détecte une tendance monotone en comparant les années entre elles, mois par mois, ce qui neutralise la saisonnalité.</li>
      <li><b>Pente de Sen</b> : estime le taux d'évolution (médiane des pentes entre paires), avec un intervalle de confiance à 95 %.</li>
      <li><b>Autocorrélation</b> : la variance du test est corrigée par la taille d'échantillon effective lorsque l'autocorrélation d'ordre 1 est positive et significative (approximation).</li>
      <li><b>Seuil</b> : 5 %. Périodes d'au moins ${D.stats.min_years} années entières. Les séries insuffisantes ne produisent aucun résultat.</li></ul>
      <h3>Limites à garder en tête</h3><ul><li>La significativité statistique n'est pas l'importance environnementale du changement ; une p-value &gt; 0,05 n'est pas une preuve d'absence de changement.</li>
      <li>Une limite administrative ne garantit pas une analyse fiable : la température et les précipitations (grille ≈ 55 × 70 km) ne décrivent pas précisément une zone locale.</li>
      <li>Les comparaisons multiples (provinces × variables) augmentent le risque de faux positifs ; aucune correction n'est appliquée dans cette version.</li>
      <li>Une tendance positive n'est pas une amélioration environnementale. Une corrélation n'est pas une causalité.</li>
      <li>Précipitations : l'API fournit des mm/jour moyens, convertis en cumul mensuel (× nombre de jours du mois).</li>
      <li>Les données manquantes sont conservées comme manquantes, jamais remplacées par zéro ; les pixels MODIS invalides ne sont pas comptés comme non brûlés.</li></ul></div>
      ${vars}
      <div class="card"><h3>Limites administratives</h3><div class="tbl-scroll"><table><thead><tr><th>Fichier</th><th>Source</th><th>Système de coordonnées</th><th>Statut</th></tr></thead><tbody>${geo}</tbody></table></div>
      <details><summary>Traçabilité des 36 séries</summary><div class="tbl-scroll"><table><thead><tr><th>Variable</th><th>Région</th><th>Produit</th><th>Période</th><th>Récupérée le</th><th>Mois manquants</th></tr></thead><tbody>${rows}</tbody></table></div></details>
      <p class="muted small" style="margin-top:12px">Paramètres statistiques conservés : ${D.trends.params.method}. Les résultats sont reproductibles avec <code>scripts/trend_analysis.py</code>.</p></div>`;
  }

  /* ── Navigation et rendu ────────────────────────────────────────────── */
  const VIEWS = ["overview", "explore", "trends", "compare", "methods", "about"];
  const TITLES = { overview: "Overview", explore: "Explore", trends: "Trends", compare: "Compare", methods: "Data & Methods", about: "About" };
  let current = "overview", cmpBuilt = false;
  EC.maps = {};

  EC.render = function () {
    const s = EC.state; EC.syncFilters();
    $("#topPeriod").textContent = current === "overview" ? `Période : ${P0}–${P1}` : current === "compare" ? `Période : ${cmp.y0}–${cmp.y1}` : ["explore", "trends"].includes(current) ? `Période : ${s.y0}–${s.y1}` : "";
    if (current === "overview") renderOverview(); else if (current === "explore") renderExplore(); else if (current === "trends") renderTrends();
    else if (current === "compare") { if (!cmpBuilt) { buildCompareControls(); cmpBuilt = true; } renderCompare(); } else if (current === "methods") renderMethods();
    if (window.lucide) lucide.createIcons();
  };

  function route() {
    let v = location.hash.slice(1); if (!VIEWS.includes(v)) v = "overview"; current = v;
    VIEWS.forEach((x) => ($("#view-" + x).hidden = x !== v));
    document.querySelectorAll(".rail nav a").forEach((a) => (a.dataset.view === v ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    $("#sectionTitle").textContent = TITLES[v]; $("#rail").classList.remove("open"); $("#menuBtn").setAttribute("aria-expanded", "false");
    EC.render(); window.scrollTo(0, 0);
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("#demoBanner").hidden = !D.meta.demo; document.body.classList.toggle("has-banner", !!D.meta.demo);
    const bh = () => document.documentElement.style.setProperty("--bh", (D.meta.demo ? $("#demoBanner").offsetHeight : 0) + "px"); bh(); window.addEventListener("resize", bh);
    $("#aboutVersion").textContent = `EcoShield v${D.meta.version} · données générées le ${new Date(D.meta.generated_at).toLocaleDateString("fr-FR")} · ${D.meta.demo ? "jeu de démonstration" : "données réelles"}`;
    EC.buildFilters($("#filtersExplore")); EC.buildFilters($("#filtersTrends"));
    $("#ovProvinces").addEventListener("click", (e) => { const b = e.target.closest("[data-region]"); if (b) { EC.state.scale = "province"; EC.state.region = b.dataset.region; location.hash = "explore"; } });
    $("#menuBtn").addEventListener("click", () => { const o = $("#rail").classList.toggle("open"); $("#menuBtn").setAttribute("aria-expanded", o); });
    window.addEventListener("hashchange", route); route();
  });
})();
