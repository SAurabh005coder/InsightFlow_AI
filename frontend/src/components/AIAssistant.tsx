import React from 'react';
import axios from 'axios';
import { 
  Bot, 
  Send, 
  X, 
  MessageSquare, 
  Plus, 
  Sparkles, 
  Loader2, 
  ChevronRight,
  Database
} from 'lucide-react';

interface Message {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface Session {
  session_id: string;
  title: string;
  dataset_id?: string;
  created_at: string;
  updated_at: string;
}

interface AIAssistantProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({ isOpen, onClose }) => {
  const [sessions, setSessions] = React.useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = React.useState<string>('');
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState<string>('');
  const [loading, setLoading] = React.useState<boolean>(false);
  const [sessionLoading, setSessionLoading] = React.useState<boolean>(false);
  const [sidebarOpen, setSidebarOpen] = React.useState<boolean>(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const activeDatasetId = localStorage.getItem('active_dataset_id');

  // Fetch list of chat sessions
  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await axios.get('/api/v1/ai/chat/sessions', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(res.data);
      if (res.data.length > 0 && !activeSessionId) {
        setActiveSessionId(res.data[0].session_id);
      }
    } catch (err) {
      console.error('Failed to load chat sessions', err);
    }
  };

  // Fetch messages of active session
  const fetchMessages = async (sid: string) => {
    try {
      setSessionLoading(true);
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await axios.get(`/api/v1/ai/chat/sessions/${sid}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(res.data);
    } catch (err) {
      console.error('Failed to load messages', err);
    } finally {
      setSessionLoading(false);
    }
  };

  // Create new session
  const handleNewSession = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await axios.post('/api/v1/ai/chat/session', {
        title: `Chat Session - ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
        dataset_id: activeDatasetId || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(prev => [res.data, ...prev]);
      setActiveSessionId(res.data.session_id);
      setMessages([]);
      setSidebarOpen(false);
    } catch (err) {
      console.error('Failed to create new chat session', err);
    }
  };

  // Send message
  const handleSendMessage = async (textToSend: string) => {
    const queryText = textToSend.trim();
    if (!queryText) return;
    if (!activeSessionId) {
      // Create session first if none exists
      await handleNewSession();
    }
    
    setInput('');
    // Optimistic local update for quick rendering
    const tempUserMsg: Message = {
      message_id: Math.random().toString(),
      role: 'user',
      content: queryText,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const targetSessionId = activeSessionId || sessions[0]?.session_id;
      if (!token || !targetSessionId) return;

      const res = await axios.post(`/api/v1/ai/chat/sessions/${targetSessionId}/message`, {
        content: queryText
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Update full message history returned by API
      setMessages(res.data.messages);
    } catch (err) {
      console.error('Failed to send query', err);
      // Fallback message
      setMessages(prev => [
        ...prev,
        {
          message_id: Math.random().toString(),
          role: 'assistant',
          content: 'Sorry, the assistant encountered an error. Please try again.',
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Auto-scroll messages
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Load initial data
  React.useEffect(() => {
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen]);

  // Load messages when active session changes
  React.useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
    }
  }, [activeSessionId]);

  if (!isOpen) return null;

  // Simple Markdown Parser to format assistant messages
  const parseMarkdown = (text: string) => {
    return text.split('\n').map((line, idx) => {
      // Headings
      if (line.startsWith('### ')) {
        return <h4 key={idx} className="text-sm font-bold text-cyan-400 mt-3 mb-1.5">{line.replace('### ', '')}</h4>;
      }
      if (line.startsWith('#### ')) {
        return <h5 key={idx} className="text-xs font-semibold text-slate-300 mt-2 mb-1">{line.replace('#### ', '')}</h5>;
      }
      // List items
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        const cleanLine = line.trim().replace(/^[-*]\s+/, '');
        return (
          <li key={idx} className="text-xs text-slate-300 list-disc ml-4 my-0.5">
            {parseInlineFormatting(cleanLine)}
          </li>
        );
      }
      // Standard line
      return line.trim() === '' ? <div key={idx} className="h-2" /> : (
        <p key={idx} className="text-xs text-slate-300 leading-relaxed my-1">
          {parseInlineFormatting(line)}
        </p>
      );
    });
  };

  // Helper to bold items with double asterisk **bold**
  const parseInlineFormatting = (line: string) => {
    const boldRegex = /\*\*(.*?)\*\*/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = boldRegex.exec(line)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        parts.push(line.substring(lastIndex, matchIndex));
      }
      parts.push(<strong key={matchIndex} className="font-semibold text-cyan-300">{match[1]}</strong>);
      lastIndex = boldRegex.lastIndex;
    }

    if (lastIndex < line.length) {
      parts.push(line.substring(lastIndex));
    }

    return parts.length > 0 ? parts : line;
  };

  const quickChips = [
    { label: 'Summarize Dataset', query: 'Generate an executive summary of this dataset.' },
    { label: 'Explain KPIs', query: 'Explain the calculated dashboard KPIs and metrics.' },
    { label: 'Sales Forecast', query: 'Summarize the demand and sales forecast outlook.' },
    { label: 'Customer Clusters', query: 'Explain the customer K-Means segmentation results.' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-sm animate-fade-in">
      {/* Background click overlay */}
      <div className="absolute inset-0 cursor-default" onClick={onClose} />

      {/* Drawer Container */}
      <div className="relative w-full max-w-md h-full bg-slate-900 border-l border-slate-800/80 shadow-2xl flex flex-col z-10">
        
        {/* Header */}
        <div className="px-4 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-cyan-500/10">
              <Bot size={18} className="text-slate-950" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center">
                AI Analytics Assistant
                <Sparkles size={12} className="ml-1 text-cyan-400" />
              </h3>
              <p className="text-[10px] text-slate-500 font-medium">Schema-Aware Interpreter</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Sessions list"
            >
              <MessageSquare size={16} />
            </button>
            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Sessions Sidebar Overlay */}
        {sidebarOpen && (
          <div className="absolute inset-y-0 left-0 w-64 border-r border-slate-800 bg-slate-950/95 z-20 flex flex-col p-4 animate-slide-in">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Chat History</span>
              <button 
                onClick={handleNewSession}
                className="flex items-center space-x-1 px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-[10px] font-bold hover:bg-cyan-500/20 transition-colors"
              >
                <Plus size={10} />
                <span>New Chat</span>
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
              {sessions.map((s) => {
                const isActive = s.session_id === activeSessionId;
                return (
                  <button
                    key={s.session_id}
                    onClick={() => {
                      setActiveSessionId(s.session_id);
                      setSidebarOpen(false);
                    }}
                    className={`
                      w-full text-left px-3 py-2 rounded-lg text-xs truncate flex items-center space-x-2 transition-all
                      ${isActive 
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium' 
                        : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'}
                    `}
                  >
                    <MessageSquare size={12} className={isActive ? 'text-cyan-400' : 'text-slate-500'} />
                    <span className="truncate flex-1">{s.title}</span>
                    <ChevronRight size={10} className="text-slate-600" />
                  </button>
                );
              })}
              {sessions.length === 0 && (
                <p className="text-[10px] text-slate-500 text-center py-8">No chats created yet.</p>
              )}
            </div>
          </div>
        )}

        {/* Messages Pane */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-950/30">
          
          {/* Welcome Message */}
          {messages.length === 0 && !sessionLoading && (
            <div className="py-6 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-800/50 flex items-center justify-center mx-auto border border-slate-800">
                <Bot size={24} className="text-cyan-400" />
              </div>
              <div className="space-y-1 max-w-xs mx-auto">
                <h4 className="text-xs font-bold text-slate-200">Interpret Analytics in Real-Time</h4>
                <p className="text-[10px] text-slate-500 leading-relaxed">
                  Ask questions about active metrics, outlier removals, time-series projections, or user cluster segments. The AI does not compute metrics, eliminating hallucinations.
                </p>
              </div>

              {activeDatasetId && (
                <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[10px] text-slate-400 font-medium">
                  <Database size={10} className="text-cyan-500" />
                  <span>Linked to active dataset</span>
                </div>
              )}
            </div>
          )}

          {sessionLoading ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="animate-spin text-cyan-500" size={24} />
            </div>
          ) : (
            messages.map((msg) => {
              const isAssistant = msg.role === 'assistant';
              return (
                <div 
                  key={msg.message_id} 
                  className={`flex ${isAssistant ? 'justify-start' : 'justify-end'}`}
                >
                  <div className={`
                    max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs shadow-md border
                    ${isAssistant 
                      ? 'bg-slate-900 border-slate-800 text-slate-300 rounded-tl-sm' 
                      : 'bg-gradient-to-br from-cyan-600/90 to-indigo-600/90 border-cyan-500/30 text-white rounded-tr-sm'}
                  `}>
                    {isAssistant ? (
                      <div className="space-y-1">{parseMarkdown(msg.content)}</div>
                    ) : (
                      <p className="leading-relaxed">{msg.content}</p>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Typing Loading State */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-900 border border-slate-800 text-slate-400 max-w-[85%] rounded-2xl rounded-tl-sm px-3.5 py-2.5 flex items-center space-x-2">
                <Loader2 className="animate-spin text-cyan-400" size={14} />
                <span className="text-[10px] font-medium tracking-wide">AI is analyzing results...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick prompt Chips */}
        {messages.length === 0 && !sessionLoading && (
          <div className="px-4 py-2 border-t border-slate-800 bg-slate-900/20">
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block mb-1.5">Suggested Queries</span>
            <div className="grid grid-cols-2 gap-1.5">
              {quickChips.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(chip.query)}
                  className="px-2.5 py-2 text-left rounded-lg bg-slate-800/40 hover:bg-slate-800 border border-slate-800/60 text-[10px] text-slate-300 font-medium truncate transition-all active:scale-95 flex items-center space-x-1"
                >
                  <Sparkles size={8} className="text-cyan-400 shrink-0" />
                  <span className="truncate">{chip.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input box */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/60 flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(input)}
            placeholder="Ask about active analytics results..."
            disabled={loading || sessionLoading}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 disabled:opacity-50"
          />
          <button
            onClick={() => handleSendMessage(input)}
            disabled={loading || sessionLoading || !input.trim()}
            className="p-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 text-slate-950 font-bold hover:shadow-lg hover:shadow-cyan-500/10 active:scale-95 transition-all disabled:opacity-40 disabled:scale-100"
          >
            <Send size={14} />
          </button>
        </div>
        
      </div>
    </div>
  );
};
