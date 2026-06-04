import uPlot from "uplot";
import "./style.css";

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get("session-id") || "local-dev";
document.getElementById("session-id-val").textContent = sessionId;

const consoleEl = document.getElementById("logs-console");
const dot = document.getElementById("connection-status-dot");

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
    };

    socket.onclose = () => {
        dot.className = "pulse-indicator disconnected";
        addLog("System", "WebSocket connection closed. Reconnecting in 3s...");
        activeSocket = null;
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = () => {
        addLog("System", "WebSocket error occurred.");
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

connectWebSocket();
