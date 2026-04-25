const { useState, useEffect, useRef, useCallback } = React;
const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } = Recharts;

// Use relative path so it works on HuggingFace Spaces and locally
const API = "";

/* ─── helpers ─── */
const sev = (s) => ({ HIGH: "high", MEDIUM: "medium", LOW: "low" }[s] || "low");
const sevColor = (s) => ({ HIGH: "#f87171", MEDIUM: "#facc15", LOW: "#4ade80" }[s] || "#4ade80");
const sevOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
const statusColor = (s) => ({ idle: "#94a3b8", working: "#facc15", done: "#4ade80", failed: "#f87171" }[s] || "#94a3b8");
const ts = (t) => { try { return new Date(t).toLocaleTimeString(); } catch { return t; } };

/* ─── LogCard ─── */
function LogCard({ log, idx }) {
  const resolved = log.resolved;
  return (
    <div
      className={`glass-bright rounded-xl p-4 card-hover slide-in ${log.severity === "HIGH" && !resolved ? "glow-red" : ""}`}
      style={{ animationDelay: `${idx * 0.04}s`, opacity: resolved ? 0.45 : 1, transition: "opacity .4s" }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`badge-${sev(log.severity)} text-xs font-bold px-2 py-0.5 rounded-full font-mono`}>
              {log.severity}
            </span>
            {resolved && (
              <span className="bg-emerald-900/30 text-emerald-400 border border-emerald-500/30 text-xs px-2 py-0.5 rounded-full">
                ✓ RESOLVED
              </span>
            )}
            <span className="text-slate-500 text-xs font-mono">{ts(log.timestamp)}</span>
          </div>
          <p className="text-sm font-semibold text-slate-100 truncate">{log.title}</p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">{log.description}</p>
        </div>
        <div className="shrink-0 text-right">
          <span className="text-slate-600 text-xs font-mono">#{log.id}</span>
        </div>
      </div>
    </div>
  );
}

/* ─── LogsPanel ─── */
function LogsPanel({ logs }) {
  const sorted = [...logs].sort((a, b) => (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9));
  const counts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
  logs.forEach(l => { if (counts[l.severity] !== undefined) counts[l.severity]++; });
  const unresolved = logs.filter(l => !l.resolved).length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div className="flex items-center gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 tracking-wide">INCIDENT LOGS</h2>
            <p className="text-xs text-slate-500">{unresolved} active · {logs.length - unresolved} resolved</p>
          </div>
        </div>
        <div className="flex gap-2 text-xs font-mono">
          <span className="badge-high px-2 py-1 rounded-lg">{counts.HIGH} HIGH</span>
          <span className="badge-medium px-2 py-1 rounded-lg">{counts.MEDIUM} MED</span>
          <span className="badge-low px-2 py-1 rounded-lg">{counts.LOW} LOW</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {sorted.length === 0
          ? <div className="text-center text-slate-600 py-8 text-sm">No logs available</div>
          : sorted.map((log, i) => <LogCard key={log.id} log={log} idx={i} />)}
      </div>
    </div>
  );
}

/* ─── AgentCard ─── */
function AgentCard({ name, agent }) {
  const icons = { Manager: "🧠", Monitor: "🔍", Engineer: "⚙️" };
  const sc = statusColor(agent.status);
  return (
    <div className="glass-bright rounded-xl p-5 card-hover flex-1 min-w-0 fade-in">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{icons[name] || "🤖"}</span>
          <span className="font-bold text-sm text-slate-100 tracking-wide uppercase">{name}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="pulse-dot w-2 h-2 rounded-full" style={{ background: sc }} />
          <span className="text-xs font-mono uppercase" style={{ color: sc }}>{agent.status}</span>
        </div>
      </div>
      <div className="mb-2">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-0.5">Action</p>
        <p className="text-xs font-mono text-indigo-300 bg-indigo-950/40 px-2 py-1 rounded-md truncate">
          {agent.current_action || "—"}
        </p>
      </div>
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-0.5">Reasoning</p>
        <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">{agent.message || "—"}</p>
      </div>
    </div>
  );
}

/* ─── RewardChart ─── */
function RewardChart({ history }) {
  const data = history.map((r, i) => ({ step: i + 1, reward: r }));
  const total = history.reduce((a, b) => a + b, 0);
  const last = history[history.length - 1] ?? 0;

  return (
    <div className="glass-bright rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div>
          <h3 className="text-sm font-bold text-slate-100 tracking-wide">REWARD HISTORY</h3>
          <p className="text-xs text-slate-500">{history.length} steps</p>
        </div>
        <div className="flex gap-4 text-right">
          <div>
            <p className="text-xs text-slate-500">Total</p>
            <p className={`text-sm font-bold font-mono ${total >= 0 ? "text-emerald-400" : "text-red-400"}`}>{total > 0 ? "+" : ""}{total}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Last</p>
            <p className={`text-sm font-bold font-mono ${last >= 0 ? "text-emerald-400" : "text-red-400"}`}>{last > 0 ? "+" : ""}{last}</p>
          </div>
        </div>
      </div>
      <div className="flex-1">
        {data.length === 0
          ? <div className="flex items-center justify-center h-full text-slate-600 text-sm">No reward data yet</div>
          : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.07)" />
                <XAxis dataKey="step" tick={{ fill: "#64748b", fontSize: 10 }} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid rgba(148,163,184,0.15)", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#94a3b8" }}
                  itemStyle={{ color: "#818cf8" }}
                />
                <ReferenceLine y={0} stroke="rgba(148,163,184,0.2)" strokeDasharray="4 4" />
                <Line
                  type="monotone" dataKey="reward" stroke="#818cf8" strokeWidth={2}
                  dot={{ r: 3, fill: "#818cf8", strokeWidth: 0 }}
                  activeDot={{ r: 5, fill: "#a5b4fc" }}
                  isAnimationActive={true}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
      </div>
    </div>
  );
}

/* ─── Controls ─── */
function Controls({ isRunning, systemStatus, onStep, onRun, onStop, onReset }) {
  const [agent, setAgent] = useState("manager");
  const [action, setAction] = useState("prioritize");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [steps, setSteps] = useState(10);

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleStep = async () => {
    setLoading(true);
    try {
      await onStep(agent, action, message || `${agent} executing ${action}`);
      showToast("Step executed", "success");
      setMessage("");
    } catch (e) {
      showToast(e.message, "error");
    } finally { setLoading(false); }
  };

  const handleRun = async () => {
    try { await onRun(steps); showToast(`Autonomous loop started (${steps} steps)`, "success"); }
    catch (e) { showToast(e.message, "error"); }
  };

  const handleStop = async () => {
    try { await onStop(); showToast("Stop signal sent", "success"); }
    catch (e) { showToast(e.message, "error"); }
  };

  const handleReset = async () => {
    try { await onReset(); showToast("Environment reset", "success"); }
    catch (e) { showToast(e.message, "error"); }
  };

  const actionOptions = {
    manager: ["prioritize", "monitor_queue", "escalate"],
    monitor: ["scan", "anomaly_detect", "flag"],
    engineer: ["resolve", "investigate", "patch"],
  };

  const sysColors = { idle: "#94a3b8", running: "#facc15", resolved: "#4ade80", failed: "#f87171" };

  return (
    <div className="glass-bright rounded-xl p-5 flex flex-col gap-4 h-full relative">
      {/* Toast */}
      {toast && (
        <div className={`absolute top-3 right-3 z-50 text-xs px-3 py-2 rounded-lg font-medium fade-in
          ${toast.type === "success" ? "bg-emerald-900/80 text-emerald-300 border border-emerald-500/30" : "bg-red-900/80 text-red-300 border border-red-500/30"}`}>
          {toast.msg}
        </div>
      )}

      {/* System status */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-100 tracking-wide">CONTROLS</h3>
        <div className="flex items-center gap-2">
          <span className="pulse-dot w-2 h-2 rounded-full" style={{ background: sysColors[systemStatus] || "#94a3b8" }} />
          <span className="text-xs font-mono uppercase" style={{ color: sysColors[systemStatus] || "#94a3b8" }}>{systemStatus}</span>
        </div>
      </div>

      {/* Manual mode */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Manual Mode</p>
        <div className="space-y-2">
          <div className="flex gap-2">
            <select
              value={agent} onChange={e => setAgent(e.target.value)}
              disabled={isRunning}
              className="flex-1 text-xs rounded-lg px-3 py-2 font-mono disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <option value="manager">Manager</option>
              <option value="monitor">Monitor</option>
              <option value="engineer">Engineer</option>
            </select>
            <select
              value={action} onChange={e => setAction(e.target.value)}
              disabled={isRunning}
              className="flex-1 text-xs rounded-lg px-3 py-2 font-mono disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {(actionOptions[agent] || []).map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <input
            type="text" placeholder="Reasoning message (optional)"
            value={message} onChange={e => setMessage(e.target.value)}
            disabled={isRunning}
            className="w-full text-xs rounded-lg px-3 py-2 disabled:opacity-40 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleStep}
            disabled={isRunning || loading}
            className="w-full btn-primary text-white text-xs font-semibold py-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "Executing…" : "⚡ Execute Step"}
          </button>
        </div>
      </div>

      <div className="border-t border-slate-700/50" />

      {/* Auto mode */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Autonomous Mode</p>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-slate-400">Steps:</span>
          <input
            type="number" min={1} max={50} value={steps}
            onChange={e => setSteps(Number(e.target.value))}
            disabled={isRunning}
            className="w-16 text-xs rounded-lg px-2 py-1 text-center font-mono disabled:opacity-40"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex-1 btn-green text-white text-xs font-semibold py-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <span className="flex items-center justify-center gap-1.5">
                <span className="pulse-dot w-1.5 h-1.5 bg-white rounded-full inline-block" /> Running…
              </span>
            ) : "▶ Run AI Agents"}
          </button>
          <button
            onClick={handleStop}
            disabled={!isRunning}
            className="flex-1 btn-danger text-white text-xs font-semibold py-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ■ Stop
          </button>
        </div>
      </div>

      <div className="border-t border-slate-700/50 mt-auto" />

      <button
        onClick={handleReset}
        className="w-full btn-gray text-slate-300 text-xs font-semibold py-2 rounded-lg"
      >
        ↺ Reset Environment
      </button>
    </div>
  );
}

/* ─── App ─── */
function App() {
  const [state, setState] = useState({ logs: [], agents: { manager: {}, monitor: {}, engineer: {} }, reward_history: [], system_status: "idle" });
  const [isRunning, setIsRunning] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const pollRef = useRef(null);

  const fetchState = useCallback(async () => {
    try {
      const r = await fetch(`${API}/state`);
      if (!r.ok) return;
      const d = await r.json();
      setState(d);
      setIsRunning(d.system_status === "running");
      setLastUpdated(new Date());
    } catch {}
  }, []);

  useEffect(() => {
    fetchState();
    pollRef.current = setInterval(fetchState, 2000);
    return () => clearInterval(pollRef.current);
  }, [fetchState]);

  const postStep = async (agent, action, message) => {
    const r = await fetch(`${API}/step`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent, action, message }) });
    if (!r.ok) throw new Error((await r.json()).detail || "Step failed");
    fetchState();
  };

  const postRun = async (steps) => {
    const r = await fetch(`${API}/run_agents`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ steps }) });
    if (!r.ok) throw new Error((await r.json()).detail || "Run failed");
    fetchState();
  };

  const postStop = async () => {
    await fetch(`${API}/stop_agents`, { method: "POST" });
    fetchState();
  };

  const postReset = async () => {
    await fetch(`${API}/reset`, { method: "POST" });
    fetchState();
  };

  const agents = state.agents || {};

  return (
    <div className="min-h-screen flex flex-col p-4 gap-4">
      {/* Header */}
      <header className="glass rounded-xl px-5 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-sm">🛡️</div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 tracking-widest uppercase">Incident Response</h1>
            <p className="text-xs text-slate-500">Multi-Agent SOC Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LIVE
          </span>
          {lastUpdated && <span>{lastUpdated.toLocaleTimeString()}</span>}
        </div>
      </header>

      {/* Main: top half logs, bottom half agents+controls+chart */}
      <div className="flex-1 grid grid-rows-2 gap-4 min-h-0" style={{ gridTemplateRows: "1fr 1fr" }}>

        {/* TOP — Logs */}
        <div className="glass rounded-xl p-4 min-h-0">
          <LogsPanel logs={state.logs} />
        </div>

        {/* BOTTOM — Agents + Controls + Chart */}
        <div className="grid gap-4 min-h-0" style={{ gridTemplateColumns: "1fr 1fr 1fr 1.1fr 1.3fr" }}>
          <AgentCard name="Manager" agent={agents.manager || {}} />
          <AgentCard name="Monitor" agent={agents.monitor || {}} />
          <AgentCard name="Engineer" agent={agents.engineer || {}} />
          <Controls
            isRunning={isRunning}
            systemStatus={state.system_status}
            onStep={postStep}
            onRun={postRun}
            onStop={postStop}
            onReset={postReset}
          />
          <RewardChart history={state.reward_history} />
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
