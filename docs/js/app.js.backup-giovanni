
(() => {
  "use strict";

  /* =========================================================
     ECOSHIELD — APPLICATION PRINCIPALE
     ========================================================= */

  const D = window.ECOSHIELD_DATA;

  const content = document.querySelector(".content");

  if (!D) {
    if (content) {
      content.innerHTML = `
        <div class="card">
          <h3>Données indisponibles</h3>
          <p>
            Impossible de charger les données EcoShield.
            Vérifiez que le fichier de données est correctement chargé.
          </p>
        </div>
      `;
    }
    return;
  }

  /* =========================================================
     OUTILS GÉNÉRAUX
     ========================================================= */

  const $ = id => document.getElementById(id);

  const setText = (id, value) => {
    const element = $(id);
    if (element) element.textContent = value;
  };

  const setHTML = (id, value) => {
    const element = $(id);
    if (element) element.innerHTML = value;
  };

  const fmt = (n, digits = 2) => {
    if (n === null || n === undefined || !Number.isFinite(Number(n))) {
      return "—";
    }

    return Number(n).toLocaleString("fr-FR", {
      maximumFractionDigits: digits,
      minimumFractionDigits: 0
    });
  };

  const dateLabel = date => {
    if (!date) return "Date inconnue";

    const d = new Date(date + "T00:00:00");

    if (Number.isNaN(d.getTime())) return date;

    return d.toLocaleDateString("fr-FR", {
      month: "long",
      year: "numeric"
    });
  };

  const shortDate = date => {
    if (!date) return "";

    const d = new Date(date + "T00:00:00");

    if (Number.isNaN(d.getTime())) return date;

    return d.toLocaleDateString("fr-FR", {
      month: "short",
      year: "numeric"
    });
  };

  const safeArray = value => Array.isArray(value) ? value : [];

  const escapeHTML = value => String(value ?? "").replace(
    /[&<>"']/g,
    char => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    })[char]
  );

  /* =========================================================
     CONFIGURATION DES VARIABLES
     ========================================================= */

  const variableInfo = {
    TAIR: {
      name: "Température de l'air",
      unit: "°C",
      short: "Température"
    },

    PRECIP: {
      name: "Précipitations",
      unit: "mm/mois",
      short: "Précipitations"
    },

    SOILM: {
      name: "Humidité du sol (0–10 cm)",
      unit: "kg/m²",
      short: "Humidité du sol"
    }
  };

  const series = D.series || {};
  const indicators = safeArray(D.indicators);
  const summary = D.decision_summary || {};
  const charts = {};

  const signalNames = [
    "AUCUN SIGNAL COMBINÉ",
    "SIGNAL ISOLÉ À SURVEILLER",
    "DÉFICIT HYDRIQUE POTENTIEL",
    "SIGNAL HYDRIQUE RENFORCÉ"
  ];

  const signalClass = signal => ({
    "AUCUN SIGNAL COMBINÉ": "no",
    "SIGNAL ISOLÉ À SURVEILLER": "warn",
    "DÉFICIT HYDRIQUE POTENTIEL": "warn",
    "SIGNAL HYDRIQUE RENFORCÉ": "strong"
  }[signal] || "no");

  const signalLabel = signal => {
    const label = escapeHTML(signal || "Signal inconnu");

    return `<span class="badge ${signalClass(signal)}">${label}</span>`;
  };

  const availableSeries = Object.entries(series).filter(
    ([code, rows]) =>
      variableInfo[code] &&
      Array.isArray(rows) &&
      rows.length > 0
  );

  const getSeries = code => safeArray(series[code]);

  const getLastRecord = rows => {
    return rows.length ? rows[rows.length - 1] : null;
  };

  /* =========================================================
     GRAPHIQUES
     ========================================================= */

  function createChart(id, config) {
    const canvas = $(id);

    if (!canvas || typeof Chart === "undefined") return;

    if (charts[id]) {
      charts[id].destroy();
      delete charts[id];
    }

    charts[id] = new Chart(canvas, config);
  }

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,

    interaction: {
      intersect: false,
      mode: "index"
    },

    plugins: {
      legend: {
        display: false
      },

      tooltip: {
        backgroundColor: "#102E28",
        padding: 11
      }
    },

    scales: {
      x: {
        ticks: {
          maxTicksLimit: 10,
          maxRotation: 0,
          color: "#718078",
          font: {
            size: 10
          }
        },

        grid: {
          display: false
        }
      },

      y: {
        ticks: {
          color: "#718078",
          font: {
            size: 10
          }
        },

        grid: {
          color: "#edf1ee"
        }
      }
    }
  };

  /* =========================================================
     VUE D'ENSEMBLE
     ========================================================= */

  function renderOverview() {
    const counts = summary.nombre_mois_par_signal || {};
    const total = Number(summary.nombre_mois) || 0;

    const waterSignals =
      (counts["DÉFICIT HYDRIQUE POTENTIEL"] || 0) +
      (counts["SIGNAL HYDRIQUE RENFORCÉ"] || 0);

    const kpis = [
      [
        "Variables climatiques",
        fmt(availableSeries.length, 0),
        "Séries disponibles"
      ],
      [
        "Mois analysés",
        fmt(total, 0),
        "Période d'observation"
      ],
      [
        "Signaux hydriques",
        fmt(waterSignals, 0),
        "Déficit potentiel ou renforcé"
      ],
      [
        "Provinces explorables",
        fmt(safeArray(D.simulation?.provinces).length, 0),
        "Espace de simulation"
      ]
    ];

    setHTML(
      "overviewKpis",
      kpis.map(k => `
        <div class="kpi">
          <div class="kpi-label">${k[0]}</div>
          <div class="kpi-value">${k[1]}</div>
          <div class="kpi-foot">${k[2]}</div>
        </div>
      `).join("")
    );

    /* Dernières valeurs disponibles */

    const latestHTML = availableSeries.map(([code, rows]) => {
      const last = getLastRecord(rows);
      const info = variableInfo[code];

      return `
        <div class="latest-row">
          <div>
            <strong>${info.name}</strong>
            <small>${dateLabel(last.date)}</small>
          </div>

          <div class="latest-value">
            ${fmt(last.value)}
            <small>${info.unit}</small>
          </div>
        </div>
      `;
    });

    if (!latestHTML.length) {
      latestHTML.push(`
        <div class="latest-row">
          <span>Aucune série climatique disponible.</span>
        </div>
      `);
    }

    setHTML("latestValues", latestHTML.join(""));

    /* Résumé des tendances */

    const results = D.trends?.resultats || {};

    const trendHTML = Object.entries(results)
      .filter(([code]) => variableInfo[code])
      .map(([code, result]) => {
        const t = result.saisonnier || {};

        return `
          <div class="latest-row">
            <div>
              <strong>${variableInfo[code].short}</strong>
              <small>
                Analyse saisonnière · p ajustée
                ${fmt(t.p_value_ajustee_BH, 3)}
              </small>
            </div>

            ${signalLabel(
              t.significatif_apres_BH
                ? "Tendance significative"
                : "Non significative"
            )}
          </div>
        `;
      });

    setHTML(
      "trendSummary",
      trendHTML.length
        ? trendHTML.join("")
        : "<p>Aucun résultat statistique disponible.</p>"
    );

    setText(
      "overviewSource",
      "Les analyses scientifiques présentées reposent sur des séries mensuelles NASA Giovanni couvrant une zone autour de Libreville. L'exploration des neuf provinces utilise un jeu de données de simulation distinct."
    );
  }

  /* =========================================================
     ANALYSE CLIMATIQUE
     ========================================================= */

  let climateCode = availableSeries[0]?.[0] || "PRECIP";

  function renderClimate() {
    const selector = $("climateVariable");

    if (selector && series[selector.value]) {
      climateCode = selector.value;
    }

    const rows = getSeries(climateCode);
    const info = variableInfo[climateCode];

    if (!info || !rows.length) {
      setText("climatePeriod", "Aucune donnée disponible");

      setHTML(
        "climateDescription",
        "<p>Cette variable ne dispose pas encore de données.</p>"
      );

      return;
    }

    createChart("climateChart", {
      type: "line",

      data: {
        labels: rows.map(r => shortDate(r.date)),

        datasets: [{
          label: info.name,
          data: rows.map(r => r.value),

          borderColor: "#25865A",
          backgroundColor: "rgba(37,134,90,.10)",

          borderWidth: 2,
          pointRadius: 0,
          pointHitRadius: 8,

          fill: true,
          tension: 0.22
        }]
      },

      options: lineOptions
    });

    setText(
      "climatePeriod",
      `${rows[0].date.slice(0, 7)} → ${rows[rows.length - 1].date.slice(0, 7)} · ${rows.length} mois`
    );

    const meta = safeArray(D.meta?.series).find(
      item => item.code === climateCode
    );

    const source = meta
      ? `Source : ${escapeHTML(meta.produit)}. Résolution spatiale : ${escapeHTML(meta.resolution_spatiale)}.`
      : "Source : données climatiques intégrées au jeu de données EcoShield.";

    setHTML(
      "climateDescription",
      `<strong>${info.name}</strong> — unité : ${info.unit}. ${source} Résolution temporelle : mensuelle.`
    );

    /* Cartes des variables disponibles */

    const cards = availableSeries.map(([code, data]) => {
      const last = getLastRecord(data);
      const variable = variableInfo[code];

      return `
        <div class="card">
          <span class="eyebrow">
            ${variable.short.toUpperCase()}
          </span>

          <h3>
            ${fmt(last.value)} ${variable.unit}
          </h3>

          <p>
            Dernier relevé : ${dateLabel(last.date)}<br>
            ${data.length} observations mensuelles.
          </p>
        </div>
      `;
    });

    setHTML(
      "variableCards",
      cards.length
        ? cards.join("")
        : "<div class='card'>Aucune variable disponible.</div>"
    );
  }

  /* =========================================================
     TENDANCES STATISTIQUES
     ========================================================= */

  function renderTrends() {
    const type = $("trendType")?.value || "saisonnier";

    const rows = Object.entries(
      D.trends?.resultats || {}
    ).filter(([code]) => variableInfo[code]);

    const tableHTML = rows.map(([code, result]) => {
      const t = result[type];

      if (!t) return "";

      const slopeUnit = type === "saisonnier"
        ? result.unite_pente_saisonnier
        : result.unite_pente_annuel;

      return `
        <tr>
          <td>
            <strong>${variableInfo[code].name}</strong><br>
            <span class="muted">${fmt(t.n_obs, 0)} observations</span>
          </td>

          <td>
            ${fmt(t.sen_slope, 4)}<br>
            <span class="muted">${escapeHTML(slopeUnit || "")}</span>
          </td>

          <td>
            [${fmt(t.ci_low, 3)} ; ${fmt(t.ci_high, 3)}]
          </td>

          <td>${fmt(t.p_value_ajustee_BH, 4)}</td>

          <td>
            ${signalLabel(
              t.significatif_apres_BH
                ? "Tendance significative"
                : "Non significative"
            )}
          </td>
        </tr>
      `;
    }).join("");

    setHTML(
      "trendTable",
      tableHTML || `
        <tr>
          <td colspan="5">Aucun résultat statistique disponible.</td>
        </tr>
      `
    );

    const validRows = rows
      .map(([, result]) => result[type])
      .filter(Boolean);

    const all = validRows.length > 0 &&
      validRows.every(t => !t.significatif_apres_BH);

    setText(
      "trendConclusionTitle",
      all
        ? "Aucune tendance significative détectée"
        : "Des tendances significatives ont été détectées"
    );

    setText(
      "trendConclusion",
      all
        ? "Pour les variables disposant de résultats, aucune tendance statistiquement significative n'est détectée au seuil retenu après correction Benjamini-Hochberg. Cela ne démontre pas l'absence de tendance."
        : "Au moins une variable présente une tendance statistiquement significative après correction Benjamini-Hochberg."
    );
  }

  /* =========================================================
     SIGNAUX ENVIRONNEMENTAUX
     ========================================================= */

  function renderSignals() {
    const counts = summary.nombre_mois_par_signal || {};
    const total = Number(summary.nombre_mois) || 0;

    const kpis = signalNames.map(signal => {
      const count = Number(counts[signal]) || 0;
      const percentage = total > 0 ? 100 * count / total : 0;

      return `
        <div class="kpi">
          <div class="kpi-label">${signal}</div>
          <div class="kpi-value">${fmt(count, 0)}</div>
          <div class="kpi-foot">${fmt(percentage, 1)} % des mois</div>
        </div>
      `;
    });

    setHTML("signalKpis", kpis.join(""));

    /* Diagramme circulaire */

    createChart("signalChart", {
      type: "doughnut",

      data: {
        labels: signalNames,

        datasets: [{
          data: signalNames.map(s => Number(counts[s]) || 0),

          backgroundColor: [
            "#8DAF9A",
            "#39AFC0",
            "#D59A37",
            "#D45B54"
          ],

          borderWidth: 2,
          borderColor: "#fff"
        }]
      },

      options: {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
          legend: {
            position: "bottom",

            labels: {
              boxWidth: 10,
              padding: 13,
              font: {
                size: 10
              }
            }
          }
        }
      }
    });

    /* Dernier signal */

    const last = indicators[indicators.length - 1];

    if (last) {
      setHTML("lastSignalTitle", signalLabel(last.niveau_signal));

      setText(
        "lastSignalDate",
        `Dernier relevé : ${dateLabel(last.date)}`
      );

      setText(
        "lastSignalDetail",
        last.recommandation || "Aucune recommandation disponible."
      );
    } else {
      setText("lastSignalTitle", "Aucun signal disponible");
      setText("lastSignalDate", "Aucune date disponible");
      setText("lastSignalDetail", "Les indicateurs ne sont pas encore chargés.");
    }

    /* Filtre */

    const filter = $("signalFilter");

    if (filter) {
      filter.innerHTML =
        '<option value="all">Tous les signaux</option>' +
        signalNames.map(signal => `
          <option value="${escapeHTML(signal)}">
            ${signal}
          </option>
        `).join("");
    }

    renderSignalTable();
  }

  function renderSignalTable() {
    const filter = $("signalFilter")?.value || "all";

    const rows = indicators
      .filter(row =>
        filter === "all" || row.niveau_signal === filter
      )
      .slice()
      .reverse();

    const html = rows.map(row => `
      <tr>
        <td>${dateLabel(row.date)}</td>

        <td>${fmt(row.temperature_c)} °C</td>

        <td>${fmt(row.precipitation_mm)} mm</td>

        <td>${fmt(row.humidite_sol_kg_m2)} kg/m²</td>

        <td>${signalLabel(row.niveau_signal)}</td>
      </tr>
    `).join("");

    setHTML(
      "signalTable",
      html || `
        <tr>
          <td colspan="5">Aucun signal ne correspond à ce filtre.</td>
        </tr>
      `
    );
  }

  /* =========================================================
     EXPLORATION PROVINCIALE
     ========================================================= */

  function renderProvinces() {
    const simulation = D.simulation || {};
    const provinces = safeArray(simulation.provinces);

    const selector = $("provinceSelect");

    if (!selector) return;

    selector.innerHTML = provinces.map(province => `
      <option value="${escapeHTML(province)}">
        ${escapeHTML(province)}
      </option>
    `).join("");

    updateProvince();
  }

  function updateProvince() {
    const simulation = D.simulation || {};
    const province = $("provinceSelect")?.value;
    const variable = $("provinceVariable")?.value;

    if (!province || !variable) return;

    const records = safeArray(simulation.records)
      .filter(row => row.province === province)
      .sort((a, b) => String(a.date).localeCompare(String(b.date)));

    const units = {
      temperature_c: "°C",
      precipitation_mm: "mm/mois",
      humidite_sol_kg_m2: "kg/m²"
    };

    const unit = units[variable] || "";

    const values = records
      .map(row => Number(row[variable]))
      .filter(Number.isFinite);

    if (!records.length || !values.length) {
      setHTML(
        "provinceStats",
        '<div class="kpi"><div class="kpi-label">Données</div><div class="kpi-value">Indisponibles</div></div>'
      );

      setText(
        "provinceSignal",
        `Aucune donnée disponible pour ${province}.`
      );

      createChart("provinceChart", {
        type: "line",
        data: {
          labels: [],
          datasets: []
        },
        options: lineOptions
      });

      return;
    }

    const average = values.reduce((a, b) => a + b, 0) / values.length;
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);

    const stats = [
      ["Moyenne", `${fmt(average)} ${unit}`],
      ["Minimum", `${fmt(minimum)} ${unit}`],
      ["Maximum", `${fmt(maximum)} ${unit}`]
    ];

    setHTML(
      "provinceStats",
      stats.map(item => `
        <div class="kpi">
          <div class="kpi-label">${item[0]}</div>
          <div class="kpi-value">${item[1]}</div>
        </div>
      `).join("")
    );

    /* Graphique provincial */

    createChart("provinceChart", {
      type: "line",

      data: {
        labels: records.map(row => shortDate(row.date)),

        datasets: [{
          label: unit,
          data: records.map(row => row[variable]),

          borderColor: "#39AFC0",
          backgroundColor: "rgba(57,175,192,.10)",

          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.25
        }]
      },

      options: lineOptions
    });

    /* Signal dominant */

    const levels = records.reduce((acc, row) => {
      if (row.niveau_signal) {
        acc[row.niveau_signal] = (acc[row.niveau_signal] || 0) + 1;
      }

      return acc;
    }, {});

    const dominant = Object.entries(levels)
      .sort((a, b) => b[1] - a[1])[0];

    setText(
      "provinceSignal",
      dominant
        ? `${province} : niveau le plus fréquent dans cette simulation : ${dominant[0]} (${dominant[1]} mois sur ${records.length}).`
        : `Aucun niveau de signal disponible pour ${province}.`
    );
  }

  /* =========================================================
     DONNÉES ET MÉTHODOLOGIE
     ========================================================= */

  function renderMethods() {
    const metas = safeArray(D.meta?.series);

    const sourceItems = metas.map(meta => `
      <li>
        <strong>${escapeHTML(meta.variable)}</strong>
        — ${escapeHTML(meta.produit)}<br>
        Résolution : ${escapeHTML(meta.resolution_spatiale)}
        · Période :
        ${escapeHTML(meta.periode_analysee?.[0] ?? "—")}
        à
        ${escapeHTML(meta.periode_analysee?.[1] ?? "—")}
      </li>
    `).join("");

    setHTML("methodsContent", `
      <div class="methods-grid">

        <article class="card">
          <span class="eyebrow">SOURCES SCIENTIFIQUES</span>
          <h3>Données NASA Giovanni</h3>
          <ul>
            ${sourceItems || "<li>Aucune métadonnée disponible.</li>"}
          </ul>
        </article>

        <article class="card">
          <span class="eyebrow">TRAITEMENT DES DONNÉES</span>
          <h3>Préparation des séries</h3>

          <ul>
            <li>Température : conversion Kelvin vers degrés Celsius.</li>
            <li>Précipitations : conversion du taux moyen mm/h en cumul mensuel.</li>
            <li>Humidité du sol : valeur conservée en kg/m².</li>
            <li>Valeurs manquantes et doublons contrôlés ; aucune interpolation.</li>
            <li>Valeur atypique de précipitation de novembre 2017 signalée et conservée.</li>
          </ul>
        </article>

        <article class="card">
          <span class="eyebrow">STATISTIQUES</span>
          <h3>Méthodes d'analyse</h3>

          <ul>
            <li>Test de Mann-Kendall saisonnier et annuel.</li>
            <li>Pente de Sen et intervalle de confiance à 95 %.</li>
            <li>Correction Benjamini-Hochberg des tests multiples.</li>
            <li>Les résultats affichés utilisent les p-values ajustées.</li>
          </ul>
        </article>

        <article class="card">
          <span class="eyebrow">INDICATEURS</span>
          <h3>Signaux environnementaux</h3>

          <ul>
            <li>Période : janvier 2016 à septembre 2025.</li>
            <li>Référence climatologique exploratoire : 2016–2024.</li>
            <li>Anomalies standardisées et seuils exploratoires.</li>
            <li>Indicateurs non validés comme alertes opérationnelles ou prévisions.</li>
          </ul>
        </article>

        <article class="card method-wide">
          <span class="eyebrow">LIMITES ET PÉRIMÈTRE</span>
          <h3>Interprétation des résultats</h3>

          <p>
            Les séries Giovanni sont des moyennes spatiales sur des boîtes
            englobantes localisées autour de Libreville. Elles ne représentent
            pas une mesure exhaustive de l'ensemble du territoire gabonais.
            Les boîtes englobantes et résolutions diffèrent selon les variables.
          </p>

          <p>
            Les indicateurs combinés sont exploratoires. Ils ne constituent
            ni une preuve de sécheresse, ni une prévision, ni une alerte officielle.
          </p>

          <p>
            Les neuf provinces présentées dans l'espace d'exploration reposent
            sur une simulation de démonstration distincte des observations
            Giovanni. Les valeurs simulées ne sont pas des mesures climatiques réelles.
          </p>
        </article>

      </div>
    `);
  }

  /* =========================================================
     NAVIGATION
     ========================================================= */

  const views = [
    "overview",
    "climate",
    "trends",
    "signals",
    "provinces",
    "methods"
  ];

  const titles = {
    overview: "Vue d'ensemble",
    climate: "Analyse climatique",
    trends: "Tendances statistiques",
    signals: "Signaux environnementaux",
    provinces: "Exploration provinciale",
    methods: "Données et méthodologie"
  };

  function navigate(view) {
    if (!views.includes(view)) {
      view = "overview";
    }

    document.querySelectorAll(".view").forEach(element => {
      element.classList.toggle(
        "active",
        element.id === `view-${view}`
      );
    });

    document.querySelectorAll(".nav-btn").forEach(element => {
      element.classList.toggle(
        "active",
        element.dataset.view === view
      );
    });

    setText("pageTitle", titles[view]);

    if (location.hash !== `#${view}`) {
      history.replaceState(null, "", `#${view}`);
    }

    if (view === "climate") renderClimate();
    if (view === "trends") renderTrends();
    if (view === "signals") renderSignals();
    if (view === "provinces") updateProvince();
  }

  /* =========================================================
     ÉVÉNEMENTS
     ========================================================= */

  document.querySelectorAll(".nav-btn").forEach(button => {
    button.addEventListener("click", () => {
      navigate(button.dataset.view);
    });
  });

  document.querySelectorAll("[data-go]").forEach(button => {
    button.addEventListener("click", () => {
      navigate(button.dataset.go);
    });
  });

  $("climateVariable")?.addEventListener("change", renderClimate);

  $("trendType")?.addEventListener("change", renderTrends);

  $("signalFilter")?.addEventListener("change", renderSignalTable);

  $("provinceSelect")?.addEventListener("change", updateProvince);

  $("provinceVariable")?.addEventListener("change", updateProvince);

  window.addEventListener("hashchange", () => {
    navigate(location.hash.replace("#", ""));
  });

  /* =========================================================
     PÉRIODE GLOBALE
     ========================================================= */

  const allDates = availableSeries.flatMap(([, rows]) =>
    rows.map(row => row.date).filter(Boolean)
  ).sort();

  if (allDates.length) {
    setText(
      "globalPeriod",
      `${allDates[0].slice(0, 7)} — ${allDates[allDates.length - 1].slice(0, 7)}`
    );
  } else {
    setText("globalPeriod", "Période indisponible");
  }

  /* =========================================================
     INITIALISATION
     ========================================================= */

  renderOverview();
  renderClimate();
  renderTrends();
  renderSignals();
  renderProvinces();
  renderMethods();

  navigate(location.hash.replace("#", "") || "overview");

})();
