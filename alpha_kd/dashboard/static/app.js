let equityChart = null;

function formatPnL(pnl) {
    if (pnl === null || pnl === undefined) return "-";
    const percent = (pnl * 100).toFixed(2) + "%";
    return pnl >= 0 ? "+" + percent : percent;
}

function updateChart(logs) {
    const ctx = document.getElementById("equity-chart").getContext("2d");
    const labels = logs.map(log => log.bar_time || log.timestamp || "");
    const data = logs.map(log => log.equity || 0);

    if (equityChart) {
        equityChart.data.labels = labels;
        equityChart.data.datasets[0].data = data;
        equityChart.update();
    } else {
        equityChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Portfolio Equity",
                    data: data,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { display: false },
                    y: { grid: { color: "rgba(255, 255, 255, 0.05)" } }
                }
            }
        });
    }
}

function updateUI(logs) {
    if (!logs || logs.length === 0) return;
    const latest = logs[logs.length - 1];

    document.getElementById("agg-equity").textContent = latest.equity ? "$" + latest.equity.toFixed(2) : "-";
    const dd = (latest.drawdown || 0.0) * 100;
    document.getElementById("current-drawdown").textContent = dd.toFixed(2) + "%";

    const breaker = document.getElementById("breaker-status");
    if (latest.is_halted) {
        breaker.textContent = "HALTED";
        breaker.className = "value status-halted";
    } else {
        breaker.textContent = "ACTIVE";
        breaker.className = "value status-ok";
    }

    // Update ticker cards
    const container = document.getElementById("ticker-cards");
    container.innerHTML = "";
    if (latest.tickers) {
        Object.entries(latest.tickers).forEach(([sym, t]) => {
            const card = document.createElement("div");
            card.className = "ticker-card";
            card.innerHTML = `
                <h3>${sym}</h3>
                <div class="metric"><span class="label">Side</span><span class="value">${(t.side || "flat").toUpperCase()}</span></div>
                <div class="metric"><span class="label">Entry</span><span class="value">${t.entry_price ? t.entry_price.toFixed(2) : "-"}</span></div>
                <div class="metric"><span class="label">PnL</span><span class="value">${formatPnL(t.unrealized_pnl)}</span></div>
                <div class="metric"><span class="label">Kelly</span><span class="value">${((t.kelly_size || 0)*100).toFixed(1)}%</span></div>
                <div class="metric"><span class="label">Equity</span><span class="value">$${(t.equity || 0).toFixed(0)}</span></div>
            `;
            container.appendChild(card);
        });
    }

    // Update terminal view
    const terminal = document.getElementById("terminal");
    terminal.innerHTML = "";
    logs.forEach(log => {
        const line = document.createElement("div");
        line.className = "terminal-line";
        const ts = log.bar_time || log.timestamp || "unknown";
        const ddPct = ((log.drawdown || 0) * 100).toFixed(2);
        line.textContent = `[${ts}] Equity: $${(log.equity || 0).toFixed(2)} | DD: ${ddPct}% | Halted: ${log.is_halted}`;
        if (log.is_halted) line.style.color = "var(--danger)";
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

setInterval(fetchTelemetry, 1000);
fetchTelemetry();
