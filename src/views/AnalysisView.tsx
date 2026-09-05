import Markdown from 'react-markdown';
import analysisMd from '../data/analysis.md?raw';
import { FileText, Cpu, Server, Shield, Brain } from 'lucide-react';

export default function AnalysisView() {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center space-x-3 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
          <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
          Arquitetura do Agente
        </h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex items-start space-x-4">
          <Brain className="w-8 h-8 text-purple-500" />
          <div>
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">Cérebro</h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Qwen 2.5 Coder (7B/32B AWQ) + vLLM</p>
          </div>
        </div>
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex items-start space-x-4">
          <Cpu className="w-8 h-8 text-green-500" />
          <div>
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">Ambiente (Colab)</h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">GPU T4 (16GB VRAM) / Drive + Workspace</p>
          </div>
        </div>
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex items-start space-x-4">
          <Shield className="w-8 h-8 text-amber-500" />
          <div>
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">Segurança</h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Local Bridge c/ Whitelist Strict</p>
          </div>
        </div>
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex items-start space-x-4">
          <Server className="w-8 h-8 text-blue-500" />
          <div>
            <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">Ferramentas</h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Git, Terminal, FileSystem, Build Tools</p>
          </div>
        </div>
      </div>

      <div className="prose prose-zinc dark:prose-invert max-w-none bg-white dark:bg-zinc-900 p-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
        <Markdown>{analysisMd}</Markdown>
      </div>
    </div>
  );
}
