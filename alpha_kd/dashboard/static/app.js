let equityChart = null, currentMode = null, currentAction = null, isLoading = false;

const formatPnL = pnl => (pnl === null || pnl === undefined) ? "-" : (pnl >= 0 ? "+" : "") + (pnl * 100).toFixed(2) + "%";

function updateChart(logs) {
    const ctx = document.getElementById("equity-chart").getContext("2d");
    const labels = logs.map(l => l.bar_time || l.timestamp || "");
    const data = logs.map(l => l.equity || 0);
    if (equityChart) {
        equityChart.data.labels = labels;
        equityChart.data.datasets[0].data = data;
        equityChart.update();
    } else {
        equityChart = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [{ label: "Portfolio Equity", data, borderColor: "#3b82f6", backgroundColor: "rgba(59, 130, 246, 0.1)", fill: true, tension: 0.1 }]
            },
            options: { responsive: true, scales: { x: { display: false }, y: { grid: { color: "rgba(255, 255, 255, 0.05)" } } } }
        });
    }
}

function sendControl(mode, action) {
    const payload = {};
    if (mode) payload.mode = mode;
    if (action) payload.action = action;
    fetch("/api/control", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        .then(res => res.json())
        .then(data => { if (data.status === "ok") syncControlUI(data.control); })
        .catch(err => console.error("Error updating control:", err));
}

function syncControlUI(ctrl) {
    currentMode = ctrl.mode; currentAction = ctrl.action; isLoading = ctrl.loading;
    const select = document.getElementById("mode-select");
    if (select.value !== currentMode) select.value = currentMode;

    document.getElementById("btn-start").classList.toggle("active", currentAction === "start");
    document.getElementById("btn-pause").classList.toggle("active", currentAction === "pause");
    document.getElementById("btn-halt").classList.toggle("active", currentAction === "halt");

    const indicator = document.getElementById("status-indicator");
    const txt = document.getElementById("status-text");
    const isHalt = currentAction === "halt";

    if (isLoading) {
        indicator.className = "status-indicator status-loading";
        txt.textContent = "STATUS: LOADING";
    } else {
        indicator.className = "status-indicator";
        txt.textContent = isHalt ? "HALTED" : "LIVE MONITOR";
    }

    select.disabled = isLoading || isHalt;
    document.getElementById("btn-start").disabled = isLoading || isHalt;
    document.getElementById("btn-pause").disabled = isLoading || isHalt;
    document.getElementById("btn-halt").disabled = isHalt;
}

function updateUI(data) {
    const logs = data.logs || [];
    syncControlUI(data);
    if (!logs.length) return;
    const latest = logs[logs.length - 1];

    document.getElementById("agg-equity").textContent = latest.equity ? "$" + latest.equity.toFixed(2) : "-";
    document.getElementById("current-drawdown").textContent = ((latest.drawdown || 0) * 100).toFixed(2) + "%";

    const breaker = document.getElementById("breaker-status");
    const halted = latest.is_halted || currentAction === "halt";
    breaker.textContent = halted ? "HALTED" : "ACTIVE";
    breaker.className = "value " + (halted ? "status-halted" : "status-ok");

    const container = document.getElementById("ticker-cards");
    container.innerHTML = "";
    if (latest.tickers) {
        Object.entries(latest.tickers).forEach(([sym, t]) => {
            const card = document.createElement("div");
            card.className = "ticker-card";
            card.innerHTML = `<h3>${sym}</h3>
                <div class="metric"><span class="label">Side</span><span class="value">${(t.side || "flat").toUpperCase()}</span></div>
                <div class="metric"><span class="label">Entry</span><span class="value">${t.entry_price ? t.entry_price.toFixed(2) : "-"}</span></div>
                <div class="metric"><span class="label">PnL</span><span class="value">${formatPnL(t.unrealized_pnl)}</span></div>
                <div class="metric"><span class="label">Kelly</span><span class="value">${((t.kelly_size || 0)*100).toFixed(1)}%</span></div>
                <div class="metric"><span class="label">Equity</span><span class="value">$${(t.equity || 0).toFixed(0)}</span></div>`;
            container.appendChild(card);
        });
    }

    const terminal = document.getElementById("terminal");
    terminal.innerHTML = "";
    logs.forEach(log => {
        const line = document.createElement("div");
        line.className = "terminal-line";
        const ts = log.bar_time || log.timestamp || "unknown";
        const isH = log.is_halted || currentAction === 'halt';
        line.textContent = `[${ts}] Equity: $${(log.equity || 0).toFixed(2)} | DD: ${((log.drawdown || 0) * 100).toFixed(2)}% | Halted: ${isH}`;
        if (isH) line.style.color = "var(--danger)";
        terminal.appendChild(line);
    });
    terminal.scrollTop = terminal.scrollHeight;
    updateChart(logs);
}

function fetchTelemetry() {
    fetch("/api/telemetry")
        .then(res => res.json())
        .then(data => updateUI(data))
        .catch(err => console.error("Error fetching telemetry:", err));
}

document.getElementById("mode-select").addEventListener("change", e => sendControl(e.target.value, null));
document.getElementById("btn-start").addEventListener("click", () => sendControl(null, "start"));
document.getElementById("btn-pause").addEventListener("click", () => sendControl(null, "pause"));
document.getElementById("btn-halt").addEventListener("click", () => {
    if (confirm("Are you sure you want to FORCE HALT all execution?")) sendControl(null, "halt");
});

setInterval(fetchTelemetry, 1000);
fetchTelemetry();
