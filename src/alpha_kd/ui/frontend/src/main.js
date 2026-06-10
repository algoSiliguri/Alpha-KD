import uPlot from "uplot";
import "./style.css";

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get("session-id") || "local-dev";
document.getElementById("session-id-val").textContent = sessionId;

const consoleEl = document.getElementById("logs-console");
const dot = document.getElementById("connection-status-dot");
const apiOfflineBanner = document.getElementById("api-offline-banner");
const wsOfflineBanner = document.getElementById("ws-offline-banner");

function addLog(source, text) {
    const timeStr = new Date().toLocaleTimeString();
    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = `<span class="log-time">[${timeStr}]</span> <strong>${source}:</strong> ${text}`;
    consoleEl.appendChild(entry);
    consoleEl.scrollTop = consoleEl.scrollHeight;

    // Cap log lines
    while (consoleEl.children.length > 200) {
        consoleEl.removeChild(consoleEl.firstChild);
    }
}

// Pre-allocate uPlot data container
const data = [
    [], // Timestamps
    [], // Price
    [], // Capital
];

const container = document.getElementById("chart-container");
const opts = {
    title: "Real-time Telemetry Metrics",
    width: container.clientWidth || 800,
    height: container.clientHeight || 300,
    scales: {
        x: { time: true },
        y: { auto: true },
        r: { auto: true },
    },
    series: [
        {},
        {
            label: "Price",
            stroke: "#10b981",
            width: 2,
            scale: "y",
        },
        {
            label: "Capital",
            stroke: "#3b82f6",
            width: 2,
            scale: "r",
        },
    ],
    axes: [
        {},
        {
            scale: "y",
            values: (self, ticks) => ticks.map((t) => t.toFixed(2)),
            stroke: "#10b981",
        },
        {
            scale: "r",
            side: 1,
            values: (self, ticks) => ticks.map((t) => t.toFixed(0)),
            stroke: "#3b82f6",
            grid: { show: false },
        },
    ],
};

const plot = new uPlot(opts, data, container);

// Throttled plot redrawing
let needsRedraw = false;
function renderLoop() {
    if (needsRedraw) {
        plot.setData(data);
        needsRedraw = false;
    }
    requestAnimationFrame(renderLoop);
}
requestAnimationFrame(renderLoop);

// Resize observer for responsive charting
new ResizeObserver((entries) => {
    for (let entry of entries) {
        plot.setSize({
            width: entry.contentRect.width,
            height: entry.contentRect.height,
        });
    }
}).observe(container);

let activeSocket = null;
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsHost = window.location.hostname || "127.0.0.1";
const wsPort = 8000;

function connectWebSocket() {
    addLog("System", `Connecting to ws://${wsHost}:${wsPort}/api/telemetry/ws...`);
    const socket = new WebSocket(
        `${wsProtocol}//${wsHost}:${wsPort}/api/telemetry/ws`
    );
    socket.binaryType = "arraybuffer";
    activeSocket = socket;

    socket.onopen = () => {
        dot.className = "pulse-indicator connected";
        addLog("System", "Telemetry WebSocket connection established.");
        wsOfflineBanner.style.display = "none";
    };

    socket.onclose = () => {
        dot.className = "pulse-indicator disconnected";
        addLog("System", "WebSocket connection closed. Reconnecting in 3s...");
        activeSocket = null;
        wsOfflineBanner.style.display = "block";
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = () => {
        addLog("System", "WebSocket error occurred.");
        wsOfflineBanner.style.display = "block";
    };

    socket.onmessage = (event) => {
        const buffer = event.data;
        if (buffer.byteLength < 45) {
            return;
        }

        const view = new DataView(buffer);
        const seqlock = view.getBigUint64(0, true);
        const timestampNs = view.getBigInt64(8, true);
        const strategyId = view.getUint32(16, true);
        const statusFlag = view.getUint8(20);
        const currentPrice = view.getFloat32(21, true);
        const positionSize = view.getFloat32(25, true);
        const unrealizedPnl = view.getFloat32(29, true);
        const realizedPnl = view.getFloat32(33, true);
        const allocatedCapital = view.getFloat32(37, true);
        const payloadLength = view.getUint32(41, true);

        // Update textual metrics cards
        document.getElementById("metric-sequence-id").textContent = seqlock.toString();
        document.getElementById("metric-price").textContent = currentPrice.toFixed(2);
        document.getElementById("metric-position-size").textContent = positionSize.toFixed(2);

        const upnlEl = document.getElementById("metric-unrealized-pnl");
        upnlEl.textContent = unrealizedPnl.toFixed(2);
        upnlEl.className = `metric-value ${unrealizedPnl >= 0 ? "up" : "down"}`;

        const rpnlEl = document.getElementById("metric-realized-pnl");
        rpnlEl.textContent = realizedPnl.toFixed(2);
        rpnlEl.className = `metric-value ${realizedPnl >= 0 ? "up" : "down"}`;

        document.getElementById("metric-capital").textContent = allocatedCapital.toFixed(2);

        // Parse custom payload if present
        let payloadText = "";
        if (payloadLength > 0 && buffer.byteLength >= 45 + payloadLength) {
            const textBuffer = new Uint8Array(buffer, 45, payloadLength);
            payloadText = new TextDecoder().decode(textBuffer);
            addLog(`Strategy #${strategyId}`, payloadText);
        }

        // Add coordinates to uPlot data structure
        const timeSec = Number(timestampNs / 1000000000n);
        data[0].push(timeSec);
        data[1].push(currentPrice);
        data[2].push(allocatedCapital);

        if (data[0].length > 5000) {
            data[0].shift();
            data[1].shift();
            data[2].shift();
        }

        needsRedraw = true;
    };
}

// State management
let activeView = "live"; // "live" | "backtest"
let strategies = [];
let selectedStrategyId = null;
let selectedCompareStrategyId = null;
let latestBacktestResult = null;
let latestCompareResult = null;
let backtestPlot = null;

// Selectors
const tabLive = document.getElementById("tab-live");
const tabBacktest = document.getElementById("tab-backtest");
const liveStreamView = document.getElementById("live-stream-view");
const backtestView = document.getElementById("backtest-view");
const liveStatusNote = document.getElementById("live-status-note");

const strategySelector = document.getElementById("strategy-selector");
const compareStrategySelector = document.getElementById("compare-strategy-selector");
const strategyInfo = document.getElementById("strategy-info");
const exportJsonBtn = document.getElementById("export-json-btn");
const exportCsvBtn = document.getElementById("export-csv-btn");
const runBacktestBtn = document.getElementById("run-backtest-btn");
const backtestStatusMsg = document.getElementById("backtest-status-msg");
const backtestChartContainer = document.getElementById("backtest-chart-container");
const backtestTradesContainer = document.getElementById("backtest-trades-container");
const backtestRegimeContainer = document.getElementById("backtest-regime-container");
const regimeDistributionBar = document.getElementById("regime-distribution-bar");

// Parameter override panel elements
const paramOverridesPanel = document.getElementById("param-overrides-panel");
const resetParamsBtn = document.getElementById("reset-params-btn");
const paramInputs = {
    fast_sma: document.getElementById("param-fast-sma"),
    slow_sma: document.getElementById("param-slow-sma"),
    rsi: document.getElementById("param-rsi"),
    tp: document.getElementById("param-tp"),
    sl: document.getElementById("param-sl"),
    cost: document.getElementById("param-cost"),
    leverage: document.getElementById("param-leverage"),
};

const DEFAULT_PARAMS = {
    fast_sma: 10, slow_sma: 20, rsi: 14,
    tp: 0.01, sl: -0.01, cost: 0.0001, leverage: 1,
};

function fillParamInputsFromDefaults(defaults) {
    Object.entries(paramInputs).forEach(([key, el]) => {
        el.value = defaults[key] ?? "";
    });
}

function buildParamQueryString() {
    const parts = [];
    Object.entries(paramInputs).forEach(([key, el]) => {
        const val = el.value.trim();
        if (val !== "") {
            const def = DEFAULT_PARAMS[key];
            if (String(Number(val)) !== String(def)) {
                parts.push(`${key}=${encodeURIComponent(val)}`);
            }
        }
    });
    return parts.length ? "&" + parts.join("&") : "";
}

resetParamsBtn.addEventListener("click", () => {
    fillParamInputsFromDefaults(DEFAULT_PARAMS);
});
const btObservationsContainer = document.getElementById("bt-observations-container");

// Metadata labels
const btTradesCount = document.getElementById("bt-trades-count");
const btBarsCount = document.getElementById("bt-bars-count");

// Elements for metrics
const btMetricReturn = document.getElementById("bt-metric-return");
const btMetricDrawdown = document.getElementById("bt-metric-drawdown");
const btMetricDdDuration = document.getElementById("bt-metric-dd-duration");
const btMetricWinrate = document.getElementById("bt-metric-winrate");
const btMetricProfitfactor = document.getElementById("bt-metric-profitfactor");
const btSharpeCard = document.getElementById("bt-sharpe-card");
const btMetricSharpe = document.getElementById("bt-metric-sharpe");
const btSortinoCard = document.getElementById("bt-sortino-card");
const btMetricSortino = document.getElementById("bt-metric-sortino");

// Tab Switching logic
tabLive.addEventListener("click", () => {
    if (activeView === "live") return;
    activeView = "live";
    tabLive.classList.add("active");
    tabBacktest.classList.remove("active");
    liveStreamView.classList.replace("view-hidden", "view-active");
    backtestView.classList.replace("view-active", "view-hidden");

    // Resize the live plot
    if (plot) {
        plot.setSize({
            width: container.clientWidth || 800,
            height: container.clientHeight || 300,
        });
    }
});

tabBacktest.addEventListener("click", () => {
    if (activeView === "backtest") return;
    activeView = "backtest";
    tabBacktest.classList.add("active");
    tabLive.classList.remove("active");
    backtestView.classList.replace("view-hidden", "view-active");
    liveStreamView.classList.replace("view-active", "view-hidden");

    // Resize the backtest plot if it exists
    if (backtestPlot) {
        backtestPlot.setSize({
            width: backtestChartContainer.clientWidth || 800,
            height: backtestChartContainer.clientHeight || 300,
        });
    }
});

// Fetch strategies on load
async function fetchStrategies() {
    try {
        const response = await fetch("/api/strategies");
        if (!response.ok) {
            throw new Error(`Failed to load strategies: ${response.statusText}`);
        }
        const data = await response.json();
        strategies = data.strategies || [];
        
        // Hide banner if successful
        apiOfflineBanner.style.display = "none";
        strategySelector.disabled = false;

        // Render strategy selector
        strategySelector.innerHTML = '<option value="">-- Choose Strategy --</option>';
        strategies.forEach((strat) => {
            const isStub = strat.status === "stub";
            const option = document.createElement("option");
            option.value = strat.strategy_id;
            option.textContent = `${strat.strategy_name}${isStub ? " [STUB]" : ""}`;
            strategySelector.appendChild(option);
        });

        // Set status note visibility in Live Stream if a stub strategy exists
        const hasStub = strategies.some(s => s.strategy_name === "CciStrategy" && s.status === "stub");
        if (hasStub) {
            liveStatusNote.style.display = "flex";
        } else {
            liveStatusNote.style.display = "none";
        }
    } catch (err) {
        console.error(err);
        apiOfflineBanner.style.display = "block";
        strategySelector.innerHTML = '<option value="">Failed to load strategies</option>';
        strategySelector.disabled = true;
        runBacktestBtn.disabled = true;
    }
}

function updateCompareSelector() {
    if (!selectedStrategyId || selectedStrategyId === "cci") {
        compareStrategySelector.disabled = true;
        compareStrategySelector.innerHTML = '<option value="">-- No Comparison --</option>';
        selectedCompareStrategyId = null;
        return;
    }

    compareStrategySelector.disabled = false;
    compareStrategySelector.innerHTML = '<option value="">-- No Comparison --</option>';

    // Add only the other legacy strategy as a comparison option
    strategies.forEach((strat) => {
        if (strat.status !== "stub" && strat.strategy_id !== selectedStrategyId) {
            const option = document.createElement("option");
            option.value = strat.strategy_id;
            option.textContent = strat.strategy_name;
            compareStrategySelector.appendChild(option);
        }
    });
}

// Handler for strategy selection
strategySelector.addEventListener("change", (e) => {
    selectedStrategyId = e.target.value;
    updateCompareSelector();
    
    if (!selectedStrategyId) {
        strategyInfo.textContent = "Select a strategy to view configuration details.";
        runBacktestBtn.disabled = true;
        paramOverridesPanel.style.display = "none";
        hideStatusMessage();
        return;
    }

    const strat = strategies.find(s => s.strategy_id === selectedStrategyId);
    if (!strat) return;

    const isStub = strat.status === "stub";
    
    // Build parameters readout safely
    let paramsHtml = "";
    if (strat.parameters) {
        paramsHtml = `<div class="parameter-grid">` + 
            Object.entries(strat.parameters).map(([k, v]) => `
                <div class="parameter-badge">
                    <span class="parameter-badge-name">${k}</span>
                    <span class="parameter-badge-val">${v}</span>
                </div>
            `).join("") + 
            `<div class="parameter-badge"><span class="parameter-badge-name">path</span><span class="parameter-badge-val">${strat.path}</span></div>` +
            `<div class="parameter-badge"><span class="parameter-badge-name">status</span><span class="parameter-badge-val">${strat.status}</span></div>` +
            `<div class="parameter-badge"><span class="parameter-badge-name">regime_aware</span><span class="parameter-badge-val">${strat.regime_aware ? "Yes" : "No"}</span></div>` +
            `</div>`;
    }

    strategyInfo.innerHTML = `
        <strong>Name:</strong> ${strat.strategy_name} <span class="strategy-badge ${isStub ? 'badge-stub' : 'badge-active'}">${strat.status}</span><br>
        ${paramsHtml}
    `;

    if (isStub) {
        runBacktestBtn.disabled = true;
        paramOverridesPanel.style.display = "none";
        showStatusMessage("error", `Backtest unavailable: ${strat.strategy_name} belongs to the zero-alloc streaming path and is currently stub/incomplete.`);
    } else {
        runBacktestBtn.disabled = false;
        paramOverridesPanel.style.display = "block";
        fillParamInputsFromDefaults(strat.parameters || DEFAULT_PARAMS);
        hideStatusMessage();
    }
});

compareStrategySelector.addEventListener("change", (e) => {
    selectedCompareStrategyId = e.target.value || null;
    
    const primaryStrat = strategies.find(s => s.strategy_id === selectedStrategyId);
    if (!primaryStrat) return;
    
    let primaryParamsHtml = "";
    if (primaryStrat.parameters) {
        primaryParamsHtml = `<div class="parameter-grid">` + 
            Object.entries(primaryStrat.parameters).map(([k, v]) => `
                <div class="parameter-badge">
                    <span class="parameter-badge-name">${k}</span>
                    <span class="parameter-badge-val">${v}</span>
                </div>
            `).join("") + 
            `<div class="parameter-badge"><span class="parameter-badge-name">path</span><span class="parameter-badge-val">${primaryStrat.path}</span></div>` +
            `<div class="parameter-badge"><span class="parameter-badge-name">status</span><span class="parameter-badge-val">${primaryStrat.status}</span></div>` +
            `<div class="parameter-badge"><span class="parameter-badge-name">regime_aware</span><span class="parameter-badge-val">${primaryStrat.regime_aware ? "Yes" : "No"}</span></div>` +
            `</div>`;
    }

    let infoText = `
        <strong>Primary Name:</strong> ${primaryStrat.strategy_name} <span class="strategy-badge ${primaryStrat.status === 'stub' ? 'badge-stub' : 'badge-active'}">${primaryStrat.status}</span><br>
        ${primaryParamsHtml}
    `;
    
    if (selectedCompareStrategyId) {
        const compareStrat = strategies.find(s => s.strategy_id === selectedCompareStrategyId);
        if (compareStrat) {
            let compareParamsHtml = "";
            if (compareStrat.parameters) {
                compareParamsHtml = `<div class="parameter-grid">` + 
                    Object.entries(compareStrat.parameters).map(([k, v]) => `
                        <div class="parameter-badge" style="border-color: rgba(245, 158, 11, 0.2); background: rgba(245, 158, 11, 0.08); color: #fde047;">
                            <span class="parameter-badge-name" style="color: var(--text-secondary);">${k}</span>
                            <span class="parameter-badge-val" style="color: var(--text-primary);">${v}</span>
                        </div>
                    `).join("") + 
                    `<div class="parameter-badge" style="border-color: rgba(245, 158, 11, 0.2); background: rgba(245, 158, 11, 0.08); color: #fde047;"><span class="parameter-badge-name">path</span><span class="parameter-badge-val">${compareStrat.path}</span></div>` +
                    `<div class="parameter-badge" style="border-color: rgba(245, 158, 11, 0.2); background: rgba(245, 158, 11, 0.08); color: #fde047;"><span class="parameter-badge-name">status</span><span class="parameter-badge-val">${compareStrat.status}</span></div>` +
                    `<div class="parameter-badge" style="border-color: rgba(245, 158, 11, 0.2); background: rgba(245, 158, 11, 0.08); color: #fde047;"><span class="parameter-badge-name">regime_aware</span><span class="parameter-badge-val">${compareStrat.regime_aware ? "Yes" : "No"}</span></div>` +
                    `</div>`;
            }
            infoText += `
                <br><strong>Comparison Name:</strong> ${compareStrat.strategy_name} <span class="strategy-badge ${compareStrat.status === 'stub' ? 'badge-stub' : 'badge-active'}">${compareStrat.status}</span><br>
                ${compareParamsHtml}
            `;
        }
    }
    
    strategyInfo.innerHTML = infoText;
});

function showStatusMessage(type, text) {
    backtestStatusMsg.className = `status-message ${type}`;
    backtestStatusMsg.textContent = text;
    backtestStatusMsg.style.display = "block";
}

function hideStatusMessage() {
    backtestStatusMsg.style.display = "none";
}

// Helper to safely format and set metric value (handling comparison mode)
function setMetricValue(el, primaryVal, compareVal, suffix = "") {
    el.innerHTML = "";
    
    const formatVal = (v) => {
        if (v === null || v === undefined || isNaN(v)) return "Unavailable";
        if (typeof v === "number") return v.toFixed(2);
        return v;
    };

    if (compareVal !== undefined && compareVal !== null) {
        const wrapper = document.createElement("div");
        wrapper.className = "metric-comparison";
        
        const primaryCol = document.createElement("div");
        primaryCol.className = "metric-comp-col";
        primaryCol.innerHTML = `
            <span class="metric-comp-label">Primary</span>
            <span class="metric-value primary-color">${formatVal(primaryVal)}${primaryVal !== null && primaryVal !== undefined && !isNaN(primaryVal) ? suffix : ""}</span>
        `;
        
        const compareCol = document.createElement("div");
        compareCol.className = "metric-comp-col";
        compareCol.innerHTML = `
            <span class="metric-comp-label">Compare</span>
            <span class="metric-value compare-color">${formatVal(compareVal)}${compareVal !== null && compareVal !== undefined && !isNaN(compareVal) ? suffix : ""}</span>
        `;
        
        wrapper.appendChild(primaryCol);
        wrapper.appendChild(compareCol);
        el.appendChild(wrapper);
    } else {
        const val = formatVal(primaryVal);
        const isUnavailable = val === "Unavailable";
        el.textContent = `${val}${!isUnavailable ? suffix : ""}`;
        el.className = isUnavailable ? "metric-value unavailable-value" : "metric-value";
    }
}

// Run Backtest action
runBacktestBtn.addEventListener("click", async () => {
    if (!selectedStrategyId) return;
    
    // Clear previous results or plots
    if (backtestPlot) {
        backtestPlot.destroy();
        backtestPlot = null;
    }
    backtestChartContainer.innerHTML = "";
    backtestTradesContainer.innerHTML = '<div class="status-message empty">No backtest run yet.</div>';
    backtestRegimeContainer.innerHTML = '<div class="status-message empty" style="padding: 0.5rem; font-size: 0.8rem;">No regime data.</div>';
    regimeDistributionBar.innerHTML = '<span class="regime-dist-empty">No distribution data available.</span>';
    resetMetrics();

    if (btObservationsContainer) {
        btObservationsContainer.innerHTML = '<div class="status-message loading" style="padding: 0.5rem; font-size: 0.8rem;">Generating observations...</div>';
    }

    showStatusMessage("loading", "Loading backtest...");
    runBacktestBtn.disabled = true;

    try {
        let result = null;
        let compareResult = null;

        // Fetch primary backtest (append non-default param overrides)
        const paramQs = buildParamQueryString();
        const response = await fetch(`/api/backtest/${selectedStrategyId}${paramQs ? "?" + paramQs.slice(1) : ""}`);
        if (!response.ok) {
            let errorMsg = `Server error: ${response.status}`;
            try {
                const errorJson = await response.json();
                if (errorJson.detail) errorMsg = errorJson.detail;
            } catch (_) {}
            throw new Error(`Primary strategy failed: ${errorMsg}`);
        }
        result = await response.json();
        latestBacktestResult = result;

        // Fetch comparison backtest if selected
        if (selectedCompareStrategyId) {
            const compareResponse = await fetch(`/api/backtest/${selectedCompareStrategyId}`);
            if (!compareResponse.ok) {
                let errorMsg = `Server error: ${compareResponse.status}`;
                try {
                    const errorJson = await compareResponse.json();
                    if (errorJson.detail) errorMsg = errorJson.detail;
                } catch (_) {}
                throw new Error(`Comparison strategy failed: ${errorMsg}`);
            }
            compareResult = await compareResponse.json();
            latestCompareResult = compareResult;
        } else {
            latestCompareResult = null;
        }
        
        hideStatusMessage();

        // Check if there are bars processed or equity curve
        if (!result.equity_curve || result.equity_curve.length === 0) {
            showStatusMessage("empty", "No trades found in the simulation.");
            return;
        }

        renderBacktestResults(result, compareResult);
    } catch (err) {
        showStatusMessage("error", `Backtest failed: ${err.message}`);
    } finally {
        runBacktestBtn.disabled = false;
    }
});

function resetMetrics() {
    // Hide export buttons
    exportJsonBtn.style.display = "none";
    exportJsonBtn.disabled = true;
    exportCsvBtn.style.display = "none";
    exportCsvBtn.disabled = true;

    setMetricValue(btMetricReturn, null, null);
    setMetricValue(btMetricDrawdown, null, null);
    setMetricValue(btMetricDdDuration, null, null);
    setMetricValue(btMetricWinrate, null, null);
    setMetricValue(btMetricProfitfactor, null, null);
    
    setMetricValue(btMetricSharpe, null, null);
    const explainSharpe = btSharpeCard.querySelector(".metric-explain");
    if (explainSharpe) explainSharpe.remove();
    
    setMetricValue(btMetricSortino, null, null);
    const explainSortino = btSortinoCard.querySelector(".metric-explain");
    if (explainSortino) explainSortino.remove();

    btTradesCount.textContent = "0 Trades";
    btBarsCount.textContent = "0 Bars";

    if (btObservationsContainer) {
        btObservationsContainer.innerHTML = '<div class="status-message empty" style="padding: 0.5rem; font-size: 0.8rem;">No observations generated yet.</div>';
    }
}

function renderBacktestResults(result, compareResult) {
    // 1. Render Metrics & Update Counters
    const metrics = result.metrics;
    const compareMetrics = compareResult ? compareResult.metrics : null;
    
    btTradesCount.textContent = `${result.trades ? result.trades.length : 0} Trades`;
    btBarsCount.textContent = `${result.bars_processed || 0} Bars`;

    if (metrics) {
        setMetricValue(btMetricReturn, metrics.total_return * 100, compareMetrics ? compareMetrics.total_return * 100 : null, "%");
        setMetricValue(btMetricDrawdown, metrics.max_drawdown * 100, compareMetrics ? compareMetrics.max_drawdown * 100 : null, "%");
        setMetricValue(btMetricDdDuration, metrics.drawdown_duration_bars, compareMetrics ? compareMetrics.drawdown_duration_bars : null, " bars");
        setMetricValue(btMetricWinrate, metrics.win_rate * 100, compareMetrics ? compareMetrics.win_rate * 100 : null, "%");
        setMetricValue(btMetricProfitfactor, metrics.profit_factor, compareMetrics ? compareMetrics.profit_factor : null);

        // Clear any old explanations
        const oldExplainS = btSharpeCard.querySelector(".metric-explain");
        if (oldExplainS) oldExplainS.remove();
        const oldExplainSo = btSortinoCard.querySelector(".metric-explain");
        if (oldExplainSo) oldExplainSo.remove();

        // Sharpe Ratio Card
        setMetricValue(btMetricSharpe, metrics.sharpe_ratio, compareMetrics ? compareMetrics.sharpe_ratio : null);
        const pNumTrades = result.trades ? result.trades.length : 0;
        const cNumTrades = compareResult && compareResult.trades ? compareResult.trades.length : 0;

        if (pNumTrades < 10 || (compareResult && cNumTrades < 10)) {
            const explain = document.createElement("span");
            explain.className = "metric-explain";
            explain.textContent = "Insufficient observations (< 10) for Sharpe/Sortino ratios.";
            btSharpeCard.appendChild(explain);
        }

        // Sortino Ratio Card
        setMetricValue(btMetricSortino, metrics.sortino_ratio, compareMetrics ? compareMetrics.sortino_ratio : null);
    }

    // 2. Render Equity Curve Chart
    const timestamps = result.per_bar.map(r => {
        if (r.timestamp_ns) {
            return Number(BigInt(r.timestamp_ns) / 1000000000n);
        }
        return Math.floor(Date.now() / 1000); // fallback
    });

    let finalTimestamps = timestamps;
    let primaryEquity = result.equity_curve;
    let compareEquity = compareResult ? compareResult.equity_curve : null;

    if (compareResult) {
        // Alignment Strategy: Truncate to shortest common length
        const minLen = Math.min(primaryEquity.length, compareEquity.length);
        primaryEquity = primaryEquity.slice(0, minLen);
        compareEquity = compareEquity.slice(0, minLen);
        finalTimestamps = timestamps.slice(0, minLen);
    }

    const equityData = [
        finalTimestamps,
        primaryEquity
    ];
    if (compareResult) {
        equityData.push(compareEquity);
    }

    const primaryName = result.strategy_id === "rsi_sma" ? "RsiSma" : "RsiSmaRegime";
    const compareName = compareResult ? (compareResult.strategy_id === "rsi_sma" ? "RsiSma" : "RsiSmaRegime") : "";

    const btOpts = {
        title: compareResult ? `Equity Curve Overlay (${primaryName} vs ${compareName})` : "Equity Curve",
        width: backtestChartContainer.clientWidth || 800,
        height: backtestChartContainer.clientHeight || 300,
        scales: {
            x: { time: true },
            y: { auto: true }
        },
        series: [
            {},
            {
                label: primaryName,
                stroke: "#3b82f6",
                width: 2
            }
        ],
        axes: [
            {},
            {
                values: (self, ticks) => ticks.map((t) => t.toFixed(2)),
                stroke: "#3b82f6"
            }
        ]
    };

    if (compareResult) {
        btOpts.series.push({
            label: compareName,
            stroke: "#f59e0b",
            width: 2
        });
    }

    // Safe instance creation
    if (backtestPlot) {
        backtestPlot.destroy();
    }
    backtestPlot = new uPlot(btOpts, equityData, backtestChartContainer);

    // 3. Render Trades Log (Primary strategy only)
    if (!result.trades || result.trades.length === 0) {
        backtestTradesContainer.innerHTML = '<div class="status-message empty">No trades found in the simulation.</div>';
    } else {
        const table = document.createElement("table");
        table.className = "trade-table";
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Entry Index</th>
                    <th>Exit Index</th>
                    <th>Entry Price</th>
                    <th>Exit Price</th>
                    <th>PnL</th>
                    <th>Return</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        `;
        const tbody = table.querySelector("tbody");
        result.trades.forEach(t => {
            const pnl = t.pnl || 0;
            const ret = t.exit_return || 0;
            const rowClass = pnl >= 0 ? "profit" : "loss";
            const row = document.createElement("tr");
            row.className = `trade-row ${rowClass}`;
            row.innerHTML = `
                <td><strong>${t.position_size > 0 ? "BUY" : "SELL"}</strong></td>
                <td>${t.entry_idx}</td>
                <td>${t.exit_idx}</td>
                <td>${t.entry_price.toFixed(2)}</td>
                <td>${t.exit_price ? t.exit_price.toFixed(2) : "Open"}</td>
                <td>${pnl.toFixed(2)}</td>
                <td>${(ret * 100).toFixed(2)}%</td>
            `;
            tbody.appendChild(row);
        });
        backtestTradesContainer.innerHTML = "";
        backtestTradesContainer.appendChild(table);
    }

    // 4. Render Regime Display & Distribution Summaries
    if (!result.regime_timeline || result.regime_timeline.length === 0) {
        backtestRegimeContainer.innerHTML = '<div class="status-message empty" style="padding: 0.5rem; font-size: 0.8rem;">No regime data.</div>';
        regimeDistributionBar.innerHTML = '<span class="regime-dist-empty">No distribution data available.</span>';
    } else {
        // Collect consecutive regime blocks to present cleanly
        const blocks = [];
        const distributionCounts = {};
        let currentRegime = null;
        let startIdx = 0;

        result.regime_timeline.forEach((reg, idx) => {
            // Count for distribution summary
            distributionCounts[reg] = (distributionCounts[reg] || 0) + 1;

            if (reg !== currentRegime) {
                if (currentRegime !== null) {
                    blocks.push({ regime: currentRegime, start: startIdx, end: idx - 1 });
                }
                currentRegime = reg;
                startIdx = idx;
            }
        });
        if (currentRegime !== null) {
            blocks.push({ regime: currentRegime, start: startIdx, end: result.regime_timeline.length - 1 });
        }

        // Render Distribution percentages
        const totalBars = result.regime_timeline.length;
        regimeDistributionBar.innerHTML = "";
        
        // Define color scheme for regimes
        const regimeColors = {
            "bull": "#10b981",
            "bear": "#ef4444",
            "neutral": "#6b7280",
            "unknown": "#374151"
        };

        Object.keys(distributionCounts).forEach(key => {
            const count = distributionCounts[key];
            const pct = ((count / totalBars) * 100).toFixed(1);
            const segment = document.createElement("div");
            segment.className = "regime-segment";
            const color = regimeColors[key.toLowerCase()] || regimeColors["unknown"];
            segment.style.backgroundColor = color;
            segment.style.width = `${pct}%`;
            segment.title = `${key}: ${count} bars (${pct}%)`;
            segment.textContent = pct >= 8 ? `${key} (${pct}%)` : `${pct}%`;
            regimeDistributionBar.appendChild(segment);
        });

        backtestRegimeContainer.innerHTML = "";
        const recentBlocks = blocks.slice(-15).reverse(); // Show last 15 regime changes
        recentBlocks.forEach(b => {
            const item = document.createElement("div");
            item.className = "regime-item";
            item.innerHTML = `Bar ${b.start} - ${b.end}: <strong>${b.regime}</strong>`;
            backtestRegimeContainer.appendChild(item);
        });
    }

    // Show export buttons when backtest is successfully loaded
    exportJsonBtn.style.display = "inline-block";
    exportJsonBtn.disabled = false;
    exportCsvBtn.style.display = "inline-block";
    exportCsvBtn.disabled = false;

    // Render Observations & Metadata
    renderObservationsAndMetadata(result, compareResult);
}

function renderObservationsAndMetadata(result, compareResult) {
    if (!btObservationsContainer) return;
    
    const primaryName = result.strategy_id === "rsi_sma" ? "RsiSma" : "RsiSmaRegime";
    const compareName = compareResult ? (compareResult.strategy_id === "rsi_sma" ? "RsiSma" : "RsiSmaRegime") : "";
    
    const isComparison = !!compareResult;
    const timestamp = new Date().toLocaleString();
    
    let metadataHtml = `
        <div class="metadata-grid">
            <div class="metadata-row">
                <strong>Strategy ID:</strong>
                <span>${result.strategy_id}</span>
            </div>
            <div class="metadata-row">
                <strong>Strategy Name:</strong>
                <span>${primaryName}</span>
            </div>
            <div class="metadata-row">
                <strong>Path:</strong>
                <span>${result.strategy_id === "cci" ? "zero_alloc" : "legacy"}</span>
            </div>
            <div class="metadata-row">
                <strong>Status:</strong>
                <span>research_only</span>
            </div>
            <div class="metadata-row">
                <strong>Bars Processed:</strong>
                <span>${result.bars_processed || 0}</span>
            </div>
            <div class="metadata-row">
                <strong>Trade Count:</strong>
                <span>${result.trades ? result.trades.length : 0}</span>
            </div>
            <div class="metadata-row">
                <strong>Comparison:</strong>
                <span>${isComparison ? "Enabled" : "Disabled"}</span>
            </div>
            <div class="metadata-row">
                <strong>Alignment:</strong>
                <span>${isComparison ? "Shortest common length" : "None (Single Run)"}</span>
            </div>
            <div class="metadata-row" style="grid-column: 1 / -1;">
                <strong>Export Timestamp:</strong>
                <span>${timestamp}</span>
            </div>
            ${result.parameters_used ? `
            <div class="metadata-row" style="grid-column: 1 / -1;">
                <strong>Parameters Used:</strong>
                <div class="parameter-grid" style="margin-top: 0.25rem;">
                    ${Object.entries(result.parameters_used).map(([k, v]) => `
                        <div class="parameter-badge">
                            <span class="parameter-badge-name">${k}</span>
                            <span class="parameter-badge-val">${v}</span>
                        </div>
                    `).join("")}
                </div>
            </div>
            ${isComparison ? `<div class="metadata-row" style="grid-column: 1 / -1; font-size: 0.75rem; color: var(--text-muted, #aaa);">Comparison strategy runs with default parameters.</div>` : ""}
            ` : ""}
        </div>
    `;

    let observations = [];
    
    // Always show baseline context as required:
    // "Both strategies are legacy research backtests only."
    observations.push({
        type: "info",
        text: "Both strategies are legacy research backtests only."
    });
    
    if (isComparison) {
        // "Comparison curves are aligned by shortest common length."
        observations.push({
            type: "info",
            text: "Comparison curves are aligned by shortest common length."
        });
        
        // comparative drawdown observations using precise wording:
        // "RsiSmaRegime has lower max drawdown than RsiSma in this backtest result."
        const pDrawdown = result.metrics ? result.metrics.max_drawdown : null;
        const cDrawdown = compareResult.metrics ? compareResult.metrics.max_drawdown : null;
        if (pDrawdown !== null && cDrawdown !== null) {
            if (pDrawdown < cDrawdown) {
                observations.push({
                    type: "info",
                    text: `${primaryName} has lower max drawdown than ${compareName} in this backtest result.`
                });
            } else if (cDrawdown < pDrawdown) {
                observations.push({
                    type: "info",
                    text: `${compareName} has lower max drawdown than ${primaryName} in this backtest result.`
                });
            }
        }
        
        // comparative trade completed trade counts:
        // "RsiSma has more completed trades than RsiSmaRegime in this backtest result."
        const pTrades = result.trades ? result.trades.length : 0;
        const cTrades = compareResult.trades ? compareResult.trades.length : 0;
        if (pTrades !== cTrades) {
            if (pTrades > cTrades) {
                observations.push({
                    type: "info",
                    text: `${primaryName} has more completed trades than ${compareName} in this backtest result.`
                });
            } else {
                observations.push({
                    type: "info",
                    text: `${compareName} has more completed trades than ${primaryName} in this backtest result.`
                });
            }
        }
    }
    
    // Sharpe observations using precise wording:
    // "Sharpe ratio is unavailable because there are fewer than 10 observations."
    const pTradesCount = result.trades ? result.trades.length : 0;
    const cTradesCount = compareResult && compareResult.trades ? compareResult.trades.length : 0;
    if (pTradesCount < 10 || (isComparison && cTradesCount < 10)) {
        observations.push({
            type: "warning",
            text: "Sharpe ratio is unavailable because there are fewer than 10 observations."
        });
    }

    let observationsListHtml = `
        <div class="observations-list" style="margin-top: 0.75rem;">
            ${observations.map(o => `
                <div class="observation-item ${o.type}">
                    ${o.text}
                </div>
            `).join("")}
        </div>
    `;

    btObservationsContainer.innerHTML = metadataHtml + observationsListHtml;
}

// Wire up Export Buttons
exportJsonBtn.addEventListener("click", () => {
    if (!latestBacktestResult) return;
    
    let exportObj = latestBacktestResult;
    if (latestCompareResult) {
        exportObj = {
            primary: latestBacktestResult,
            comparison: latestCompareResult
        };
    }

    const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `alpha_kd_backtest_${selectedStrategyId}${selectedCompareStrategyId ? "_vs_" + selectedCompareStrategyId : ""}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

exportCsvBtn.addEventListener("click", () => {
    if (!latestBacktestResult) return;

    let csv = "Strategy,Type,Entry Index,Exit Index,Entry Price,Exit Price,PnL,Return\n";
    
    const appendTrades = (strategyName, trades) => {
        if (!trades) return;
        trades.forEach(t => {
            const typeStr = t.position_size > 0 ? "BUY" : "SELL";
            const entryIdx = t.entry_idx;
            const exitIdx = t.exit_idx !== undefined && t.exit_idx !== null ? t.exit_idx : "";
            const entryPrice = t.entry_price;
            const exitPrice = t.exit_price !== undefined && t.exit_price !== null ? t.exit_price : "";
            const pnl = t.pnl !== undefined && t.pnl !== null ? t.pnl : "";
            const ret = t.exit_return !== undefined && t.exit_return !== null ? t.exit_return : "";
            csv += `"${strategyName}","${typeStr}",${entryIdx},${exitIdx},${entryPrice},${exitPrice},${pnl},${ret}\n`;
        });
    };

    const primaryName = latestBacktestResult.strategy_id === "rsi_sma" ? "RsiSma" : "RsiSmaRegime";
    appendTrades(primaryName, latestBacktestResult.trades);

    if (latestCompareResult) {
        const compareName = latestCompareResult.strategy_id === "rsi_sma" ? "RsiSma" : "RsiSmaRegime";
        appendTrades(compareName, latestCompareResult.trades);
    }

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `alpha_kd_trades_${selectedStrategyId}${selectedCompareStrategyId ? "_vs_" + selectedCompareStrategyId : ""}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Observe Backtest chart resizing
new ResizeObserver((entries) => {
    for (let entry of entries) {
        if (backtestPlot && activeView === "backtest") {
            backtestPlot.setSize({
                width: entry.contentRect.width,
                height: entry.contentRect.height,
            });
        }
    }
}).observe(backtestChartContainer);

// Initialize setup
fetchStrategies();
connectWebSocket();

