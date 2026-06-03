let lastTimestamp = null;

function formatPnL(pnl) {
    if (pnl === null || pnl === undefined) return "-";
    const percent = (pnl * 100).toFixed(2) + "%";
    return pnl >= 0 ? "+" + percent : percent;
}

function updateUI(logs) {
    if (!logs || logs.length === 0) return;
    const latest = logs[logs.length - 1];

    document.getElementById("strategy-side").textContent = (latest.side || "flat").toUpperCase();
    document.getElementById("entry-price").textContent = latest.entry_price ? latest.entry_price.toFixed(4) : "-";
    document.getElementById("unrealized-pnl").textContent = formatPnL(latest.unrealized_pnl);

    const dd = (latest.drawdown || 0.0) * 100;
    document.getElementById("current-drawdown").textContent = dd.toFixed(2) + "%";
    document.getElementById("peak-value").textContent = latest.equity ? "$" + latest.equity.toFixed(2) : "-";

    const breaker = document.getElementById("breaker-status");
    if (latest.is_halted) {
        breaker.textContent = "HALTED";
        breaker.className = "value status-halted";
        document.getElementById("trade-status").textContent = "HALTED";
    } else {
        breaker.textContent = "ACTIVE";
        breaker.className = "value status-ok";
        document.getElementById("trade-status").textContent = "NORMAL";
    }

    const kelly = (latest.kelly_size || 0.0) * 100;
    document.getElementById("kelly-size").textContent = kelly.toFixed(2) + "%";

    const terminal = document.getElementById("terminal");
    terminal.innerHTML = "";
    logs.forEach(log => {
        const line = document.createElement("div");
        line.className = "terminal-line";

        const timestamp = log.bar_time || log.timestamp || "unknown";
        const side = (log.side || "flat").toUpperCase();
        const unrealized = formatPnL(log.unrealized_pnl);
        const ddPct = ((log.drawdown || 0) * 100).toFixed(2);

        line.textContent = `[${timestamp}] Side: ${side} | PnL: ${unrealized} | DD: ${ddPct}% | Kelly: ${(log.kelly_size || 0).toFixed(4)} | Halted: ${log.is_halted}`;
        if (log.is_halted) {
            line.style.color = "var(--danger)";
        }
        terminal.appendChild(line);
    });
    terminal.scrollTop = terminal.scrollHeight;
}

function fetchTelemetry() {
    fetch("/api/telemetry")
        .then(response => response.json())
        .then(data => {
            updateUI(data);
        })
        .catch(err => {
            console.error("Error fetching telemetry:", err);
        });
}

setInterval(fetchTelemetry, 1000);
fetchTelemetry();
