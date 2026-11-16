/* EcoShield — carte Leaflet : remplissage = direction de la tendance, bordure = significativité (deux informations distinctes). */
(function () {
  const EC = (window.EC = window.EC || {});
  const COL = { up: "#25865A", down: "#D45B54", none: "#87938D", sig: "#2689B8", nosig: "#D59A37" };

  EC.legendHTML = function () {
    return `<div class="legend">
      <div><span class="sw up"></span>Tendance à la hausse (remplissage vert)</div>
      <div><span class="sw down"></span>Tendance à la baisse (remplissage rouge)</div>
      <div><span class="sw none"></span>Tendance non détectable (gris)</div>
      <div><span class="sw sig"></span>Résultat significatif à 5 % (bordure bleue)</div>
      <div><span class="sw nosig"></span>Résultat non significatif (bordure ambre pointillée)</div></div>
      <p class="muted small" style="margin:8px 0 0">Une hausse n'est pas forcément favorable, et « non détectable » ne signifie pas « aucun changement ».</p>`;
  };

  EC.createMap = function (elId, opt) {
    const D = EC.D;
    const map = L.map(elId, { minZoom: 5, maxZoom: 11, scrollWheelZoom: false, zoomSnap: 0.25 });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", { attribution: "© OpenStreetMap · © CARTO", subdomains: "abcd", maxZoom: 19 }).addTo(map);
    const ctx = () => (opt.fixedVar ? { v: opt.fixedVar, a: D.meta.period[0], b: D.meta.period[1] } : { v: EC.state.variable, a: EC.state.y0, b: EC.state.y1 });
    const selected = (id) => !opt.fixedVar && EC.state.region === id;

    function style(f) {
      const { v, a, b } = ctx(); const id = f.properties.id; const t = EC.trend(v, id, a, b);
      const local = f.properties.level === "local", rel = EC.regionById(id).reliable[v];
      const fill = !t ? "#cfd8d3" : t.dir === 1 ? COL.up : t.dir === -1 ? COL.down : COL.none;
      const sel = selected(id);
      if (local && !rel) return { fillColor: "#66736D", fillOpacity: 0.1, color: sel ? "#102E28" : "#66736D", weight: sel ? 3 : 1.5, dashArray: "2 4" };
      return { fillColor: fill, fillOpacity: local ? (rel ? 0.7 : 0.12) : t ? 0.58 : 0.2,
               color: sel ? "#102E28" : !t ? "#a9b5af" : t.sig ? COL.sig : COL.nosig, weight: sel ? 4 : 2, dashArray: !t || t.sig ? null : "5 4" };
    }
    function tip(f) {
      const { v, a, b } = ctx(); const id = f.properties.id; const t = EC.trend(v, id, a, b), V = D.variables[v];
      if (!t) return `<b>${f.properties.name}</b><br>Série insuffisante`;
      const warn = EC.regionById(id).reliable[v] ? "" : "<br><i>Résolution insuffisante pour cette zone</i>";
      return `<b>${f.properties.name}</b><br>${EC.fmtS(t.slope, V.decimals + 1)} ${V.trend_unit} · ${t.sig ? "significatif" : "non significatif"}${warn}`;
    }
    function bind(f, layer) {
      layer.bindTooltip(() => tip(f), { sticky: true });
      layer.on("click", () => opt.onSelect && opt.onSelect(f.properties.id, f.properties.level));
      layer.on("keypress", () => opt.onSelect && opt.onSelect(f.properties.id, f.properties.level));
    }
    const prov = L.geoJSON(D.geo.provinces, { style, onEachFeature: bind }).addTo(map);
    const outline = L.geoJSON(D.geo.gabon, { style: () => ({ fill: false, color: "#102E28", weight: selected("gabon") ? 4 : 1.6, interactive: false }) }).addTo(map);
    let local = null;
    if (opt.showLocal) local = L.geoJSON(D.geo.local_areas, { style, onEachFeature: bind }).addTo(map);
    const bounds = outline.getBounds();

    return {
      map,
      fit() { map.invalidateSize(); map.fitBounds(bounds, { padding: [12, 12] }); },
      update() {
        prov.setStyle(style); outline.setStyle(() => ({ fill: false, color: "#102E28", weight: selected("gabon") ? 4 : 1.6, interactive: false }));
        if (local) local.setStyle(style);
        const s = EC.state.region; if (!opt.fixedVar && s !== "gabon") { prov.eachLayer((l) => l.feature.properties.id === s && l.bringToFront()); if (local) local.eachLayer((l) => l.feature.properties.id === s && l.bringToFront()); }
      },
    };
  };
})();
