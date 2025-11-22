import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  Shield, 
  Terminal, 
  Activity, 
  Server, 
  Globe, 
  Database,
  Map as MapIcon,
  Zap,
  Brain,
  Code,
  Eye,
  Lock,
  Play,
  Layout,
  Cpu
} from 'lucide-react';

// --- Types & Interfaces ---

type LogType = 'thought' | 'action' | 'translation' | 'observation' | 'reward' | 'system';

interface LogEntry {
  id: string;
  type: LogType;
  content: string;
  metadata?: string;
  rewardValue?: number;
  timestamp: number;
}

interface Host {
  id: string;
  name: string;
  type: 'server' | 'database' | 'workstation' | 'firewall';
  status: 'compromised' | 'safe' | 'suspicious';
  x: number;
  y: number;
}

interface Scenario {
  id: string;
  name: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  description: string;
}

// Environment data and the simulation sequence are served by the backend (/api/environment)

// --- Components ---

const TopologyMap: React.FC<{ hosts: Host[] }> = ({ hosts }) => {
  // Host status is now driven by backend `host_status` events stored in `hosts`.
  const getStatus = (host: Host) => host.status || 'safe';
  const anyCompromised = hosts.some(h => h.status === 'compromised');

  return (
    <div className="relative h-full w-full bg-slate-900/30 rounded-lg overflow-hidden">
      {/* Grid Background */}
      <div className="absolute inset-0 opacity-10" 
           style={{ backgroundImage: 'linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
      </div>

      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        {/* Dynamic Edges */}
        <line x1="50" y1="100" x2="200" y2="50" stroke="#334155" strokeWidth="1" />
        <line x1="50" y1="100" x2="200" y2="150" stroke="#334155" strokeWidth="1" />
        
        {/* Attack Path Highlight (driven by host status) */}
        {anyCompromised ? (
          <line x1="50" y1="100" x2="350" y2="100" stroke="#ef4444" strokeWidth="2" strokeDasharray="5,5" className="animate-pulse" />
        ) : (
          <line x1="50" y1="100" x2="350" y2="100" stroke="#334155" strokeWidth="1" />
        )}

        <line x1="350" y1="100" x2="500" y2="100" stroke="#334155" strokeWidth="1" />
      </svg>

      {hosts.map(host => {
        const currentStatus = getStatus(host);
        return (
          <div 
            key={host.id}
            className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center transition-all duration-500"
            style={{ left: host.x, top: host.y }}
          >
            <div className={`
              w-10 h-10 rounded-lg flex items-center justify-center border transition-all duration-300
              ${currentStatus === 'compromised' ? 'bg-red-500/20 border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]' : 
                currentStatus === 'suspicious' ? 'bg-amber-500/20 border-amber-500' :
                'bg-slate-800 border-slate-600'}
            `}>
              {host.type === 'database' ? <Database size={16} className={currentStatus === 'compromised' ? 'text-red-400' : 'text-slate-300'} /> :
               host.type === 'firewall' ? <Shield size={16} className={currentStatus === 'compromised' ? 'text-red-400' : 'text-slate-300'} /> :
               <Server size={16} className={currentStatus === 'compromised' ? 'text-red-400' : 'text-slate-300'} />}
            </div>
            <span className="mt-1 text-[10px] font-mono text-slate-400 bg-slate-900/80 px-1 rounded">
              {host.name}
            </span>
          </div>
        );
      })}
    </div>
  );
};

const LogItem: React.FC<{ entry: LogEntry }> = ({ entry }) => {
  const iconMap = {
    thought: <Brain size={14} className="text-purple-400" />,
    action: <Terminal size={14} className="text-blue-400" />,
    translation: <Code size={14} className="text-cyan-400" />,
    observation: <Eye size={14} className="text-emerald-400" />,
    reward: <Zap size={14} className="text-yellow-400" />,
    system: <Activity size={14} className="text-slate-400" />
  };

  const colorMap = {
    thought: 'border-l-purple-500 bg-purple-500/5 text-purple-100',
    action: 'border-l-blue-500 bg-blue-500/5 text-blue-100',
    translation: 'border-l-cyan-500 bg-cyan-950/30 text-cyan-200 font-mono text-xs',
    observation: 'border-l-emerald-500 bg-emerald-500/5 text-emerald-100',
    reward: 'border-l-yellow-500 bg-yellow-500/10 text-yellow-100',
    system: 'border-l-slate-500 bg-slate-800/50 text-slate-400'
  };

  return (
    <div className={`p-3 rounded-r-lg border-l-2 mb-3 animate-slideRight ${colorMap[entry.type]} transition-all hover:bg-opacity-20`}>
      <div className="flex items-center gap-2 mb-1">
        {iconMap[entry.type]}
        <span className="text-[10px] uppercase tracking-wider font-bold opacity-70">
          {entry.type === 'translation' ? 'Sim2Real Translation' : entry.type}
        </span>
        <span className="text-[10px] opacity-40 ml-auto">{new Date(entry.timestamp).toLocaleTimeString()}</span>
      </div>
      <div className={`${entry.type === 'translation' ? 'font-mono' : 'font-sans'} text-sm leading-relaxed`}>
        {entry.content}
      </div>
      {entry.metadata && (
        <div className="mt-2 text-[10px] px-2 py-1 bg-black/20 rounded inline-block text-opacity-70 text-current border border-white/5">
          {entry.metadata}
        </div>
      )}
      {entry.rewardValue && (
        <div className="mt-2 flex items-center gap-1 text-xs font-bold text-yellow-400">
          <Zap size={12} fill="currentColor" /> +{entry.rewardValue.toFixed(1)} Reward Signal
        </div>
      )}
    </div>
  );
};

// Reward chart uses Recharts for nicer visualization

export default function App() {
  const [logs, setLogs] = useState<LogEntry[]>([
    { id: 'init', type: 'system', content: 'Environment Initialized. Waiting for Agent input...', timestamp: Date.now() }
  ]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [mode, setMode] = useState<'sim' | 'real'>('sim');
  const [cumulativeReward, setCumulativeReward] = useState(0);
  const [simStep, setSimStep] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [rewardPoints, setRewardPoints] = useState<Array<{ x: number; y: number }>>([]);
  const [artifacts, setArtifacts] = useState<Array<{ id?: string; time?: number; type?: string; description?: string; value?: string; impact?: string; confidence?: number | string; source?: string; step?: number }>>([]);

  const investigateMutation = useMutation<any, Error, string>({
    mutationFn: async (prompt: string) => {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      return res.json();
    },
    onMutate: (p: string) => {
      setLogs(prev => [...prev, { id: `req-${Date.now()}`, type: 'system', content: `Sending prompt to backend: "${p}"`, timestamp: Date.now() }]);
    },
    onSuccess: (data: any) => {
      setLogs(prev => [...prev, { id: `res-${Date.now()}`, type: 'system', content: `Backend response: ${typeof data === 'string' ? data : JSON.stringify(data)}`, timestamp: Date.now() }]);
    },
    onError: (err: Error | unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      setLogs(prev => [...prev, { id: `err-${Date.now()}`, type: 'system', content: `Backend error: ${message}`, timestamp: Date.now() }]);
    }
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  // Fetch environment from backend on mount
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch('/api/environment');
        if (!res.ok) return;
        const data = await res.json();
        if (!mounted) return;
        setHosts(data.hosts || []);
        setScenarios(data.scenarios || []);
      } catch (e) {
        // ignore fetch errors for now
      }
    })();
    return () => { mounted = false };
  }, []);

  const handleExecute = async () => {
    if (!prompt) return;

    setIsSimulating(true);
    setSimStep(0);
    setCumulativeReward(0);
    setRewardPoints([]);

    let investigationId: string | undefined;
    try {
      const resp = await investigateMutation.mutateAsync(prompt);
      // backend returns { investigation_id }
      investigationId = resp?.investigation_id || resp?.investigationId || resp?.id;
    } catch (e) {
      setIsSimulating(false);
      return;
    }

    if (!investigationId) {
      setIsSimulating(false);
      setLogs(prev => [...prev, { id: `err-${Date.now()}`, type: 'system', content: 'No investigation id returned by backend', timestamp: Date.now() }]);
      return;
    }

    // Stream NDJSON events from backend
    try {
      const streamRes = await fetch(`/api/events/${investigationId}`);
      if (!streamRes.ok || !streamRes.body) throw new Error(`Stream failed: ${streamRes.status}`);
      const reader = streamRes.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let stepCounter = 0;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const ev = JSON.parse(line);
            // Map backend event types to LogEntry
            const type = (ev.type as LogType) || 'system';
            stepCounter += 1;
            setSimStep(stepCounter);

            if (type === 'reward' && ev.rewardValue) {
              setCumulativeReward(prev => {
                const newCum = ev.cumulativeReward !== undefined ? Number(ev.cumulativeReward) : prev + Number(ev.rewardValue);
                setRewardPoints(rp => [...rp, { x: stepCounter, y: newCum }]);
                return newCum;
              });
            }
            // artifact events emitted by backend
            if (ev.type === 'artifact' && ev.artifact) {
              setArtifacts(prev => [...prev, ev.artifact]);
            }

            // host status updates emitted by backend
            if (ev.type === 'host_status') {
              const hostId = ev.host_id as string | undefined;
              const hostName = ev.host_name as string | undefined;
              const status = ev.status as 'compromised' | 'suspicious' | 'safe' | string;
              if (status) {
                setHosts(prev => prev.map(h => {
                  if (hostId && h.id === hostId) return { ...h, status: status as any };
                  if (!hostId && hostName && h.name && hostName.includes(h.name)) return { ...h, status: status as any };
                  return h;
                }));
              }
            }

            const entry: LogEntry = {
              id: `evt-${Date.now()}-${Math.random().toString(36).slice(2,6)}`,
              type: (['thought','action','translation','observation','reward','system'].includes(type) ? type : 'system') as LogType,
              content: ev.content || ev.message || JSON.stringify(ev),
              metadata: ev.metadata,
              rewardValue: ev.rewardValue,
              timestamp: ev.timestamp || Date.now()
            };
            setLogs(prev => [...prev, entry]);

            if (ev.type === 'final_report') {
              setLogs(prev => [...prev, { id: `report-${Date.now()}`, type: 'system', content: 'Final report received', timestamp: Date.now() }]);
              // merge findings into artifacts table if present
              if (ev.report && Array.isArray(ev.report.findings)) {
                setArtifacts(prev => {
                  const existingIds = new Set(prev.filter(p => p.id).map(p => p.id));
                  const additions = ev.report.findings
                    .filter((f: any) => !f.id || !existingIds.has(f.id))
                    .map((f: any) => ({
                      id: f.id,
                      time: f.time || Date.now(),
                      type: f.type || 'Finding',
                      description: f.description || f.value || f.description || JSON.stringify(f),
                      value: f.value || f.description || JSON.stringify(f),
                      impact: f.impact || '',
                      confidence: f.confidence ?? '',
                      source: f.source ?? '',
                      step: f.step ?? ''
                    }));
                  return [...prev, ...additions];
                });
              }
            }
            if (ev.type === 'stream_closed') {
              // stream end signal
            }
          } catch (err) {
            // ignore parse errors for now
          }
        }
      }
      // flush remaining buffer
      if (buffer.trim()) {
        try {
          const ev = JSON.parse(buffer);
          const type = (ev.type as LogType) || 'system';
          const entry: LogEntry = {
            id: `evt-${Date.now()}`,
            type: (['thought','action','translation','observation','reward','system'].includes(type) ? type : 'system') as LogType,
            content: ev.content || ev.message || JSON.stringify(ev),
            metadata: ev.metadata,
            rewardValue: ev.rewardValue,
            timestamp: ev.timestamp || Date.now()
          };
          if (type === 'reward' && ev.rewardValue) {
            setCumulativeReward(prev => {
              const newCum = ev.cumulativeReward !== undefined ? Number(ev.cumulativeReward) : prev + Number(ev.rewardValue);
              setRewardPoints(rp => [...rp, { x: simStep || 1, y: newCum }]);
              return newCum;
            });
          }
          setLogs(prev => [...prev, entry]);
        } catch (e) {}
      }
    } catch (e) {
      setLogs(prev => [...prev, { id: `err-${Date.now()}`, type: 'system', content: `Streaming error: ${String(e)}`, timestamp: Date.now() }]);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30 overflow-hidden">
      
      {/* Navbar */}
      <header className="h-14 border-b border-slate-800 bg-slate-900 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield size={18} className="text-white" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-bold tracking-tight text-lg">Sherlock</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest">RL-Driven Security Agent</span>
          </div>
        </div>

        <div className="flex items-center gap-4 bg-slate-950 rounded-lg p-1 border border-slate-800">
          <button 
            onClick={() => setMode('sim')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-2 ${mode === 'sim' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <Layout size={14} /> Simulation (Train)
          </button>
          <button 
            onClick={() => setMode('real')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-2 ${mode === 'real' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <Globe size={14} /> Real-World (Deploy)
          </button>
        </div>

        <div className="flex items-center gap-4 text-sm">
           <div className="flex flex-col items-end mr-4">
             <span className="text-[10px] text-slate-500 uppercase">Reward Model</span>
             <span className="text-xs font-mono text-emerald-400">v2.4 (PPO)</span>
           </div>
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
            <Cpu size={16} className="text-slate-400" />
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        
        {/* Left Panel: Agent Brain / Logs */}
        <div className="w-1/2 border-r border-slate-800 flex flex-col bg-slate-950/50">
          
          {/* Prompt Input */}
          <div className="p-6 border-b border-slate-800 bg-slate-900/30">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">
              Agent Directive (Natural Language)
            </label>
            <div className="relative">
              <input 
                type="text" 
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!isSimulating && prompt && investigateMutation.status !== 'pending') {
                      handleExecute();
                    }
                  }
                }}
                placeholder="Ex: Investigate suspicious login activity from external IP 45.13.12.99..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-4 pr-32 py-3 text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-slate-100 placeholder-slate-600"
              />
              <button 
                onClick={handleExecute}
                disabled={isSimulating || !prompt || investigateMutation.status === 'pending'}
                className="absolute right-1.5 top-1.5 bottom-1.5 px-4 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {investigateMutation.status === 'pending' ? <Activity className="animate-spin" size={14} /> : isSimulating ? <Activity className="animate-spin" size={14} /> : <Play size={14} />}
                {investigateMutation.status === 'pending' ? 'Sending' : isSimulating ? 'Running' : 'Execute'}
              </button>
            </div>
            <p className="mt-2 text-[10px] text-slate-500 flex items-center gap-1">
               <Brain size={10} /> Multi-hop reasoning enabled. Model will chain queries until reward threshold is met.
            </p>
          </div>

          {/* Log Stream */}
          <div className="flex-1 overflow-hidden flex flex-col relative">
            <div className="px-4 py-2 bg-slate-900/50 border-b border-slate-800 flex justify-between items-center">
              <span className="text-xs font-mono text-slate-400">Execution Log</span>
              <span className="text-[10px] text-slate-600 uppercase">Live Stream</span>
            </div>
            
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 custom-scrollbar">
               {logs.map((entry) => (
                 <LogItem key={entry.id} entry={entry} />
               ))}
               {isSimulating && (
                 <div className="flex items-center gap-2 pl-2 mt-2 animate-pulse text-slate-500 text-xs">
                   <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                   Agent is thinking...
                 </div>
               )}
            </div>
          </div>
        </div>

        {/* Right Panel: Environment State & Metrics */}
        <div className="w-1/2 flex flex-col bg-slate-900/20">
          
          {/* Stats Bar */}
          <div className="h-16 border-b border-slate-800 flex items-center divide-x divide-slate-800 bg-slate-900/40">
            <div className="flex-1 px-6 flex flex-col justify-center">
              <span className="text-[10px] text-slate-500 uppercase font-bold mb-1">Cumulative Reward</span>
              <div className="text-xl font-mono text-yellow-400 flex items-center gap-2">
                <Zap size={16} fill="currentColor" />
                {cumulativeReward.toFixed(1)}
              </div>
            </div>
            <div className="flex-1 px-6 flex flex-col justify-center">
              <span className="text-[10px] text-slate-500 uppercase font-bold mb-1">Steps Taken</span>
              <div className="text-xl font-mono text-white">{simStep} <span className="text-sm text-slate-500">/ 20 (Limit)</span></div>
            </div>
            <div className="flex-1 px-6 flex flex-col justify-center">
              <span className="text-[10px] text-slate-500 uppercase font-bold mb-1">Active Scenario</span>
              <div className="text-sm font-medium text-blue-300 truncate">{scenarios[0]?.name ?? 'APT29 Lateral Movement'}</div>
            </div>
          </div>

          {/* Topology View */}
          <div className="border-b border-slate-800 bg-slate-900/30 p-3">
            <div style={{ width: '100%', height: 110 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={rewardPoints.map(p => ({ step: p.x, reward: p.y }))}>
                  <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                  <XAxis dataKey="step" stroke="#94a3b8" />
                  <YAxis stroke="#f59e0b" />
                  <Tooltip formatter={(value: any) => [value, 'Reward']} />
                  <Line type="monotone" dataKey="reward" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="flex-1 p-6 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-4">
               <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2">
                 <MapIcon size={16} className="text-blue-500" />
                 Environment Topology (Simulated)
               </h3>
               <div className="flex items-center gap-3 text-[10px] text-slate-400">
                  <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-slate-600"></div> Safe</span>
                  <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500 shadow shadow-red-500/50"></div> Compromised</span>
               </div>
            </div>
            
            <div className="flex-1 border border-slate-800 rounded-lg bg-slate-950 relative shadow-inner">
               <TopologyMap hosts={hosts} />
            </div>
          </div>

          {/* Detected Artefacts Table */}
          <div className="h-1/3 border-t border-slate-800 bg-slate-900/30 flex flex-col">
            <div className="px-6 py-3 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
               <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                 <Lock size={14} className="text-emerald-500" />
                 Key Artefacts Uncovered
               </h3>
            </div>
            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-900/80 text-[10px] text-slate-500 uppercase sticky top-0">
                  <tr>
                    <th className="px-6 py-2 font-medium">Time</th>
                    <th className="px-6 py-2 font-medium">ID</th>
                    <th className="px-6 py-2 font-medium">Type</th>
                    <th className="px-6 py-2 font-medium">Value</th>
                    <th className="px-6 py-2 font-medium">Impact</th>
                    <th className="px-6 py-2 font-medium">Confidence</th>
                    <th className="px-6 py-2 font-medium">Source</th>
                    <th className="px-6 py-2 font-medium">Step</th>
                  </tr>
                </thead>
                <tbody className="text-xs font-mono divide-y divide-slate-800">
                  {artifacts.length > 0 ? (
                    artifacts.map((a, idx) => (
                      <tr key={a.id ?? idx} className="hover:bg-slate-800/50 animate-fadeIn">
                        <td className="px-6 py-3 text-slate-400">{a.time ? new Date(a.time).toLocaleTimeString() : '-'}</td>
                        <td className="px-6 py-3 text-slate-300 font-mono">{a.id ?? '-'}</td>
                        <td className="px-6 py-3 text-blue-300">{a.type ?? 'Artifact'}</td>
                        <td className="px-6 py-3 text-slate-300">{a.description ?? a.value ?? ''}</td>
                        <td className="px-6 py-3 text-amber-400">{a.impact ?? ''}</td>
                        <td className="px-6 py-3 text-slate-300">{a.confidence ?? ''}</td>
                        <td className="px-6 py-3 text-slate-300">{a.source ?? ''}</td>
                        <td className="px-6 py-3 text-slate-300">{a.step ?? ''}</td>
                      </tr>
                    ))
                  ) : null}
                </tbody>
              </table>
                {artifacts.length === 0 && (
                   <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-2">
                     <SearchIcon size={24} className="opacity-20" />
                     <span className="text-xs">Waiting for agent findings...</span>
                   </div>
                )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Helper icon for empty state
const SearchIcon = ({ size, className }: { size: number, className?: string }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <circle cx="11" cy="11" r="8"></circle>
    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
  </svg>
);