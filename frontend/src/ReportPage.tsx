import { useEffect, useState } from 'react';

interface Artifact {
  id?: string;
  time?: number;
  type?: string;
  description?: string;
  value?: string;
  impact?: string;
  confidence?: number | string;
  source?: string;
  step?: number;
}

interface EventItem {
  type: string;
  content?: string;
  metadata?: string;
  timestamp?: number;
  rewardValue?: number;
  cumulativeReward?: number;
  artifact?: Artifact;
}

export default function ReportPage({ investigationId }: { investigationId?: string }) {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const id = investigationId || (() => {
    const m = window.location.pathname.match(/\/report\/(.+)/);
    return m ? m[1] : undefined;
  })();

  useEffect(() => {
    if (!id) return;
    let mounted = true;
    setLoading(true);
    fetch(`/api/report/${id}`)
      .then(async res => {
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const data = await res.json();
        if (!mounted) return;
        setReport(data);
      })
      .catch(err => {
        if (!mounted) return;
        setError(String(err));
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });
    return () => { mounted = false };
  }, [id]);

  if (!id) return <div className="p-6">No investigation id in URL (use <code>/report/&lt;id&gt;</code>).</div>;
  if (loading) return <div className="p-6">Loading report {id}...</div>;
  if (error) return <div className="p-6 text-red-400">Error: {error}</div>;
  if (!report) return <div className="p-6">No report available for {id}</div>;

  const events: EventItem[] = report.report?.events || [];
  const findings: Artifact[] = report.report?.findings || [];

  return (
    <div className="p-6 overflow-auto">
      <h2 className="text-2xl font-bold mb-2">Investigation Report: {id}</h2>
      <p className="text-sm text-slate-400 mb-4">Status: {report.status}</p>

      <section className="mb-6">
        <h3 className="font-semibold mb-2">Summary</h3>
        <div className="p-3 bg-slate-900 rounded">{report.report?.summary}</div>
      </section>

      <section className="mb-6">
        <h3 className="font-semibold mb-2">Findings / Artifacts</h3>
        {findings.length === 0 ? (
          <div className="p-3 bg-slate-900 rounded">No findings recorded.</div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {findings.map(f => (
              <div key={f.id || Math.random()} className="p-3 bg-slate-900 rounded">
                <div className="text-sm font-mono text-slate-300">{f.id} — {f.source} — step: {f.step}</div>
                <div className="mt-1 text-slate-200">{f.description}</div>
                <div className="text-xs text-slate-400 mt-2">Impact: {f.impact} • Confidence: {f.confidence}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 className="font-semibold mb-2">Event Sequence</h3>
        <div className="space-y-2">
          {events.length === 0 && <div className="p-3 bg-slate-900 rounded">No event sequence recorded in report.</div>}
          {events.map((ev, i) => (
            <div key={i} className="p-2 bg-slate-900/60 rounded">
              <div className="text-[11px] text-slate-400">{new Date(ev.timestamp || Date.now()).toLocaleTimeString()} • {ev.type}</div>
              <div className="mt-1 text-sm text-slate-200">{ev.content}</div>
              {ev.artifact && (
                <div className="mt-2 text-xs text-emerald-300">Artifact: {ev.artifact.id} — {ev.artifact.description}</div>
              )}
              {ev.rewardValue !== undefined && (
                <div className="mt-1 text-xs text-yellow-300">Reward: {ev.rewardValue} (cum {ev.cumulativeReward})</div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
