import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, Bot, Sparkles, Loader, Wifi, WifiOff, HelpCircle, X, History, GitBranch, Cpu, HardDrive, Activity, FolderOpen, Terminal, Brain, Zap, Bug, Code, Eye, EyeOff, Copy, Check, ChevronDown, ChevronUp, Lightbulb, RefreshCw, Cloud, CloudOff, FileCode, Edit3, Plus, FilePlus, Download, Save, File, ExternalLink, Search, Play, Trash2, Edit } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000';

const DEBUG_PROMPTS = [
  { label: 'Debug Error', prompt: 'Find and fix this bug: ', icon: Bug },
  { label: 'Explain Code', prompt: 'Explain this code: ', icon: Code },
  { label: 'Fix Bug', prompt: 'Find and fix the bug in: ', icon: Zap },
  { label: 'Review Code', prompt: 'Review this code for issues: ', icon: Eye },
];

const PROJECT_ACTIONS = [
  { label: 'Analyze Project', prompt: 'Analyze this entire project. Show me: 1) Project structure, 2) Tech stack, 3) Main entry points, 4) Dependencies, 5) What it does', icon: FolderOpen },
  { label: 'Add Feature', prompt: 'Add a new feature to this project: ', icon: Plus },
  { label: 'Refactor', prompt: 'Refactor and improve this code: ', icon: Edit3 },
  { label: 'Create API', prompt: 'Create a new API endpoint for: ', icon: Code },
  { label: 'Add Tests', prompt: 'Add unit tests for: ', icon: FileCode },
  { label: 'Fix Issues', prompt: 'Find and fix all issues in: ', icon: Zap },
  { label: 'Plan + Write', prompt: 'PLAN_WRITE /path/to/file:reason for change:code to write', icon: Edit },
];

const SCRIPT_ACTIONS = [
  { label: 'Python Script', prompt: 'Write a production-ready Python script with argparse, logging, and error handling for: ', icon: FileCode },
  { label: 'Bash Script', prompt: 'Write a professional bash script with usage function and error handling for: ', icon: Terminal },
  { label: 'Node Script', prompt: 'Write a Node.js script with async/await and proper error handling for: ', icon: FileCode },
  { label: 'API Script', prompt: 'Write a REST API client script in Python with requests library for: ', icon: Code },
];

const QUICK_ACTIONS = [
  { label: 'Git Status', cmd: 'GIT_STATUS ', icon: GitBranch },
  { label: 'System Info', cmd: 'SYSTEM_INFO ', icon: Cpu },
  { label: 'Project Tree', cmd: 'PROJECT_STRUCTURE .', icon: FolderOpen },
  { label: 'Count Lines', cmd: 'COUNT_LINES .', icon: Activity },
  { label: 'New Python', prompt: 'Create a new Python script for: ', icon: FilePlus },
  { label: 'New Bash', prompt: 'Create a new bash script for: ', icon: Terminal },
];

const ONLINE_ACTIONS = [
  { label: 'Install Tool', prompt: 'INSTALL ', icon: Download },
  { label: 'Check Installed', prompt: 'CHECK_INSTALLED ', icon: Search },
  { label: 'Download File', prompt: 'DOWNLOAD_URL ', icon: ExternalLink },
  { label: 'Read URL', prompt: 'READ_URL ', icon: Activity },
];

export default function DevAI() {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(null);
  const [offlineMode, setOfflineMode] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showAllThinking, setShowAllThinking] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [debugInput, setDebugInput] = useState('');
  const [currentThinking, setCurrentThinking] = useState('');
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const thinkingCache = useRef({});

  useEffect(() => {
    fetch(`${API}/devai/status`)
      .then(r => r.json())
      .then(d => {
        setIsOffline(!d.status?.includes('ready'));
        setOfflineMode(d.offline !== false);
      })
      .catch(() => setIsOffline(true));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentThinking]);

  const send = async (text, skipHistory = false) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    if (!skipHistory) {
      setCommandHistory(prev => [trimmed, ...prev.slice(0, 49)]);
      setHistoryIndex(-1);
    }

    const userMsg = { role: 'user', text: trimmed };
    const assistantMsg = { role: 'assistant', text: '', thinking: '', showThinking: true };
    
    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setInput('');
    setLoading(true);
    setCurrentThinking('🤔 Analyzing your request and planning...');
    setDebugInput('');

    try {
      // Always use streaming for live thinking
      const response = await fetch(`${API}/devai/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, stream: true }),
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let thinkingBuffer = '';
      let inThinking = false;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            
            // Handle thinking tags
            if (data.includes('<think>')) {
              inThinking = true;
              thinkingBuffer = data.replace(/[\s\S]*<think>/, '');
              if (thinkingBuffer) {
                setCurrentThinking(thinkingBuffer);
              }
            } else if (data.includes('</think>')) {
              inThinking = false;
              thinkingBuffer += data.replace(/<\/think>[\s\S]*/, '');
              setCurrentThinking('');
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  thinking: thinkingBuffer,
                  showThinking: true,
                };
                return updated;
              });
            } else if (inThinking) {
              thinkingBuffer += data;
              setCurrentThinking(thinkingBuffer + '...');
            } else {
              fullResponse += data;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  text: fullResponse,
                };
                return updated;
              });
            }
          }
        }
      }
      
      // Save final thinking
      if (thinkingBuffer) {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            thinking: thinkingBuffer,
            showThinking: true,
          };
          return updated;
        });
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          text: 'Failed to reach Dev AI Pro. Is the backend running?',
        };
        return updated;
      });
    } finally {
      setLoading(false);
      setCurrentThinking('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
    if (e.key === 'ArrowUp' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        setInput(commandHistory[newIndex]);
      }
    }
    if (e.key === 'ArrowDown' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setInput(commandHistory[newIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setInput('');
      }
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const downloadText = (text, filename = 'output.txt') => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const extractCodeBlocks = (text) => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const blocks = [];
    let match;
    while ((match = codeBlockRegex.exec(text)) !== null) {
      blocks.push({
        language: match[1] || 'txt',
        code: match[2].trim()
      });
    }
    return blocks;
  };

  const downloadCode = (code, language, index) => {
    const extensions = {
      python: 'py', javascript: 'js', typescript: 'ts', bash: 'sh', shell: 'sh',
      html: 'html', css: 'css', json: 'json', markdown: 'md', sql: 'sql',
      go: 'go', rust: 'rs', java: 'java', c: 'c', cpp: 'cpp'
    };
    const ext = extensions[language.toLowerCase()] || 'txt';
    const filename = `devai_script_${index + 1}.${ext}`;
    downloadText(code, filename);
  };

  const toggleThinking = (index) => {
    setMessages(prev => {
      const updated = [...prev];
      if (updated[index] && updated[index].role === 'assistant') {
        updated[index] = { ...updated[index], showThinking: !updated[index].showThinking };
      }
      return updated;
    });
  };

  const handleDebug = (type) => {
    const prompt = DEBUG_PROMPTS.find(p => p.label === type)?.prompt || '';
    setDebugMode(true);
    setInput(prompt);
    inputRef.current?.focus();
  };

  const formatOutput = (text) => {
    if (!text) return '';
    return text.split('\n').map((line, i) => {
      const formatted = line
        .replace(/✅/g, '<span class="text-green-400">✅</span>')
        .replace(/❌/g, '<span class="text-red-400">❌</span>')
        .replace(/📄/g, '<span class="text-blue-400">📄</span>')
        .replace(/📁/g, '<span class="text-yellow-400">📁</span>')
        .replace(/📂/g, '<span class="text-purple-400">📂</span>')
        .replace(/🔍/g, '<span class="text-cyan-400">🔍</span>')
        .replace(/🌐/g, '<span class="text-blue-400">🌐</span>')
        .replace(/🌳/g, '<span class="text-green-400">🌳</span>')
        .replace(/🖥️/g, '<span class="text-gray-400">🖥️</span>')
        .replace(/💻/g, '<span class="text-blue-400">💻</span>')
        .replace(/🧠/g, '<span class="text-pink-400">🧠</span>')
        .replace(/💾/g, '<span class="text-orange-400">💾</span>')
        .replace(/⚡/g, '<span class="text-yellow-400">⚡</span>')
        .replace(/📊/g, '<span class="text-indigo-400">📊</span>')
        .replace(/🔒/g, '<span class="text-red-400">🔒</span>')
        .replace(/🔧/g, '<span class="text-orange-400">🔧</span>')
        .replace(/🐛/g, '<span class="text-red-400">🐛</span>')
        .replace(/💡/g, '<span class="text-yellow-400">💡</span>')
        .replace(/📌/g, '<span class="text-blue-400">📌</span>')
        .replace(/<!--/g, '<span class="text-gray-500">&lt;!--</span>')
        .replace(/-->/g, '<span class="text-gray-500">--&gt;</span>');
      return <span key={i} className="block whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: formatted }} />;
    });
  };

  const formatThinking = (thinking) => {
    if (!thinking) return '';
    return thinking.split('\n').map((line, i) => {
      const formatted = line
        .replace(/^[\s]*\*\*?(.*?)\*\*?:?/g, '<span class="text-purple-400 font-semibold">$1:</span>')
        .replace(/`([^`]+)`/g, '<span class="text-green-400 bg-black/30 px-1 rounded">$1</span>')
        .replace(/\*\*([^*]+)\*\*/g, '<span class="font-bold text-white">$1</span>');
      return <span key={i} className="block" dangerouslySetInnerHTML={{ __html: formatted || '&nbsp;' }} />;
    });
  };

  return (
    <div
      className="relative w-full h-full flex flex-col overflow-hidden"
      style={{ background: 'var(--bg)', fontFamily: 'var(--font-body)', color: 'var(--text)' }}
    >
      <div className="ambient-bg" />
      <div className="blob blob-1" />
      <div className="blob blob-2" />

      {/* Header */}
      <div
        className="flex-shrink-0 flex items-center gap-2 px-3 py-2 z-10"
        style={{
          background: 'var(--surface)',
          backdropFilter: 'blur(14px)',
          borderBottom: '1.5px solid var(--border)',
        }}
      >
        <button
          onClick={() => navigate('/')}
          className="p-2 rounded-xl border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all flex items-center justify-center min-h-[44px] min-w-[44px]"
          aria-label="Back"
        >
          <ArrowLeft size={20} />
        </button>
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
          style={{ background: 'var(--ai-bg)' }}
        >
          <Sparkles size={20} style={{ color: 'var(--ai-color)' }} />
        </div>
        <div className="flex-1 min-w-0">
          <h1 style={{ fontFamily: 'var(--font-head)', fontWeight: 800, color: 'var(--ai-color)', fontSize: '1rem' }}>
            Dev AI Pro
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <button
              onClick={() => setOfflineMode(!offlineMode)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all hover:scale-105"
              style={{ 
                background: offlineMode ? 'rgba(34,197,94,.2)' : 'rgba(59,130,246,.2)',
                color: offlineMode ? '#22c55e' : '#3b82f6',
                border: `2px solid ${offlineMode ? '#22c55e' : '#3b82f6'}`,
              }}
            >
              {offlineMode ? <CloudOff size={12} /> : <Cloud size={12} />}
              {offlineMode ? 'OFFLINE' : 'ONLINE'}
            </button>
            <span style={{ fontSize: '.6rem', color: 'var(--text-mid)' }}>
              {offlineMode ? 'Local AI' : 'Cloud AI'}
            </span>
          </div>
        </div>
        <button
          onClick={() => setShowHistory(true)}
          className="p-2 rounded-xl border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all flex items-center justify-center min-h-[44px] min-w-[44px]"
          aria-label="History"
        >
          <History size={18} />
        </button>
        <button
          onClick={() => setShowHelp(true)}
          className="p-2 rounded-xl border-2 border-[var(--border)] text-[var(--text-mid)] hover:border-[var(--ai-color)] hover:text-[var(--ai-color)] transition-all flex items-center justify-center min-h-[44px] min-w-[44px]"
          aria-label="Help"
        >
          <HelpCircle size={18} />
        </button>
      </div>

      {/* Project, Debug, Script & Quick Actions Bar */}
      <div className="flex-shrink-0 px-2 py-2 flex flex-col gap-2" style={{ background: 'var(--surface)' }}>
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
          <span style={{ fontSize: '.65rem', color: 'var(--text-mid)', whiteSpace: 'nowrap' }}>PROJECT:</span>
          {PROJECT_ACTIONS.map(({ label, prompt, icon: Icon }) => (
            <button
              key={label}
              onClick={() => { setInput(prompt); inputRef.current?.focus(); }}
              disabled={loading}
              className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all disabled:opacity-50 hover:scale-105"
              style={{ background: 'rgba(124,58,237,.15)', color: '#7c3aed', border: '1px solid rgba(124,58,237,.3)' }}
            >
              <Icon size={11} />
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
          <span style={{ fontSize: '.65rem', color: 'var(--text-mid)', whiteSpace: 'nowrap' }}>SCRIPT:</span>
          {SCRIPT_ACTIONS.map(({ label, prompt, icon: Icon }) => (
            <button
              key={label}
              onClick={() => { setInput(prompt); inputRef.current?.focus(); }}
              disabled={loading}
              className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all disabled:opacity-50 hover:scale-105"
              style={{ background: 'rgba(34,197,94,.15)', color: '#22c55e', border: '1px solid rgba(34,197,94,.3)' }}
            >
              <Icon size={11} />
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
          <span style={{ fontSize: '.65rem', color: 'var(--text-mid)', whiteSpace: 'nowrap' }}>DEBUG:</span>
          {DEBUG_PROMPTS.map(({ label, prompt, icon: Icon }) => (
            <button
              key={label}
              onClick={() => handleDebug(label)}
              disabled={loading}
              className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all disabled:opacity-50 hover:scale-105"
              style={{ background: 'rgba(239,68,68,.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,.3)' }}
            >
              <Icon size={11} />
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
          <span style={{ fontSize: '.65rem', color: 'var(--text-mid)', whiteSpace: 'nowrap' }}>QUICK:</span>
          {QUICK_ACTIONS.map(({ label, cmd, prompt, icon: Icon }) => (
            <button
              key={label}
              onClick={() => prompt ? (setInput(prompt), inputRef.current?.focus()) : send(cmd, true)}
              disabled={loading}
              className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all disabled:opacity-50 hover:scale-105"
              style={{ background: 'var(--ai-bg)', color: 'var(--ai-color)', border: '1px solid var(--ai-color)' }}
            >
              <Icon size={11} />
              {label}
            </button>
          ))}
        </div>
        {offlineMode === false && (
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
            <span style={{ fontSize: '.65rem', color: '#3b82f6', whiteSpace: 'nowrap' }}>🌐 ONLINE:</span>
            {ONLINE_ACTIONS.map(({ label, cmd, prompt, icon: Icon }) => (
              <button
                key={label}
                onClick={() => prompt ? (setInput(prompt), inputRef.current?.focus()) : send(cmd, true)}
                disabled={loading}
                className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all disabled:opacity-50 hover:scale-105"
                style={{ background: 'rgba(59,130,246,.15)', color: '#3b82f6', border: '1px solid rgba(59,130,246,.3)' }}
              >
                <Icon size={11} />
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 flex flex-col gap-3 scroller-ai touch-scroll-y">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center py-10">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-18 h-18 rounded-2xl flex items-center justify-center"
              style={{ background: 'var(--ai-bg)' }}
            >
              <Brain size={36} style={{ color: 'var(--ai-color)' }} />
            </motion.div>
            <div>
              <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 800, color: 'var(--ai-color)', fontSize: '1rem', marginBottom: 4 }}>
                Dev AI Pro
              </h2>
              <p style={{ color: 'var(--text-mid)', fontSize: '.8rem', maxWidth: 260, lineHeight: 1.5 }}>
                Your smart coding assistant. Ask anything - I'll show my thinking!
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 max-w-xs">
              {['fix this bug', 'explain this code', 'write a function', 'debug error'].map((hint, i) => (
                <button
                  key={i}
                  onClick={() => send(hint)}
                  className="px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:scale-105"
                  style={{ background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              {msg.role === 'user' ? (
                <div
                  className="max-w-[85%] px-4 py-2.5 rounded-2xl text-sm"
                  style={{
                    background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
                    color: '#fff',
                    borderRadius: '18px 18px 4px 18px',
                  }}
                >
                  <pre className="whitespace-pre-wrap break-words text-xs leading-relaxed" style={{ fontFamily: 'var(--font-body)' }}>
                    {msg.text}
                  </pre>
                </div>
              ) : (
                <div className="w-full max-w-[95%]">
                  {/* Thinking Section - Always visible when available */}
                  {msg.thinking && (
                    <div className="mb-2">
                      <div
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs"
                        style={{ background: 'rgba(168,85,247,.15)', color: '#a855f7', border: '1px solid rgba(168,85,247,.3)' }}
                      >
                        <Brain size={12} />
                        <span className="font-medium">My Thinking</span>
                        {msg.showThinking && (
                          <button
                            onClick={() => toggleThinking(i)}
                            className="ml-auto hover:opacity-70"
                          >
                            <ChevronUp size={12} />
                          </button>
                        )}
                      </div>
                      
                      <AnimatePresence>
                        {msg.thinking && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-2 p-3 rounded-xl overflow-hidden"
                            style={{ background: 'rgba(0,0,0,.6)', border: '1px solid rgba(168,85,247,.3)' }}
                          >
                            <pre className="text-xs leading-relaxed whitespace-pre-wrap font-mono" style={{ color: '#e9d5ff' }}>
                              {formatThinking(msg.thinking)}
                            </pre>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                  
                  {/* Response */}
                  <div
                    className="px-4 py-3 rounded-2xl"
                    style={{
                      background: 'var(--surface)',
                      color: 'var(--text)',
                      border: '1.5px solid var(--border)',
                      borderRadius: '18px 18px 18px 4px',
                    }}
                  >
                    <div className="flex justify-end gap-2 mb-2">
                      <button
                        onClick={() => downloadText(msg.text, `devai_response_${i + 1}.txt`)}
                        className="p-1.5 rounded hover:bg-[var(--bg)] transition-colors flex items-center gap-1"
                        title="Download"
                        style={{ color: 'var(--text-mid)' }}
                      >
                        <Download size={12} />
                        <span style={{ fontSize: '.65rem' }}>Txt</span>
                      </button>
                      {extractCodeBlocks(msg.text).length > 0 && (
                        <button
                          onClick={() => {
                            const blocks = extractCodeBlocks(msg.text);
                            if (blocks.length === 1) {
                              downloadCode(blocks[0].code, blocks[0].language, i);
                            } else {
                              blocks.forEach((block, bi) => downloadCode(block.code, block.language, i + bi));
                            }
                          }}
                          className="p-1.5 rounded hover:bg-[var(--bg)] transition-colors flex items-center gap-1"
                          title="Download Code"
                          style={{ color: 'var(--ai-color)' }}
                        >
                          <Save size={12} />
                          <span style={{ fontSize: '.65rem' }}>Code</span>
                        </button>
                      )}
                      <button
                        onClick={() => copyToClipboard(msg.text, i)}
                        className="p-1.5 rounded hover:bg-[var(--bg)] transition-colors flex items-center gap-1"
                        title="Copy"
                        style={{ color: 'var(--text-mid)' }}
                      >
                        {copiedIndex === i ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
                      </button>
                    </div>
                    <pre
                      className="whitespace-pre-wrap break-words text-xs leading-relaxed font-mono"
                      style={{ color: 'var(--text)' }}
                    >
                      {formatOutput(msg.text)}
                    </pre>
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-start w-full"
          >
            {/* Live Thinking - Always visible during loading */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-4 rounded-2xl w-full"
              style={{ 
                background: 'linear-gradient(135deg, rgba(124,58,237,.25), rgba(139,92,246,.2))', 
                border: '2px solid rgba(168,85,247,.6)',
                boxShadow: '0 0 30px rgba(168,85,247,.4)'
              }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Brain size={18} className="text-purple-400 animate-pulse" />
                <span className="text-sm font-bold text-purple-300">🤔 Dev AI is Thinking...</span>
                <motion.div 
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="ml-auto flex gap-1"
                >
                  <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                  <span className="w-2 h-2 rounded-full bg-purple-400" style={{ animationDelay: '0.2s' }}></span>
                  <span className="w-2 h-2 rounded-full bg-purple-400" style={{ animationDelay: '0.4s' }}></span>
                </motion.div>
              </div>
              {currentThinking ? (
                <pre 
                  className="text-xs leading-relaxed whitespace-pre-wrap font-mono p-3 rounded-lg"
                  style={{ 
                    color: '#e9d5ff', 
                    maxHeight: 250, 
                    overflow: 'auto',
                    background: 'rgba(0,0,0,.4)',
                    textShadow: '0 0 10px rgba(168,85,247,.5)',
                    border: '1px solid rgba(168,85,247,.3)'
                  }}
                >
                  {currentThinking}
                </pre>
              ) : (
                <div className="text-xs text-purple-300/70 italic p-2">
                  Analyzing your request and formulating a response...
                </div>
              )}
            </motion.div>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        className="flex-shrink-0 flex items-end gap-2 px-3 py-3 z-10"
        style={{
          background: 'var(--surface)',
          backdropFilter: 'blur(14px)',
          borderTop: '1.5px solid var(--border)',
        }}
      >
        <div
          className="flex-1 rounded-2xl px-3 py-2 flex items-end border"
          style={{
            background: 'var(--surface)',
            borderColor: 'var(--border)',
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything... (code, debug, explain)"
            rows={1}
            className="flex-1 border-none bg-transparent resize-none outline-none text-sm"
            style={{
              color: 'var(--text)',
              fontFamily: 'monospace',
              lineHeight: 1.5,
              maxHeight: 100,
            }}
            onInput={e => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
            }}
          />
        </div>
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl cursor-pointer transition-all disabled:opacity-40 hover:scale-105"
          style={{
            background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
            color: '#fff',
          }}
          aria-label="Send"
        >
          <Send size={18} />
        </button>
      </div>

      {/* Help Modal */}
      {showHelp && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-2"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          onClick={() => setShowHelp(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-lg max-h-[80vh] overflow-hidden rounded-2xl"
            style={{ background: 'var(--surface)', border: '1.5px solid var(--border)' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 800, color: 'var(--ai-color)', fontSize: '1rem' }}>
                Dev AI Pro Help
              </h2>
              <button onClick={() => setShowHelp(false)} className="p-1.5 rounded-lg hover:bg-[var(--bg)]">
                <X size={18} style={{ color: 'var(--text-mid)' }} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[68vh]">
              <div className="space-y-4">
                <div className="p-3 rounded-xl" style={{ background: 'rgba(168,85,247,.1)', border: '1px solid rgba(168,85,247,.3)' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <Brain size={16} className="text-purple-400" />
                    <span className="font-semibold text-sm" style={{ color: 'var(--text)' }}>💡 Show My Thinking</span>
                  </div>
                  <p style={{ fontSize: '.75rem', color: 'var(--text-mid)' }}>
                    Click "See My Thinking" on any response to see how I analyzed your question!
                  </p>
                </div>
                
                <div className="p-3 rounded-xl" style={{ background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.3)' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <Bug size={16} className="text-red-400" />
                    <span className="font-semibold text-sm" style={{ color: 'var(--text)' }}>🐛 Debug Mode</span>
                  </div>
                  <p style={{ fontSize: '.75rem', color: 'var(--text-mid)' }}>
                    Use debug buttons to: Debug Error, Explain Code, Fix Bug, Review Code
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-sm mb-2" style={{ color: 'var(--ai-color)' }}>Quick Commands</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {QUICK_ACTIONS.map(({ label, cmd }) => (
                      <button
                        key={label}
                        onClick={() => { send(cmd, true); setShowHelp(false); }}
                        className="text-left px-3 py-2 rounded-lg text-xs"
                        style={{ background: 'var(--bg)', color: 'var(--text)' }}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* History Modal */}
      {showHistory && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-2"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          onClick={() => setShowHistory(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-md max-h-[70vh] overflow-hidden rounded-2xl"
            style={{ background: 'var(--surface)', border: '1.5px solid var(--border)' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2">
                <History size={16} style={{ color: 'var(--ai-color)' }} />
                <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 700, color: 'var(--text)', fontSize: '.95rem' }}>
                  History
                </h2>
              </div>
              <button onClick={() => setShowHistory(false)} className="p-1.5 rounded-lg hover:bg-[var(--bg)]">
                <X size={16} style={{ color: 'var(--text-mid)' }} />
              </button>
            </div>
            <div className="overflow-y-auto max-h-[55vh]">
              {commandHistory.length === 0 ? (
                <div className="p-8 text-center" style={{ color: 'var(--text-mid)', fontSize: '.85rem' }}>
                  No history yet
                </div>
              ) : (
                <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                  {commandHistory.map((cmd, i) => (
                    <button
                      key={i}
                      onClick={() => { setInput(cmd); setShowHistory(false); inputRef.current?.focus(); }}
                      className="w-full text-left px-4 py-2.5 hover:bg-[var(--bg)] transition-colors"
                    >
                      <code style={{ color: 'var(--text)', fontSize: '.8rem', fontFamily: 'monospace' }}>{cmd}</code>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
