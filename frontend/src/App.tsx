import { useState, useRef, useEffect, type CSSProperties } from 'react';
import axios from 'axios';

// ────────────────────────────────────────────
// Types
// ────────────────────────────────────────────
interface DirectiveInterp {
  note_index: number;
  applies: boolean;
  directive_type: string;
  structured_adjustment: Record<string, unknown> | null;
  explanation: string;
}
interface HourlyPlan {
  hour: number;
  grid_kwh: number;
  solar_used_kwh: number;
  battery_action: 'charge' | 'discharge' | 'idle';
  battery_kwh: number;
  battery_energy_after_kwh: number;
}
interface ApiResponse {
  scenario_id: string;
  directive_interpretation: DirectiveInterp[];
  hourly_plan: HourlyPlan[];
  total_grid_kwh: number;
  total_cost_bdt: number;
  peak_grid_kwh: number;
  plan_summary: string;
}

// ────────────────────────────────────────────
// Demo scenario for "Try Example"
// ────────────────────────────────────────────
const DEMO_INPUT = {
  scenario_id: "DEMO-01",
  operator_notes: [
    "Facilities will wash the rooftop solar panels from noon until 2 PM. During cleaning, usable solar should be treated as roughly 25% of the forecast.",
    "The sports office moved next month's registration deadline."
  ],
  hours: Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    demand_kwh: [90,85,80,78,82,95,130,180,220,200,190,175,165,170,185,210,230,240,220,195,160,130,110,95][h],
    solar_kwh: [0,0,0,0,0,0,5,15,40,60,75,85,90,85,70,50,30,10,0,0,0,0,0,0][h],
    tariff_bdt_per_kwh: [6,6,6,6,6,6,8,8,10,10,10,10,10,10,10,12,12,12,10,10,8,8,6,6][h],
  })),
  battery: {
    capacity_kwh: 100,
    initial_energy_kwh: 50,
    minimum_energy_kwh: 10,
    max_charge_kwh_per_hour: 25,
    max_discharge_kwh_per_hour: 25,
  },
};

// ────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────
const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const formatNum = (n: number) => n.toFixed(2);

const DIRECTIVE_COLORS: Record<string, string> = {
  solar_reduction:        '#fbbf24',
  minimum_battery_reserve:'#34d399',
  no_charge_window:       '#fb7185',
  no_discharge_window:    '#f472b6',
  max_grid_window:        '#22d3ee',
  no_op:                  '#64748b',
};

const BATTERY_COLORS: Record<string, string> = {
  charge:    '#34d399',
  discharge: '#fb7185',
  idle:      '#64748b',
};

// ────────────────────────────────────────────
// Main App
// ────────────────────────────────────────────
export default function App() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chart' | 'table'>('chart');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleOptimize = async () => {
    try {
      setError(''); setResult(null); setLoading(true);
      const payload = JSON.parse(input);
      const { data } = await axios.post<ApiResponse>(`${API}/optimize-energy`, payload);
      setResult(data);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response) {
        setError(JSON.stringify(err.response.data, null, 2));
      } else if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = () => {
    setInput(JSON.stringify(DEMO_INPUT, null, 2));
    setResult(null); setError('');
  };

  // auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 500) + 'px';
    }
  }, [input]);

  return (
    <div style={styles.shell}>
      {/* ── Header ─────────────────── */}
      <header style={styles.header}>
        <div style={styles.headerInner}>
          <div style={styles.logoRow}>
            <div style={styles.logoDot} />
            <span style={styles.logoText}>GridWise</span>
            <span style={styles.badge}>v1.0</span>
          </div>
          <p style={styles.tagline}>LLM-Assisted Smart Campus Energy Optimization</p>
        </div>
        <StatusDot connected />
      </header>

      {/* ── Main Grid ──────────────── */}
      <div style={styles.mainGrid}>
        {/* LEFT: Input Panel */}
        <section style={styles.inputPanel} className="glass">
          <div style={styles.panelHeader}>
            <h2 style={styles.panelTitle}>
              <span style={styles.iconCircle}>⚡</span>
              Scenario Input
            </h2>
            <button style={styles.btnGhost} onClick={loadDemo}>
              ✦ Try Example
            </button>
          </div>

          <textarea
            ref={textareaRef}
            style={styles.textarea}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder='{\n  "scenario_id": "...",\n  "operator_notes": [...],\n  "hours": [...],\n  "battery": {...}\n}'
            spellCheck={false}
          />

          <button
            style={{
              ...styles.btnPrimary,
              ...(loading ? styles.btnDisabled : {}),
            }}
            onClick={handleOptimize}
            disabled={loading || !input.trim()}
          >
            {loading ? <Spinner /> : null}
            {loading ? 'Optimizing…' : '▶  Run Optimization'}
          </button>

          {error && (
            <div style={styles.errorBox}>
              <span style={styles.errorIcon}>✕</span>
              <pre style={styles.errorPre}>{error}</pre>
            </div>
          )}
        </section>

        {/* RIGHT: Results Panel */}
        <section style={styles.resultsPanel}>
          {!result && !loading && <EmptyState />}
          {loading && <LoadingState />}
          {result && (
            <div style={styles.resultsInner}>
              {/* KPI Cards */}
              <div style={styles.kpiRow}>
                <KpiCard label="Total Cost" value={`৳ ${formatNum(result.total_cost_bdt)}`} icon="💰" color="var(--accent-light)" />
                <KpiCard label="Grid Usage" value={`${formatNum(result.total_grid_kwh)} kWh`} icon="⚡" color="var(--cyan)" />
                <KpiCard label="Peak Grid" value={`${formatNum(result.peak_grid_kwh)} kWh`} icon="📈" color="var(--amber)" />
              </div>

              {/* Scenario ID & Summary */}
              <div className="glass" style={styles.summaryCard}>
                <div style={styles.summaryTop}>
                  <span style={styles.scenarioId}>{result.scenario_id}</span>
                </div>
                <p style={styles.summaryText}>{result.plan_summary}</p>
              </div>

              {/* Directives */}
              <div className="glass" style={styles.directivesCard}>
                <h3 style={styles.sectionTitle}>Directive Interpretation</h3>
                <div style={styles.directivesList}>
                  {result.directive_interpretation.map((d, i) => (
                    <DirectiveChip key={i} d={d} />
                  ))}
                </div>
              </div>

              {/* Hourly Plan */}
              <div className="glass" style={styles.planCard}>
                <div style={styles.planHeader}>
                  <h3 style={styles.sectionTitle}>24-Hour Energy Plan</h3>
                  <div style={styles.tabRow}>
                    <TabBtn active={activeTab === 'chart'} onClick={() => setActiveTab('chart')}>Chart</TabBtn>
                    <TabBtn active={activeTab === 'table'} onClick={() => setActiveTab('table')}>Table</TabBtn>
                  </div>
                </div>

                {activeTab === 'chart' ? (
                  <EnergyChart plan={result.hourly_plan} />
                ) : (
                  <EnergyTable plan={result.hourly_plan} />
                )}
              </div>
            </div>
          )}
        </section>
      </div>

      {/* ── Footer ─────────────────── */}
      <footer style={styles.footer}>
        <span>GridWise — BUP CSE Fest 2026</span>
        <span style={{ color: 'var(--text-dim)' }}>Powered by Gemini AI + Linear Programming</span>
      </footer>
    </div>
  );
}

// ────────────────────────────────────────────
// Sub-components
// ────────────────────────────────────────────

function StatusDot({ connected }: { connected: boolean }) {
  return (
    <div style={styles.statusRow}>
      <div style={{
        width: 8, height: 8, borderRadius: '50%',
        background: connected ? 'var(--emerald)' : 'var(--rose)',
        boxShadow: connected ? '0 0 8px var(--emerald-glow)' : '0 0 8px var(--rose-glow)',
      }} />
      <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
        {connected ? 'API Connected' : 'Disconnected'}
      </span>
    </div>
  );
}

function Spinner() {
  return <span style={styles.spinner} />;
}

function EmptyState() {
  return (
    <div style={styles.emptyState}>
      <div style={styles.emptyIcon}>⚡</div>
      <h3 style={styles.emptyTitle}>Ready to Optimize</h3>
      <p style={styles.emptyDesc}>
        Paste a scenario JSON on the left or click <strong>"Try Example"</strong> to see the optimizer in action.
      </p>
      <div style={styles.emptyFeatures}>
        <FeaturePill icon="🤖" text="LLM Interpretation" />
        <FeaturePill icon="📊" text="LP Optimization" />
        <FeaturePill icon="✅" text="Constraint Validation" />
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div style={styles.emptyState}>
      <div style={styles.loadingRing}>
        <span style={styles.spinnerLarge} />
      </div>
      <h3 style={styles.emptyTitle}>Processing Scenario…</h3>
      <p style={styles.emptyDesc}>
        Interpreting operator notes via Gemini AI and running the linear program optimizer.
      </p>
      <div style={styles.loadingSteps}>
        <LoadingStep text="Parsing operator notes" done />
        <LoadingStep text="LLM directive extraction" />
        <LoadingStep text="LP cost optimization" />
        <LoadingStep text="Schedule validation" />
      </div>
    </div>
  );
}

function LoadingStep({ text, done }: { text: string; done?: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: done ? 'var(--emerald)' : 'var(--text-dim)' }}>
      <span style={{ fontSize: 14 }}>{done ? '✓' : '○'}</span>
      <span style={{ fontSize: 13 }}>{text}</span>
    </div>
  );
}

function FeaturePill({ icon, text }: { icon: string; text: string }) {
  return (
    <div style={styles.featurePill}>
      <span>{icon}</span>
      <span>{text}</span>
    </div>
  );
}

function KpiCard({ label, value, icon, color }: { label: string; value: string; icon: string; color: string }) {
  return (
    <div className="glass" style={styles.kpiCard}>
      <div style={{ ...styles.kpiIconWrap, background: color + '18', border: `1px solid ${color}33` }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
      </div>
      <div>
        <div style={{ fontSize: 12, color: 'var(--text-dim)', textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>{label}</div>
        <div style={{ fontSize: 22, fontWeight: 700, color, letterSpacing: -0.5 }}>{value}</div>
      </div>
    </div>
  );
}

function DirectiveChip({ d }: { d: DirectiveInterp }) {
  const color = DIRECTIVE_COLORS[d.directive_type] || '#94a3b8';
  return (
    <div style={{ ...styles.directiveChip, borderColor: color + '40' }}>
      <div style={styles.directiveChipTop}>
        <span style={{ ...styles.directiveBadge, background: color + '22', color, borderColor: color + '55' }}>
          {d.directive_type.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>Note #{d.note_index}</span>
      </div>
      <p style={styles.directiveExpl}>{d.explanation}</p>
      {d.structured_adjustment && (
        <pre style={styles.directiveAdj}>
          {JSON.stringify(d.structured_adjustment, null, 2)}
        </pre>
      )}
    </div>
  );
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        ...styles.tabBtn,
        ...(active ? styles.tabBtnActive : {}),
      }}
    >
      {children}
    </button>
  );
}

// ── Chart ──
function EnergyChart({ plan }: { plan: HourlyPlan[] }) {
  const maxVal = Math.max(...plan.map(h => Math.max(h.grid_kwh, h.solar_used_kwh, h.battery_kwh)));
  const scale = maxVal > 0 ? 160 / maxVal : 1;

  return (
    <div style={styles.chartContainer}>
      {/* Legend */}
      <div style={styles.legend}>
        <LegendDot color="var(--accent-light)" label="Grid" />
        <LegendDot color="var(--amber)" label="Solar" />
        <LegendDot color="var(--emerald)" label="Battery" />
      </div>
      {/* Bars */}
      <div style={styles.chartBars}>
        {plan.map((h, i) => (
          <div key={h.hour} style={styles.barGroup}>
            <div style={styles.barStack}>
              <div style={{
                ...styles.bar,
                height: h.grid_kwh * scale,
                background: 'linear-gradient(180deg, var(--accent-light), var(--accent))',
                animationDelay: `${i * 30}ms`,
              }} title={`Grid: ${formatNum(h.grid_kwh)} kWh`} />
              <div style={{
                ...styles.bar,
                height: h.solar_used_kwh * scale,
                background: 'linear-gradient(180deg, var(--amber), #d97706)',
                animationDelay: `${i * 30 + 15}ms`,
              }} title={`Solar: ${formatNum(h.solar_used_kwh)} kWh`} />
              <div style={{
                ...styles.bar,
                height: h.battery_kwh * scale,
                background: `linear-gradient(180deg, ${BATTERY_COLORS[h.battery_action]}, ${BATTERY_COLORS[h.battery_action]}88)`,
                animationDelay: `${i * 30 + 30}ms`,
              }} title={`Battery: ${h.battery_action} ${formatNum(h.battery_kwh)} kWh`} />
            </div>
            <span style={styles.barLabel}>{h.hour}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 10, height: 10, borderRadius: 3, background: color }} />
      <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>{label}</span>
    </div>
  );
}

// ── Table ──
function EnergyTable({ plan }: { plan: HourlyPlan[] }) {
  return (
    <div style={styles.tableWrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            {['Hour', 'Grid kWh', 'Solar kWh', 'Battery Action', 'Battery kWh', 'Energy After'].map(h => (
              <th key={h} style={styles.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {plan.map(h => (
            <tr key={h.hour} style={styles.tr}>
              <td style={styles.td}>
                <span style={styles.hourBadge}>{String(h.hour).padStart(2, '0')}:00</span>
              </td>
              <td style={{ ...styles.td, color: 'var(--accent-light)' }}>{formatNum(h.grid_kwh)}</td>
              <td style={{ ...styles.td, color: 'var(--amber)' }}>{formatNum(h.solar_used_kwh)}</td>
              <td style={styles.td}>
                <span style={{
                  ...styles.actionBadge,
                  color: BATTERY_COLORS[h.battery_action],
                  background: BATTERY_COLORS[h.battery_action] + '18',
                  borderColor: BATTERY_COLORS[h.battery_action] + '40',
                }}>
                  {h.battery_action}
                </span>
              </td>
              <td style={styles.td}>{formatNum(h.battery_kwh)}</td>
              <td style={{ ...styles.td, color: 'var(--emerald)' }}>{formatNum(h.battery_energy_after_kwh)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ────────────────────────────────────────────
// Styles (all inline — zero extra deps)
// ────────────────────────────────────────────
const styles: Record<string, CSSProperties> = {
  shell: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    padding: '0 24px',
    maxWidth: 1440,
    margin: '0 auto',
  },

  // ── Header ──
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 0',
    borderBottom: '1px solid var(--border)',
  },
  headerInner: { display: 'flex', flexDirection: 'column', gap: 4 },
  logoRow: { display: 'flex', alignItems: 'center', gap: 10 },
  logoDot: {
    width: 12, height: 12, borderRadius: '50%',
    background: 'linear-gradient(135deg, var(--accent), var(--cyan))',
    boxShadow: '0 0 12px var(--accent-glow)',
  },
  logoText: {
    fontSize: 22, fontWeight: 700, letterSpacing: -0.5,
    background: 'linear-gradient(135deg, var(--accent-light), var(--cyan))',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  badge: {
    fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 99,
    background: 'var(--accent)22', color: 'var(--accent-light)',
    border: '1px solid var(--accent)44',
  },
  tagline: { fontSize: 13, color: 'var(--text-dim)', marginLeft: 22 },
  statusRow: { display: 'flex', alignItems: 'center', gap: 8 },

  // ── Main Grid ──
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: 'minmax(380px, 1fr) 2fr',
    gap: 24,
    flex: 1,
    padding: '24px 0',
  },

  // ── Input Panel ──
  inputPanel: {
    padding: 24,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    alignSelf: 'start',
    position: 'sticky' as const,
    top: 24,
    animation: 'fadeInUp 0.5s var(--ease-out)',
  },
  panelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  panelTitle: {
    fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8,
    color: 'var(--text-primary)',
  },
  iconCircle: {
    width: 32, height: 32, borderRadius: 10,
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    background: 'var(--accent)18', fontSize: 16,
  },
  textarea: {
    width: '100%',
    minHeight: 280,
    maxHeight: 500,
    resize: 'vertical' as const,
    fontFamily: 'var(--mono)',
    fontSize: 13,
    lineHeight: 1.6,
    padding: 16,
    borderRadius: 12,
    border: '1px solid var(--border)',
    background: 'rgba(0,0,0,0.3)',
    color: 'var(--text-primary)',
    outline: 'none',
    transition: 'border-color 0.2s',
  },

  // ── Buttons ──
  btnPrimary: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: '14px 24px',
    borderRadius: 12,
    border: 'none',
    background: 'linear-gradient(135deg, var(--accent), #4f46e5)',
    color: '#fff',
    fontSize: 15,
    fontWeight: 600,
    fontFamily: 'var(--sans)',
    cursor: 'pointer',
    transition: 'all 0.2s',
    boxShadow: '0 4px 20px var(--accent-glow)',
  },
  btnDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  btnGhost: {
    padding: '6px 14px',
    borderRadius: 8,
    border: '1px solid var(--border)',
    background: 'transparent',
    color: 'var(--accent-light)',
    fontSize: 13,
    fontFamily: 'var(--sans)',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },

  // ── Error ──
  errorBox: {
    display: 'flex',
    gap: 10,
    padding: 14,
    borderRadius: 12,
    background: 'rgba(251, 113, 133, 0.08)',
    border: '1px solid rgba(251, 113, 133, 0.25)',
    animation: 'fadeIn 0.3s var(--ease-out)',
  },
  errorIcon: {
    color: 'var(--rose)',
    fontWeight: 700,
    fontSize: 16,
    flexShrink: 0,
    marginTop: 2,
  },
  errorPre: {
    margin: 0,
    fontFamily: 'var(--mono)',
    fontSize: 12,
    color: 'var(--rose)',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    lineHeight: 1.5,
  },

  // ── Results Panel ──
  resultsPanel: {
    minHeight: 400,
  },
  resultsInner: {
    display: 'flex',
    flexDirection: 'column',
    gap: 20,
    animation: 'fadeInUp 0.5s var(--ease-out)',
  },

  // ── KPI ──
  kpiRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 16,
  },
  kpiCard: {
    padding: 20,
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    animation: 'slideInRight 0.5s var(--ease-out)',
  },
  kpiIconWrap: {
    width: 48, height: 48, borderRadius: 14,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },

  // ── Summary ──
  summaryCard: {
    padding: 20,
  },
  summaryTop: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  scenarioId: {
    fontSize: 13,
    fontWeight: 600,
    fontFamily: 'var(--mono)',
    padding: '4px 12px',
    borderRadius: 8,
    background: 'var(--accent)18',
    color: 'var(--accent-light)',
    border: '1px solid var(--accent)33',
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 1.7,
    color: 'var(--text-secondary)',
  },

  // ── Directives ──
  directivesCard: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 15, fontWeight: 600, marginBottom: 14,
    color: 'var(--text-primary)',
  },
  directivesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  directiveChip: {
    padding: 14,
    borderRadius: 12,
    border: '1px solid',
    background: 'rgba(0,0,0,0.2)',
  },
  directiveChipTop: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  directiveBadge: {
    fontSize: 12,
    fontWeight: 600,
    padding: '3px 10px',
    borderRadius: 6,
    border: '1px solid',
    textTransform: 'uppercase' as const,
    letterSpacing: 0.5,
  },
  directiveExpl: {
    fontSize: 13,
    lineHeight: 1.6,
    color: 'var(--text-secondary)',
    margin: 0,
  },
  directiveAdj: {
    marginTop: 8,
    padding: 10,
    borderRadius: 8,
    background: 'rgba(0,0,0,0.3)',
    fontFamily: 'var(--mono)',
    fontSize: 12,
    color: 'var(--cyan)',
    border: '1px solid var(--border)',
    overflow: 'auto' as const,
  },

  // ── Plan Card ──
  planCard: {
    padding: 20,
  },
  planHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  tabRow: {
    display: 'flex',
    gap: 4,
    padding: 3,
    borderRadius: 10,
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid var(--border)',
  },
  tabBtn: {
    padding: '6px 16px',
    borderRadius: 8,
    border: 'none',
    background: 'transparent',
    color: 'var(--text-dim)',
    fontSize: 13,
    fontWeight: 500,
    fontFamily: 'var(--sans)',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  tabBtnActive: {
    background: 'var(--accent)',
    color: '#fff',
    boxShadow: '0 2px 8px var(--accent-glow)',
  },

  // ── Chart ──
  chartContainer: {
    padding: '8px 0',
  },
  legend: {
    display: 'flex',
    gap: 20,
    marginBottom: 12,
    justifyContent: 'center',
  },
  chartBars: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: 3,
    height: 200,
    padding: '0 4px',
  },
  barGroup: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
  },
  barStack: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 2,
    height: 170,
  },
  bar: {
    width: '100%',
    minWidth: 6,
    borderRadius: '3px 3px 0 0',
    transformOrigin: 'bottom',
    animation: 'barGrow 0.6s var(--ease-out) backwards',
  },
  barLabel: {
    fontSize: 10,
    color: 'var(--text-dim)',
    fontFamily: 'var(--mono)',
  },

  // ── Table ──
  tableWrap: {
    overflowX: 'auto' as const,
    borderRadius: 12,
    border: '1px solid var(--border)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: 13,
    fontFamily: 'var(--mono)',
  },
  th: {
    padding: '10px 12px',
    textAlign: 'center' as const,
    fontWeight: 600,
    fontSize: 11,
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    color: 'var(--text-dim)',
    borderBottom: '1px solid var(--border)',
    background: 'rgba(0,0,0,0.2)',
    whiteSpace: 'nowrap' as const,
  },
  tr: {
    borderBottom: '1px solid rgba(99,102,241,0.08)',
    transition: 'background 0.15s',
  },
  td: {
    padding: '8px 12px',
    textAlign: 'center' as const,
    color: 'var(--text-secondary)',
  },
  hourBadge: {
    fontFamily: 'var(--mono)',
    fontSize: 12,
    fontWeight: 500,
    color: 'var(--text-primary)',
  },
  actionBadge: {
    fontSize: 11,
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: 6,
    border: '1px solid',
    textTransform: 'capitalize' as const,
  },

  // ── Empty / Loading ──
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '80px 40px',
    textAlign: 'center' as const,
    animation: 'fadeIn 0.5s var(--ease-out)',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 20,
    filter: 'drop-shadow(0 0 20px var(--accent-glow))',
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: 8,
  },
  emptyDesc: {
    fontSize: 14,
    color: 'var(--text-dim)',
    maxWidth: 380,
    lineHeight: 1.7,
    marginBottom: 24,
  },
  emptyFeatures: {
    display: 'flex',
    gap: 12,
  },
  featurePill: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '8px 14px',
    borderRadius: 99,
    background: 'var(--bg-glass)',
    border: '1px solid var(--border)',
    fontSize: 13,
    color: 'var(--text-secondary)',
  },
  loadingRing: {
    position: 'relative' as const,
    width: 64,
    height: 64,
    marginBottom: 20,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinner: {
    display: 'inline-block',
    width: 18,
    height: 18,
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.6s linear infinite',
  },
  spinnerLarge: {
    display: 'inline-block',
    width: 48,
    height: 48,
    border: '3px solid var(--border)',
    borderTopColor: 'var(--accent)',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  loadingSteps: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    marginTop: 20,
    alignItems: 'flex-start',
  },

  // ── Footer ──
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 0',
    borderTop: '1px solid var(--border)',
    fontSize: 13,
    color: 'var(--text-secondary)',
  },
};
