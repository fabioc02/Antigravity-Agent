import React, { useState, useEffect, useRef } from 'react';
import { Activity, Folder, TerminalSquare, CheckSquare, Settings, Play, Square, Github, Monitor, Database, Cpu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const ngrokFetch = (url: string, options: any = {}) => {
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'ngrok-skip-browser-warning': 'true'
    }
  });
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [projects, setProjects] = useState([]);
  const [health, setHealth] = useState<any>({});
  
  const [currentProject, setCurrentProject] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<string | null>(null);
  
  useEffect(() => {
    ngrokFetch('/api/health').then(r => r.json()).then(setHealth).catch(console.error);
    ngrokFetch('/api/projects').then(r => r.json()).then(data => setProjects(data.projects)).catch(console.error);
  }, []);

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-neutral-200 font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="flex-1 overflow-auto bg-[#111111] p-6 shadow-xl m-2 rounded-xl border border-neutral-800 flex flex-col">
        {activeTab === 'dashboard' && <Dashboard health={health} projects={projects} />}
        {activeTab === 'projects' && <Projects projects={projects} setProject={setCurrentProject} setTab={setActiveTab} />}
        {activeTab === 'tasks' && <Tasks project={currentProject} setTask={setCurrentTask} setTab={setActiveTab} />}
        {activeTab === 'terminal' && <AgentTerminal project={currentProject} task={currentTask} />}
        {activeTab === 'github' && <GithubTab project={currentProject} />}
        {activeTab === 'bridge' && <BridgeTab />}
        {activeTab === 'runtime' && <RuntimeTab />}
        {activeTab === 'memory' && <MemoryTab />}
        {!['dashboard', 'projects', 'tasks', 'terminal', 'github', 'bridge', 'runtime', 'memory'].includes(activeTab) && (
          <div className="flex flex-col items-center justify-center h-full text-neutral-500 space-y-4">
            <Settings className="w-12 h-12 opacity-50" />
            <h2 className="text-xl font-bold text-neutral-400">Módulo em Desenvolvimento</h2>
            <p>A aba "{activeTab}" ainda está sendo implementada no backend.</p>
          </div>
        )}
      </main>
    </div>
  );
}

function Sidebar({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (t: string) => void }) {
  const items = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'projects', label: 'Projetos', icon: Folder },
    { id: 'tasks', label: 'Tarefas', icon: CheckSquare },
    { id: 'terminal', label: 'Execução (Terminal)', icon: TerminalSquare },
    { id: 'github', label: 'GitHub', icon: Github },
    { id: 'bridge', label: 'PC Bridge', icon: Monitor },
    { id: 'runtime', label: 'Runtime', icon: Cpu },
    { id: 'memory', label: 'Memória', icon: Database },
  ];

  return (
    <aside className="w-64 bg-[#0a0a0a] p-4 border-r border-neutral-800">
      <div className="mb-8 px-4 font-bold text-xl text-indigo-400 tracking-tight flex items-center gap-2">
        <Activity className="w-6 h-6" /> Antigravity Web
      </div>
      <nav className="space-y-1">
        {items.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${activeTab === item.id ? 'bg-indigo-50 text-indigo-400' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100'}`}
          >
            <item.icon className="w-5 h-5" /> {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

function Dashboard({ health, projects }: any) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="API Status" value={health?.status === 'ok' ? 'ONLINE' : 'OFFLINE'} icon={Activity} />
        <StatCard title="Projetos" value={projects?.length || 0} icon={Folder} />
        <StatCard title="PC Bridge" value="ONLINE" icon={Monitor} />
        <StatCard title="Runtime" value="RUNNING" icon={Cpu} />
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon }: any) {
  return (
    <div className="p-4 border border-neutral-800 rounded-xl bg-[#0a0a0a] text-neutral-200 flex items-center gap-4">
      <div className="p-3 bg-[#111111] rounded-lg shadow-sm border border-neutral-800 text-indigo-400"><Icon /></div>
      <div><div className="text-sm text-neutral-400 font-medium">{title}</div><div className="text-lg font-bold">{value}</div></div>
    </div>
  );
}

function Projects({ projects, setProject, setTab }: any) {
  const [name, setName] = useState('');
  
  const createProject = async () => {
    if(!name) return;
    try {
      const res = await ngrokFetch('/api/projects', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setProject(data.project_id);
      setTab('tasks');
    } catch (e: any) {
      alert("Erro ao criar projeto: " + e.message);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Projetos</h1>
      <div className="flex gap-2">
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Novo Projeto..." className="bg-[#111111] border border-neutral-800 p-2 rounded-lg flex-1 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
        <button onClick={createProject} className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-500 transition-colors font-medium">Criar Projeto</button>
      </div>
      <div className="space-y-2">
        {projects.map((p: any) => (
          <div key={p.project_id} className="p-4 border border-neutral-800 bg-[#111111] rounded-lg flex justify-between items-center hover:border-neutral-700 transition-colors">
            <span className="font-medium">{p.project_id}</span>
            <button onClick={() => { setProject(p.project_id); setTab('tasks'); }} className="text-indigo-400 font-medium hover:text-indigo-300 transition-colors">Abrir</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function Tasks({ project, setTask, setTab }: any) {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');

  useEffect(() => {
    if(project) {
      ngrokFetch(`/api/projects/${project}/tasks`).then(r => r.json()).then(d => setTasks(d.tasks)).catch(console.error);
    }
  }, [project]);

  const createTask = async () => {
    if(!title || !project) return;
    try {
      const res = await ngrokFetch(`/api/projects/${project}/tasks`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ title }) });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setTask(data.task_id);
      setTab('terminal');
    } catch (e: any) {
      alert("Erro ao criar tarefa: " + e.message);
    }
  };

  if(!project) return <div>Selecione um projeto primeiro.</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Instruções para o Agente (Projeto: {project})</h1>
      <div className="flex flex-col gap-4 bg-[#111111] p-4 rounded-xl border border-neutral-800">
        <label className="text-neutral-400 font-medium">O que você quer que o agente construa ou faça?</label>
        <textarea 
          value={title} 
          onChange={e => setTitle(e.target.value)} 
          placeholder="Ex: Crie um script python que baixa um vídeo do youtube..." 
          className="bg-[#050505] border border-neutral-800 p-3 rounded-lg w-full text-neutral-200 placeholder-neutral-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[100px]" 
        />
        <button onClick={createTask} className="bg-indigo-600 text-white px-4 py-3 rounded-lg hover:bg-indigo-500 transition-colors font-bold w-full md:w-auto self-end">
          Enviar para o Agente
        </button>
      </div>
      <div className="space-y-2 mt-8">
        <h2 className="text-xl font-bold text-neutral-400 mb-4">Histórico de Tarefas</h2>
        {tasks.map((t: any) => (
          <div key={t.task_id} className="p-4 border border-neutral-800 bg-[#111111] rounded-lg flex justify-between items-center hover:border-neutral-700 transition-colors">
            <span className="font-medium text-neutral-300">{t.description || t.title || t.task_id} ({t.status})</span>
            <button onClick={() => { setTask(t.task_id); setTab('terminal'); }} className="text-indigo-400 font-medium hover:text-indigo-300 transition-colors bg-indigo-900/30 px-3 py-1 rounded">Abrir Terminal</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function AgentTerminal({ project, task }: any) {
  const [session, setSession] = useState<string|null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  
  const startAgent = async () => {
    setEvents([]);
    try {
      const res = await ngrokFetch('/api/agent/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ project_id: project, task_id: task }) });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`HTTP Error ${res.status}: ${errText}`);
      }
      const data = await res.json();
      setSession(data.session_id);
    } catch (e: any) {
      setEvents([{ type: 'error', error: 'Falha ao conectar com o backend: ' + e.message }]);
    }
  };
  
  const cancelAgent = async () => {
    if(session) {
      try {
        await ngrokFetch(`/api/sessions/${session}/cancel`, { method: 'POST' });
      } catch (e: any) {
        setEvents(prev => [...prev, { type: 'error', error: 'Falha ao cancelar: ' + e.message }]);
      }
    }
  };

  useEffect(() => {
    if (!session) return;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/sessions/${session}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onmessage = (e) => {
      const event = JSON.parse(e.data);
      setEvents(prev => [...prev, event]);
    };

    ws.onerror = (e) => {
      console.error("WebSocket Error:", e);
      setEvents(prev => [...prev, { type: 'error', error: 'Erro de conexão no WebSocket. Verifique o console do navegador.' }]);
    };
    
    ws.onclose = () => {
      console.log("WebSocket Closed");
    };
    
    return () => { ws.close(); };
  }, [session]);

  if(!project || !task) return <div>Selecione um projeto e uma tarefa.</div>;

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold flex items-center gap-2"><TerminalSquare /> Agent Terminal</h1>
        <div className="space-x-2">
           <button onClick={startAgent} className="bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 flex items-center gap-2"><Play className="w-4 h-4"/> INICIAR AGENTE</button>
           <button onClick={cancelAgent} className="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 flex items-center gap-2"><Square className="w-4 h-4"/> CANCELAR</button>
        </div>
      </div>
      
      <div className="flex-1 bg-[#050505] text-neutral-300 p-4 rounded-xl overflow-auto font-mono text-sm space-y-2 border border-neutral-800 shadow-inner">
        {events.length === 0 && <div className="text-neutral-400">Aguardando execução...</div>}
        {events.map((ev, i) => (
          <div key={i} className={`p-2 rounded ${ev.type === 'error' ? 'bg-red-900/50 text-red-200' : ev.type === 'tool_call' ? 'bg-indigo-900/30' : 'bg-gray-800'}`}>
            <span className="font-bold text-indigo-400 mr-2">[{ev.type.toUpperCase()}]</span>
            {ev.type === 'llm_message' && <span className="text-green-300">{ev.content}</span>}
            {ev.type === 'tool_call' && <span className="text-blue-300">Ferramenta: {ev.tool} - Args: {JSON.stringify(ev.args)}</span>}
            {ev.type === 'tool_result' && <span className="text-gray-300 whitespace-pre-wrap">{JSON.stringify(ev.result, null, 2)}</span>}
            {ev.type === 'error' && <span className="text-red-300">{ev.error}</span>}
            {ev.type === 'session_started' && <span className="text-yellow-300">Sessão Iniciada!</span>}
            {ev.type === 'session_completed' && <span className="text-yellow-300 font-bold text-lg">Sessão Concluída! {JSON.stringify(ev.result)}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

function GithubTab({ project }: any) {
  const [status, setStatus] = useState<any>(null);
  useEffect(() => {
    if(project) {
      ngrokFetch(`/api/github/status?project_id=${project}`).then(r => r.json()).then(setStatus).catch(console.error);
    }
  }, [project]);

  if(!project) return <div className="text-neutral-400 p-6">Selecione um projeto na aba Projetos primeiro.</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2"><Github /> Integração GitHub</h1>
      <div className="bg-[#111111] p-6 rounded-xl border border-neutral-800 space-y-4 shadow-sm">
        {status ? (
          <div>
            <div className="font-bold mb-2 text-indigo-400">Repositório Remoto:</div>
            <div className="bg-[#050505] p-3 rounded text-neutral-300 font-mono text-sm break-all">{status.remote || 'Nenhum repositório configurado'}</div>
            <div className="font-bold mt-4 mb-2 text-indigo-400">Status Local (Diff):</div>
            <pre className="bg-[#050505] p-3 rounded text-neutral-300 font-mono text-sm overflow-x-auto whitespace-pre-wrap">
              {status.diff || 'Nenhuma alteração local.'}
            </pre>
          </div>
        ) : (
          <div className="text-neutral-400">Carregando status do GitHub...</div>
        )}
      </div>
    </div>
  );
}

function BridgeTab() {
  const [status, setStatus] = useState<any>(null);
  useEffect(() => {
    ngrokFetch('/api/bridge/status').then(r => r.json()).then(setStatus).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2"><Monitor /> PC Bridge (Acesso Local)</h1>
      <div className="bg-[#111111] p-6 rounded-xl border border-neutral-800 space-y-4 shadow-sm">
        {status ? (
          <div>
            <div className="font-bold mb-2 text-indigo-400">Status do Tunel:</div>
            <div className="bg-[#050505] p-3 rounded text-neutral-300 font-mono text-sm">
               {status.status === 'ONLINE' ? <span className="text-green-400 font-bold">ONLINE</span> : <span className="text-red-400 font-bold">{status.status}</span>}
            </div>
            {status.endpoint && (
              <>
                <div className="font-bold mt-4 mb-2 text-indigo-400">Endpoint Configurado:</div>
                <div className="bg-[#050505] p-3 rounded text-neutral-300 font-mono text-sm">{status.endpoint}</div>
              </>
            )}
            {status.error && <div className="text-red-400 mt-2 font-medium">{status.error}</div>}
          </div>
        ) : (
          <div className="text-neutral-400">Carregando PC Bridge...</div>
        )}
      </div>
    </div>
  );
}

function RuntimeTab() {
  const [runtime, setRuntime] = useState<any>(null);
  useEffect(() => {
    ngrokFetch('/api/runtime').then(r => r.json()).then(setRuntime).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2"><Cpu /> Status do Runtime (LLM)</h1>
      <div className="bg-[#111111] p-6 rounded-xl border border-neutral-800 space-y-4 shadow-sm">
        {runtime ? (
          <div>
            <pre className="bg-[#050505] p-4 rounded-lg text-neutral-300 font-mono text-sm overflow-x-auto">
              {JSON.stringify(runtime, null, 2)}
            </pre>
          </div>
        ) : (
          <div className="text-neutral-400">Carregando informações do Runtime...</div>
        )}
      </div>
    </div>
  );
}

function MemoryTab() {
  const [sessions, setSessions] = useState<any[]>([]);
  useEffect(() => {
    ngrokFetch('/api/sessions').then(r => r.json()).then(d => setSessions(d.sessions || [])).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2"><Database /> Memória e Histórico de Sessões</h1>
      <div className="grid grid-cols-1 gap-4">
        {sessions.length === 0 ? (
          <div className="text-neutral-500 p-4">Nenhuma sessão encontrada na memória do Google Drive.</div>
        ) : sessions.map((sess: any, idx: number) => (
          <div key={idx} className="bg-[#111111] p-5 rounded-xl border border-neutral-800 space-y-3 shadow-sm hover:border-neutral-700 transition-colors">
            <div className="flex justify-between items-center">
              <span className="font-bold text-indigo-400 font-mono">{sess.session_id}</span>
              <span className={`text-xs px-2 py-1 rounded font-bold ${sess.status === 'RUNNING' ? 'bg-yellow-900/50 text-yellow-400' : 'bg-green-900/50 text-green-400'}`}>
                {sess.status}
              </span>
            </div>
            <div className="text-sm text-neutral-300 font-mono">
              Projeto: <span className="text-neutral-400">{sess.project_id}</span> <br/>
              Tarefa: <span className="text-neutral-400">{sess.task_id}</span>
            </div>
            <div className="text-xs text-neutral-500 flex justify-between">
              <span>Iniciado em: {new Date(sess.started_at * 1000).toLocaleString()}</span>
              <span>Iterações: {sess.iteration}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
