const $ = (id) => document.getElementById(id);

// --- Tab switching ---
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    $(`tab-${btn.dataset.tab}`).classList.add("active");
  };
});

// --- Populate metric checkboxes + history select ---
async function loadMetrics() {
  const res = await fetch("/api/metrics");
  const data = await res.json();
  const container = $("metricCheckboxes");
  const select = $("historyMetricSelect");
  container.innerHTML = "";
  select.innerHTML = "";
  data.metrics.forEach((name, i) => {
    const label = document.createElement("label");
    label.innerHTML = `<input type="checkbox" value="${name}" ${i < 2 ? "checked" : ""}> ${name}`;
    container.appendChild(label);

    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    select.appendChild(option);
  });
}
loadMetrics();

// --- Load demo dataset ---
$("loadDemoBtn").onclick = async () => {
  const res = await fetch("/api/demo-dataset");
  const data = await res.json();
  $("datasetInput").value = JSON.stringify(data, null, 2);
};

// --- Gauge SVG ---
function gaugeSVG(percent) {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percent / 100);
  return `
    <svg width="88" height="88" viewBox="0 0 88 88">
      <circle cx="44" cy="44" r="${radius}" fill="none" stroke="#2a2f38" stroke-width="7"/>
      <circle cx="44" cy="44" r="${radius}" fill="none" stroke="#e0a458" stroke-width="7"
        stroke-linecap="round" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
        transform="rotate(-90 44 44)" style="transition: stroke-dashoffset 0.5s ease"/>
      <text x="44" y="44" text-anchor="middle" dominant-baseline="central" class="gauge-value">${percent}%</text>
    </svg>`;
}

// --- Run evaluation ---
$("runBtn").onclick = async () => {
  let dataset;
  try {
    dataset = JSON.parse($("datasetInput").value);
  } catch (e) {
    alert("Dataset isn't valid JSON. Check for a trailing comma or missing bracket.");
    return;
  }

  const metrics = Array.from(document.querySelectorAll("#metricCheckboxes input:checked")).map((c) => c.value);
  if (metrics.length === 0) {
    alert("Select at least one metric.");
    return;
  }

  $("runBtn").textContent = "Running...";
  $("runBtn").disabled = true;

  const res = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset, metrics, label: $("runLabel").value || "run" }),
  });
  const data = await res.json();

  $("runBtn").textContent = "Run evaluation";
  $("runBtn").disabled = false;

  if (data.error) {
    alert(data.error);
    return;
  }

  renderSummary(data);
  renderRunResults(data);
};

function renderSummary(data) {
  const total = data.cases.length;
  const passed = data.cases.filter((c) => c.all_passed).length;
  const failed = total - passed;
  const percent = total ? Math.round((passed / total) * 100) : 0;

  $("summaryPanel").innerHTML = `
    <div class="summary-strip">
      <div class="gauge-figure">
        ${gaugeSVG(percent)}
        <div class="gauge-label">Pass rate</div>
      </div>
      <div class="summary-counts">
        <div class="summary-count-item count-pass">
          <div class="count-num">${passed}</div>
          <div class="count-label">Passed</div>
        </div>
        <div class="summary-count-item count-fail">
          <div class="count-num">${failed}</div>
          <div class="count-label">Failed</div>
        </div>
        <div class="summary-count-item">
          <div class="count-num">${total}</div>
          <div class="count-label">Total cases</div>
        </div>
      </div>
    </div>`;

  const banner = $("regressionBanner");
  if (data.regressions && data.regressions.length > 0) {
    banner.classList.remove("hidden");
    banner.innerHTML = data.regressions
      .map((r) => `REGRESSION — ${r.metric} vs run "${r.previous_run}": ${r.previous_score} &rarr; ${r.current_score} (dropped ${r.drop})`)
      .join("<br>");
  } else {
    banner.classList.add("hidden");
  }
}

function renderRunResults(data) {
  const container = $("runResults");
  container.innerHTML = "";
  data.cases.forEach((c) => {
    const card = document.createElement("div");
    card.className = `case-card ${c.all_passed ? "pass" : "fail"}`;
    let html = `<div class="case-title-row">
      <span class="status-badge ${c.all_passed ? "pass" : "fail"}">${c.all_passed ? "\u2713" : "\u2717"}</span>
      <span class="case-title">${c.name}</span>
    </div>`;
    c.metrics.forEach((m) => {
      const rowClass = !m.applicable ? "na" : (m.passed ? "pass" : "fail");
      const dotClass = !m.applicable ? "dot-na" : (m.passed ? "dot-pass" : "dot-fail");
      html += `<div class="metric-row ${rowClass}">
        <span class="dot ${dotClass}"></span>
        <span class="metric-body">
          <span class="metric-name-score">${m.name}: ${m.score}</span>
          ${m.reason ? `<span class="metric-reason">${m.reason}</span>` : ""}
        </span>
      </div>`;
    });
    card.innerHTML = html;
    container.appendChild(card);
  });
}

// --- History ---
$("loadHistoryBtn").onclick = async () => {
  const metric = $("historyMetricSelect").value;
  const res = await fetch(`/api/history/${metric}`);
  const rows = await res.json();

  const chart = $("historyChart");
  if (rows.length === 0) {
    chart.innerHTML = `<div class="empty-state">No readings yet for "${metric}" — run an evaluation with this metric selected first.</div>`;
    $("historyTable").innerHTML = "";
    return;
  }

  chart.innerHTML = `<div class="bar-chart">${rows
    .map((r) => {
      const height = Math.max(4, Math.round(r.avg_score * 150));
      return `<div class="bar-wrap">
        <div class="bar-value">${r.avg_score.toFixed(2)}</div>
        <div class="bar" style="height:${height}px" title="${r.run_label}: ${r.avg_score.toFixed(3)}"></div>
        <div class="bar-label">${r.run_label}</div>
      </div>`;
    })
    .join("")}</div>`;

  let tableHtml = "<table><tr><th>Run</th><th>Avg score</th><th>When</th></tr>";
  rows.forEach((r) => {
    tableHtml += `<tr><td>${r.run_label}</td><td>${r.avg_score.toFixed(3)}</td><td>${r.created_at.slice(0, 19)}</td></tr>`;
  });
  tableHtml += "</table>";
  $("historyTable").innerHTML = tableHtml;
};

// --- Pairwise ---
$("pairwiseBtn").onclick = async () => {
  $("pairwiseBtn").textContent = "Comparing...";
  $("pairwiseBtn").disabled = true;

  const res = await fetch("/api/pairwise", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input_text: $("pairwiseInput").value,
      output_a: $("pairwiseA").value,
      output_b: $("pairwiseB").value,
    }),
  });
  const data = await res.json();

  $("pairwiseBtn").textContent = "Compare";
  $("pairwiseBtn").disabled = false;

  const winnerLabel = data.winner === "tie" ? "Tie" : `Response ${data.winner} wins`;
  $("pairwiseResult").innerHTML = `<div class="case-card pass">
    <div class="case-title-row">
      <span class="status-badge pass">&#10003;</span>
      <span class="case-title">${winnerLabel}</span>
    </div>
    <div class="metric-row pass"><span class="dot dot-pass"></span><span class="metric-body"><span class="metric-reason">${data.reasoning || ""}</span></span></div>
  </div>`;
};

// --- Calibration ---
$("calibrateBtn").onclick = async () => {
  $("calibrateBtn").textContent = "Running...";
  $("calibrateBtn").disabled = true;
  $("calibrationResult").innerHTML = `<div class="empty-state">Running calibration against the labeled sample...</div>`;

  const res = await fetch("/api/calibrate", { method: "POST" });
  const data = await res.json();

  $("calibrateBtn").textContent = "Run calibration";
  $("calibrateBtn").disabled = false;

  const percent = Math.round(data.agreement_rate * 100);
  let html = `<div class="summary-strip" style="margin-top:18px">
    <div class="gauge-figure">${gaugeSVG(percent)}<div class="gauge-label">Judge agreement</div></div>
    <div class="summary-counts">
      <div class="summary-count-item count-pass"><div class="count-num">${data.agreements}</div><div class="count-label">Agreed</div></div>
      <div class="summary-count-item"><div class="count-num">${data.total}</div><div class="count-label">Total sampled</div></div>
    </div>
  </div>`;
  html += "<table><tr><th>Input</th><th>Judge</th><th>Human</th><th>Agree?</th></tr>";
  data.results.forEach((r) => {
    html += `<tr>
      <td>${r.input}</td>
      <td>${r.judge_score.toFixed(2)}</td>
      <td>${r.human_score.toFixed(2)}</td>
      <td class="${r.agree ? "agree" : "disagree"}">${r.agree ? "Yes" : "No"}</td>
    </tr>`;
  });
  html += "</table>";
  $("calibrationResult").innerHTML = html;
};
