import React, { useState, useRef, useEffect } from 'react';
import { 
  Shield, 
  Terminal, 
  Activity, 
  AlertTriangle, 
  Server, 
  Globe, 
  CheckCircle, 
  Clock, 
  ChevronRight, 
  Database,
  Share2,
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

// --- Mock Data & Simulation Logic ---

const SCENARIOS: Scenario[] = [
  { id: 's1', name: 'APT29 Lateral Movement', difficulty: 'Hard', description: 'Simulates an adversary moving from a compromised edge node to the domain controller.' },
  { id: 's2', name: 'Insider Data Exfiltration', difficulty: 'Medium', description: 'Detects unauthorized large file uploads by a privileged user during off-hours.' },
  { id: 's3', name: 'Ransomware Deployment', difficulty: 'Critical', description: 'Identifies rapid file encryption patterns and shadow copy deletion commands.' },
];

const INITIAL_HOSTS: Host[] = [
  { id: 'gw', name: 'Gateway-01', type: 'firewall', status: 'safe', x: 50, y: 150 },
  { id: 'web', name: 'Web-FE-02', type: 'server', status: 'safe', x: 200, y: 100 },
  { id: 'app', name: 'App-Svc-04', type: 'server', status: 'safe', x: 200, y: 200 },
  { id: 'db', name: 'DB-PROD-01', type: 'database', status: 'safe', x: 350, y: 150 },
  { id: 'ad', name: 'AD-Core', type: 'server', status: 'safe', x: 500, y: 150 },
];

// Sequence of events for the simulation
const SIMULATION_SEQUENCE = [
  {
    type: 'thought',
    content: 'I need to investigate the initial alert regarding suspicious traffic from external IP 45.13.12.99.',
    delay: 500
  },
  {
    type: 'action',
    content: 'Search for all successful inbound connections from 45.13.12.99 in the last 4 hours.',
    metadata: 'Tool: Natural Language Query',
    delay: 1200
  },
  {
    type: 'translation',
    content: 'index=firewall src_ip="45.13.12.99" action="allowed" | stats count by dest_ip',
    metadata: 'Sim2Real: SQL/SPL Translator',
    delay: 800
  },
  {
    type: 'observation',
    content: 'Found 12 successful connections to Gateway-01 (192.168.1.5) on port 22 (SSH).',
    delay: 1000
  },
  {
    type: 'reward',
    content: 'Initial Access Point Identified',
    rewardValue: 15,
    delay: 500
  },
  {
    type: 'thought',
    content: 'The attacker has SSH access to Gateway-01. I must check for lateral movement from that host.',
    delay: 1500
  },
  {
    type: 'action',
    content: 'Show me outbound connections from Gateway-01 to internal database ports.',
    metadata: 'Tool: Natural Language Query',
    delay: 1200
  },
  {
    type: 'translation',
    content: 'index=vpc_flow src_ip="192.168.1.5" dest_port IN (1433, 5432, 3306) | table _time, dest_ip, bytes',
    metadata: 'Sim2Real: SQL/SPL Translator',
    delay: 1000
  },
  {
    type: 'observation',
    content: 'Connection detected: Gateway-01 -> DB-PROD-01 (Port 1433) at 02:22:10. Bytes: 2.5GB',
    delay: 1200
  },
  {
    type: 'reward',
    content: 'Lateral Movement & Data Staging Detected',
    rewardValue: 35,
    delay: 500
  },
  {
    type: 'thought',
    content: 'High data transfer suggests exfiltration. I need to verify user context on the Database server.',
    delay: 1500
  },
  {
    type: 'action',
    content: 'List active sessions on DB-PROD-01 during the transfer window.',
    metadata: 'Tool: Natural Language Query',
    delay: 1200
  },
  {
    type: 'translation',
    content: 'index=wineventlog host="DB-PROD-01" EventCode=4624 | bucket _time span=5m | stats count by User',
    metadata: 'Sim2Real: SQL/SPL Translator',
    delay: 800
  },
  {
    type: 'observation',
    content: 'User "svc_backup" active. This account typically operates at 03:00, not 02:22.',
    delay: 1000
  },
  {
    type: 'reward',
    content: 'Anomaly Confirmed: Credential Misuse',
    rewardValue: 50,
    delay: 500
  }
];

// --- Components ---

const TopologyMap: React.FC<{ hosts: Host[]; activeStep: number }> = ({ hosts, activeStep }) => {
  // Determine host status based on simulation step for visual feedback
  const getStatus = (host: Host) => {
    if (activeStep > 3 && host.id === 'gw') return 'compromised';
    if (activeStep > 8 && host.id === 'db') return 'compromised';
    if (activeStep > 8 && host.id === 'ad') return 'suspicious';
    return 'safe';
  };

  return (
    <div className="relative h-full w-full bg-slate-900/30 rounded-lg overflow-hidden">
      {/* Grid Background */}
      <div className="absolute inset-0 opacity-10" 
           style={{ backgroundImage: 'linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
      </div>

      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        {/* Dynamic Edges */}
        <line x1="50" y1="150" x2="200" y2="100" stroke="#334155" strokeWidth="1" />
        <line x1="50" y1="150" x2="200" y2="200" stroke="#334155" strokeWidth="1" />
        
        {/* Attack Path Highlight */}
        {activeStep > 3 && (
          <line x1="50" y1="150" x2="350" y2="150" stroke="#ef4444" strokeWidth="2" strokeDasharray="5,5" className="animate-pulse" />
        )}
         {activeStep <= 3 && (
          <line x1="50" y1="150" x2="350" y2="150" stroke="#334155" strokeWidth="1" />
        )}

        <line x1="350" y1="150" x2="500" y2="150" stroke="#334155" strokeWidth="1" />
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

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const runSimulation = async () => {
    if (!prompt) return;
    setIsSimulating(true);
    setSimStep(0);
    setCumulativeReward(0);
    setLogs([{ id: 'start', type: 'system', content: `Initializing Investigation in ${mode === 'sim' ? 'Simulated Environment' : 'Production'}...`, timestamp: Date.now() }]);

    let currentReward = 0;
    let stepCount = 0;

    for (const step of SIMULATION_SEQUENCE) {
      await new Promise(resolve => setTimeout(resolve, step.delay));
      
      // Update state
      stepCount++;
      setSimStep(stepCount);
      
      if (step.type === 'reward') {
        currentReward += (step.rewardValue || 0);
        setCumulativeReward(currentReward);
      }

      setLogs(prev => [...prev, {
        id: `log-${Date.now()}`,
        type: step.type as LogType,
        content: step.content,
        metadata: step.metadata,
        rewardValue: step.rewardValue,
        timestamp: Date.now()
      }]);
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLogs(prev => [...prev, { id: 'end', type: 'system', content: 'Investigation Complete. Incident Report Generated.', timestamp: Date.now() }]);
    setIsSimulating(false);
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
                placeholder="Ex: Investigate suspicious login activity from external IP 45.13.12.99..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-4 pr-32 py-3 text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-slate-100 placeholder-slate-600"
              />
              <button 
                onClick={runSimulation}
                disabled={isSimulating || !prompt}
                className="absolute right-1.5 top-1.5 bottom-1.5 px-4 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {isSimulating ? <Activity className="animate-spin" size={14} /> : <Play size={14} />}
                {isSimulating ? 'Running' : 'Execute'}
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
              <div className="text-sm font-medium text-blue-300 truncate">APT29 Lateral Movement</div>
            </div>
          </div>

          {/* Topology View */}
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
               <TopologyMap hosts={INITIAL_HOSTS} activeStep={simStep} />
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
                    <th className="px-6 py-2 font-medium">Type</th>
                    <th className="px-6 py-2 font-medium">Value</th>
                    <th className="px-6 py-2 font-medium">Impact</th>
                  </tr>
                </thead>
                <tbody className="text-xs font-mono divide-y divide-slate-800">
                  {simStep >= 4 && (
                    <tr className="hover:bg-slate-800/50 animate-fadeIn">
                      <td className="px-6 py-3 text-slate-400">02:14:00</td>
                      <td className="px-6 py-3 text-blue-300">Network</td>
                      <td className="px-6 py-3 text-slate-300">SSH / 45.13.12.99</td>
                      <td className="px-6 py-3 text-amber-400">Initial Access</td>
                    </tr>
                  )}
                  {simStep >= 9 && (
                    <tr className="hover:bg-slate-800/50 animate-fadeIn">
                      <td className="px-6 py-3 text-slate-400">02:22:10</td>
                      <td className="px-6 py-3 text-blue-300">Flow Log</td>
                      <td className="px-6 py-3 text-slate-300">GW-01 -&gt; DB-PROD (2.5GB)</td>
                      <td className="px-6 py-3 text-red-400">Exfiltration</td>
                    </tr>
                  )}
                  {simStep >= 13 && (
                    <tr className="hover:bg-slate-800/50 animate-fadeIn">
                      <td className="px-6 py-3 text-slate-400">02:22:15</td>
                      <td className="px-6 py-3 text-blue-300">Auth Log</td>
                      <td className="px-6 py-3 text-slate-300">User: svc_backup</td>
                      <td className="px-6 py-3 text-red-400">Privilege Escalation</td>
                    </tr>
                  )}
                </tbody>
              </table>
              {simStep < 4 && (
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