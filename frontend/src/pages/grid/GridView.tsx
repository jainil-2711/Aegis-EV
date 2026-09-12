import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import { useGridData } from "../../hooks/useGridData";
import type {
  GridCondition,
  RenewableAvailability,
  SignalOperator,
} from "../../types/api";
import AegisIntelligence from "../../components/AegisIntelligence";

const conditions: GridCondition[] = [
  "normal",
  "high_demand",
  "high_renewable",
  "low_renewable",
];

const conditionLabel: Record<GridCondition, string> = {
  normal: "Normal",
  high_demand: "High demand",
  high_renewable: "High renewable",
  low_renewable: "Low renewable",
};

const availabilityLabel: Record<RenewableAvailability, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

function MetricCard({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900">{value}</p>
      {note && <p className="mt-1 text-xs text-slate-500">{note}</p>}
    </div>
  );
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDateTimeLocal(value: string) {
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export default function GridView() {
  const { status, forecast, signals, loading, error, publishSignal } = useGridData();
  const [condition, setCondition] = useState<GridCondition>("high_demand");
  const [recommendedLoad, setRecommendedLoad] = useState("250");
  const [operator, setOperator] = useState<SignalOperator>("lte");
  const [renewable, setRenewable] = useState<RenewableAvailability>("medium");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const chartData = useMemo(
    () =>
      (forecast?.slots ?? []).map((slot) => ({
        time: formatTime(slot.timestamp),
        demand: slot.base_load_kw,
        renewable: slot.renewable_kw,
        capacity: slot.grid_capacity_kw,
      })),
    [forecast],
  );

  useEffect(() => {
    const first = forecast?.slots?.[0];
    const fifth = forecast?.slots?.[4];
    if (first) setStartTime((current) => current || formatDateTimeLocal(first.timestamp));
    if (fifth) setEndTime((current) => current || formatDateTimeLocal(fifth.timestamp));
  }, [forecast]);

  if (loading) {
    return <div className="p-6 text-sm text-slate-500">Loading grid state...</div>;
  }

  if (error || !status || !forecast) {
    return (
      <div className="mx-auto max-w-5xl p-6 text-sm text-red-700">
        Couldn&apos;t load grid data: {error ?? "unknown error"}
      </div>
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await publishSignal({
        start_time: startTime,
        end_time: endTime,
        condition,
        recommended_ev_load_kw: Number(recommendedLoad),
        signal_operator: operator,
        renewable_availability: renewable,
      });
      setMessage("Grid signal published. The network optimizer can use it as an advisory signal.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Couldn't publish signal");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Grid operator dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Aggregate grid conditions and advisory signals — individual EV details stay with the charging network.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <MetricCard label="Grid demand" value={`${status.grid_demand_kw.toFixed(0)} kW`} note="Base load + current EV load" />
        <MetricCard label="Grid capacity" value={`${status.grid_capacity_kw.toFixed(0)} kW`} />
        <MetricCard label="Headroom" value={`${status.headroom_kw.toFixed(0)} kW`} />
        <MetricCard label="Renewable generation" value={`${status.renewable_generation_kw.toFixed(0)} kW`} />
        <MetricCard label="Aggregate EV load" value={`${status.ev_load.current_ev_load_kw.toFixed(0)} kW`} note={`Peak ${status.ev_load.peak_ev_load_kw.toFixed(0)} kW`} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-700">24-hour grid outlook</p>
            <p className="text-xs text-slate-500">Forecasted base demand, renewable generation, and available capacity</p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">30-minute slots</span>
        </div>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" interval={3} />
              <YAxis unit=" kW" />
              <Tooltip formatter={(value) => `${Number(value ?? 0).toFixed(0)} kW`} />
              <Legend />
              <Line type="monotone" dataKey="capacity" name="Grid capacity" stroke="#94a3b8" dot={false} />
              <Line type="monotone" dataKey="demand" name="Base demand" stroke="#3b82f6" dot={false} />
              <Line type="monotone" dataKey="renewable" name="Renewable" stroke="#16a34a" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-slate-800">Publish grid signal</h2>
            <p className="mt-1 text-xs text-slate-500">Signals are quantitative, advisory inputs to the network optimizer.</p>
          </div>
          <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm text-slate-700">
              Condition
              <select value={condition} onChange={(e) => setCondition(e.target.value as GridCondition)} className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2">
                {conditions.map((value) => <option key={value} value={value}>{conditionLabel[value]}</option>)}
              </select>
            </label>
            <label className="text-sm text-slate-700">
              Recommended EV load (kW)
              <input type="number" min="0" step="1" value={recommendedLoad} onChange={(e) => setRecommendedLoad(e.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" />
            </label>
            <label className="text-sm text-slate-700">
              Signal operator
              <select value={operator} onChange={(e) => setOperator(e.target.value as SignalOperator)} className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2">
                <option value="lte">At or below (≤)</option>
                <option value="gte">At or above (≥)</option>
              </select>
            </label>
            <label className="text-sm text-slate-700">
              Renewable availability
              <select value={renewable} onChange={(e) => setRenewable(e.target.value as RenewableAvailability)} className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2">
                {Object.entries(availabilityLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
            <label className="text-sm text-slate-700">
              Start
              <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" required />
            </label>
            <label className="text-sm text-slate-700">
              End
              <input type="datetime-local" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" required />
            </label>
            <div className="sm:col-span-2 flex items-center gap-3">
              <button type="submit" disabled={submitting || !startTime || !endTime} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50">
                {submitting ? "Publishing..." : "Publish signal"}
              </button>
              {message && <p className="text-sm text-slate-600">{message}</p>}
            </div>
          </form>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">Latest grid signals</h2>
          <p className="mt-1 text-xs text-slate-500">Advisory instructions visible to the network optimization layer.</p>
          {signals.length === 0 ? (
            <div className="mt-4 rounded-md bg-slate-50 p-4 text-sm text-slate-600">No signals published yet.</div>
          ) : (
            <div className="mt-4 space-y-3">
              {signals.slice(0, 5).map((signal) => (
                <div key={signal.id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-slate-800">{conditionLabel[signal.condition]}</span>
                    <span className="text-xs text-slate-500">{signal.signal_operator === "lte" ? "≤" : "≥"} {signal.recommended_ev_load_kw.toFixed(0)} kW</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {formatTime(signal.start_time)}–{formatTime(signal.end_time)} · Renewable {availabilityLabel[signal.renewable_availability]}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <AegisIntelligence
        title="Grid signal trace"
        subtitle="System context"
        items={[
          { label: "Demand", value: `${status.grid_demand_kw.toFixed(0)} kW of ${status.grid_capacity_kw.toFixed(0)} kW capacity`, tone: "cyan" },
          { label: "Renewable pulse", value: `${status.renewable_generation_kw.toFixed(0)} kW generation available now`, tone: "green" },
          { label: "Headroom", value: `${status.headroom_kw.toFixed(0)} kW remaining before capacity`, tone: status.headroom_kw < 300 ? "amber" : "slate" },
        ]}
        footer="Aegis translates these system signals into optimizer inputs. Publishing a signal does not directly control any individual vehicle."
      />

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-800">Upcoming grid slots</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">Base demand</th>
                <th className="px-3 py-2">Renewable</th>
                <th className="px-3 py-2">Capacity</th>
                <th className="px-3 py-2">Price</th>
                <th className="px-3 py-2">Carbon</th>
              </tr>
            </thead>
            <tbody>
              {forecast.slots.slice(0, 12).map((slot) => (
                <tr key={slot.timestamp} className="border-b border-slate-100">
                  <td className="px-3 py-2 font-medium text-slate-700">{formatTime(slot.timestamp)}</td>
                  <td className="px-3 py-2 text-slate-600">{slot.base_load_kw.toFixed(0)} kW</td>
                  <td className="px-3 py-2 text-green-700">{slot.renewable_kw.toFixed(0)} kW</td>
                  <td className="px-3 py-2 text-slate-600">{slot.grid_capacity_kw.toFixed(0)} kW</td>
                  <td className="px-3 py-2 text-slate-600">₹{slot.electricity_price.toFixed(2)}</td>
                  <td className="px-3 py-2 text-slate-600">{slot.carbon_intensity.toFixed(3)} kgCO₂/kWh</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
