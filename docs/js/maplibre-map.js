(() => {
  const container = document.getElementById("ecoshieldMap");
  const D = window.ECOSHIELD_DATA;

  if (!container || typeof maplibregl === "undefined" || !D) {
    console.error("EcoShield : carte, MapLibre ou données indisponibles.");
    return;
  }

  const metadata = D.meta?.series || [];
  const trends = D.trends?.resultats || {};
  const series = D.series || {};

  const getMeta = code => metadata.find(item => item.code === code);

  const getBounds = code => {
    const raw = getMeta(code)?.boite_englobante_lon_lat;
    if (!raw) return null;

    const values = raw.split(",").map(Number);
    if (values.length !== 4 || values.some(v => !Number.isFinite(v))) {
      return null;
    }

    const [west, south, east, north] = values;
    return [[west, south], [east, north]];
  };

  const format = (value, digits = 3) =>
    Number.isFinite(Number(value))
      ? Number(value).toLocaleString("fr-FR", {
          maximumFractionDigits: digits
        })
      : "—";

  const variableNames = {
    TAIR: "Température de l'air",
    PRECIP: "Précipitations",
    SOILM: "Humidité du sol"
  };

  const variableUnits = {
    TAIR: "°C",
    PRECIP: "mm/mois",
    SOILM: "kg/m²"
  };

  const latest = code => {
    const rows = series[code] || [];
    return rows.length ? rows[rows.length - 1] : null;
  };

  const trendDescription = code => {
    const result = trends[code]?.saisonnier;
    if (!result || result.status !== "ok") {
      return "Résultat statistique indisponible.";
    }

    return `
      <p><strong>Pente de Sen :</strong>
        ${format(result.sen_slope)} ${variableUnits[code]}/an</p>
      <p><strong>p-value ajustée (BH) :</strong>
        ${format(result.p_value_ajustee_BH, 4)}</p>
      <p><strong>Conclusion :</strong>
        ${result.significatif_apres_BH
          ? "Tendance statistiquement significative."
          : "Tendance non significative après correction BH."}
      </p>
    `;
  };

  const makeFeature = (code, label) => {
    const bounds = getBounds(code);
    if (!bounds) return null;

    const [[west, south], [east, north]] = bounds;

    return {
      type: "Feature",
      properties: { code, label },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [west, south],
          [east, south],
          [east, north],
          [west, north],
          [west, south]
        ]]
      }
    };
  };

  const features = [
    makeFeature("TAIR", "Emprise température"),
    makeFeature("PRECIP", "Emprise précipitations et humidité du sol")
  ].filter(Boolean);

  const map = new maplibregl.Map({
    container: "ecoshieldMap",
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors"
        }
      },
      layers: [{
        id: "osm-base",
        type: "raster",
        source: "osm"
      }]
    },
    center: [9.55, -0.05],
    zoom: 7,
    minZoom: 4,
    maxZoom: 16,
    attributionControl: true
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  map.on("load", () => {
    map.addSource("giovanni-footprints", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features
      }
    });

    map.addLayer({
      id: "giovanni-fill",
      type: "fill",
      source: "giovanni-footprints",
      paint: {
        "fill-color": [
          "match",
          ["get", "code"],
          "TAIR", "#E87535",
          "#168C83"
        ],
        "fill-opacity": 0.22
      }
    });

    map.addLayer({
      id: "giovanni-outline",
      type: "line",
      source: "giovanni-footprints",
      paint: {
        "line-color": [
          "match",
          ["get", "code"],
          "TAIR", "#C85B25",
          "#08776F"
        ],
        "line-width": 3
      }
    });

    map.on("click", "giovanni-fill", event => {
      const feature = event.features?.[0];
      if (!feature) return;

      const code = feature.properties.code;
      const meta = getMeta(code);
      const current = latest(code);

      const variables = code === "PRECIP"
        ? ["PRECIP", "SOILM"]
        : ["TAIR"];

      const measurements = variables.map(variable => {
        const row = latest(variable);
        return `
          <p><strong>${variableNames[variable]} :</strong>
          ${row ? format(row.value) + " " + variableUnits[variable] : "—"}
          ${row ? `<small>(${row.date})</small>` : ""}
          </p>
        `;
      }).join("");

      const statistics = variables.map(variable => `
        <h4>${variableNames[variable]}</h4>
        ${trendDescription(variable)}
      `).join("");

      const html = `
        <div class="ecoshield-map-popup">
          <h3>${feature.properties.label}</h3>
          <p><strong>Source :</strong> NASA Giovanni</p>
          <p><strong>Période disponible :</strong>
            ${meta.periode_analysee[0]} à ${meta.periode_analysee[1]}
          </p>
          <p><strong>Résolution :</strong>
            ${meta.resolution_spatiale}
          </p>
          <p><strong>Type de données :</strong>
            Moyenne spatiale mensuelle sur l'emprise.
          </p>
          <hr>
          <h4>Dernières mesures disponibles</h4>
          ${measurements}
          <hr>
          <h4>Tendances saisonnières</h4>
          ${statistics}
          <small>Les tendances présentées ne constituent pas des alertes officielles.</small>
        </div>
      `;

      new maplibregl.Popup({ maxWidth: "340px" })
        .setLngLat(event.lngLat)
        .setHTML(html)
        .addTo(map);
    });

    map.on("mouseenter", "giovanni-fill", () => {
      map.getCanvas().style.cursor = "pointer";
    });

    map.on("mouseleave", "giovanni-fill", () => {
      map.getCanvas().style.cursor = "";
    });

    const bounds = new maplibregl.LngLatBounds();
    features.forEach(feature => {
      feature.geometry.coordinates[0].forEach(point => bounds.extend(point));
    });

    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 65, maxZoom: 8 });
    }

    console.info("EcoShield : emprises Giovanni chargées.", features);
  });

  map.on("error", event => {
    console.error("EcoShield : erreur cartographique.", event.error);
  });

  const observer = new ResizeObserver(() => {
    if (container.offsetWidth > 0 && container.offsetHeight > 0) {
      map.resize();
    }
  });

  observer.observe(container);
  window.ecoshieldMap = map;
})();
