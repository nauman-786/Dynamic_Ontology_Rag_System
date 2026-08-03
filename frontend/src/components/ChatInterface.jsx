import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ChevronDown, ChevronRight, Sparkles, Maximize2, Minimize2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// 🎨 Custom Markdown Renderer with Premium UI/UX Effects
const CustomMarkdown = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // Gradient Headings
        h1: ({ node, ...props }) => <h1 className="text-xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600 mt-5 mb-2.5 tracking-tight" {...props} />,
        h2: ({ node, ...props }) => <h2 className="text-lg font-bold text-slate-800 mt-4 mb-2 tracking-tight" {...props} />,
        h3: ({ node, ...props }) => <h3 className="text-base font-semibold text-slate-700 mt-3 mb-1.5" {...props} />,
        
        // Highly readable paragraphs
        p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-loose text-slate-700" {...props} />,
        
        // Beautiful links
        a: ({ node, ...props }) => <a className="text-indigo-600 font-medium hover:text-indigo-800 underline decoration-indigo-200 hover:decoration-indigo-500 underline-offset-4 transition-all" {...props} />,
        
        // Custom colored list markers
        ul: ({ node, ...props }) => <ul className="list-disc list-outside ml-5 space-y-1.5 my-3 text-slate-700 marker:text-indigo-500" {...props} />,
        ol: ({ node, ...props }) => <ol className="list-decimal list-outside ml-5 space-y-1.5 my-3 text-slate-700 marker:text-indigo-500 font-medium" {...props} />,
        li: ({ node, ...props }) => <li className="pl-1 leading-relaxed" {...props} />,
        
        strong: ({ node, ...props }) => <strong className="font-semibold text-slate-900" {...props} />,
        em: ({ node, ...props }) => <em className="italic text-slate-600" {...props} />,
        
        // Sleek blockquotes
        blockquote: ({ node, ...props }) => (
          <blockquote className="border-l-4 border-indigo-500 pl-4 py-1.5 my-4 italic text-slate-600 bg-indigo-50/50 rounded-r-xl shadow-sm" {...props} />
        ),
        
        // Premium Code Blocks (Mac-style window)
        code({ node, inline, className, children, ...props }) {
          if (inline) {
            return (
              <code className="bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded-md text-[13px] font-mono border border-indigo-100/50" {...props}>
                {children}
              </code>
            );
          }
          return (
            <div className="my-4 overflow-hidden rounded-xl border border-slate-700/50 bg-[#0f172a] shadow-xl shadow-slate-900/20">
              {/* Mac-style Window header */}
              <div className="flex items-center px-4 py-2.5 bg-slate-800/50 border-b border-slate-700/50 gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500/80"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></div>
              </div>
              <pre className="p-4 text-[13px] font-mono text-slate-200 overflow-x-auto leading-relaxed" {...props}>
                <code>{children}</code>
              </pre>
            </div>
          );
        },
        
        // Modern SaaS Tables
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto my-4 rounded-xl border border-slate-200 shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-sm text-left" {...props} />
          </div>
        ),
        thead: ({ node, ...props }) => <thead className="bg-slate-50/80 backdrop-blur-sm font-semibold text-slate-800" {...props} />,
        tbody: ({ node, ...props }) => <tbody className="divide-y divide-slate-100 bg-white" {...props} />,
        th: ({ node, ...props }) => <th className="px-4 py-3 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider text-xs" {...props} />,
        td: ({ node, ...props }) => <td className="px-4 py-3 text-slate-600 leading-relaxed" {...props} />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

const ChatInterface = ({ layoutMode, setLayoutMode }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleExpand = () => {
    setLayoutMode(layoutMode === 'chat' ? 'split' : 'chat');
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userQuery = input.trim();
    setInput('');

    // 🟢 Extract STRICTLY the last 5 messages for conversation memory
    const recentHistory = messages
      .filter((m) => m.content) // Exclude empty streaming placeholders
      .slice(-5)               
      .map((m) => ({
        role: m.role,
        content: m.content,
      }));

    const userMsg = { id: Date.now(), role: 'user', content: userQuery };
    const assistantMsg = { id: Date.now() + 1, role: 'assistant', content: '', context: '' };
    
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: userQuery,
          history: recentHistory // Send only the 5 most recent messages
        }),
      });

      if (!response.body) throw new Error('ReadableStream not supported.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const rawJson = line.replace('data: ', '').trim();
            if (!rawJson) continue;

            try {
              const parsed = JSON.parse(rawJson);

              if (parsed.type === 'context') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsg.id ? { ...msg, context: parsed.content } : msg
                  )
                );
              } else if (parsed.type === 'chunk') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsg.id
                      ? { ...msg, content: msg.content + parsed.content }
                      : msg
                  )
                );
              }
            } catch (err) {}
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsg.id
            ? { ...msg, content: '❌ Error: Failed to generate response from server.' }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 relative">
      {/* Header */}
      <div className="h-14 bg-white border-b border-slate-200/60 flex items-center justify-between px-6 shrink-0 shadow-sm z-10">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
            <Sparkles size={16} />
          </div>
          <span className="font-bold text-slate-800 text-sm tracking-wide">GraphRAG Assistant</span>
        </div>
        <button 
          onClick={toggleExpand}
          className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
          title={layoutMode === 'chat' ? "Restore Split View" : "Maximize Chat"}
        >
          {layoutMode === 'chat' ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>
      </div>

      {/* Chat Area */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-8 bg-gradient-to-b from-slate-50 to-white scroll-smooth">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 max-w-md mx-auto space-y-4 animate-in fade-in duration-700">
            <div className="p-4 bg-white shadow-xl shadow-indigo-100/50 text-indigo-600 rounded-2xl ring-1 ring-slate-100">
              <Bot size={32} />
            </div>
            <div className="space-y-1">
              <h2 className="text-slate-800 font-bold text-lg">Hello there!</h2>
              <p className="text-sm text-slate-500">Ask me anything about your knowledge graph or documents.</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageItem key={msg.id} msg={msg} />
          ))
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-200/60 shrink-0 shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.05)]">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto relative flex items-center group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isStreaming}
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 rounded-2xl py-4 pl-5 pr-14 text-[15px] focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-400 focus:bg-white transition-all shadow-sm group-hover:shadow-md"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="absolute right-2.5 p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl transition-all shadow-md shadow-indigo-200 disabled:shadow-none hover:-translate-y-0.5 active:translate-y-0"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

const MessageItem = ({ msg }) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = msg.role === 'user';

  return (
    <div className={`flex gap-4 max-w-4xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'} w-full animate-in fade-in slide-in-from-bottom-2 duration-300 ease-out`}>
      
      {/* Avatar */}
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
        isUser 
          ? 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-indigo-200' 
          : 'bg-white text-indigo-600 border border-slate-200 ring-4 ring-white'
      }`}>
        {isUser ? <User size={18} /> : <Bot size={20} />}
      </div>
      
      {/* Message Content */}
      <div className="space-y-2 flex-1 max-w-[85%]">
        <div className={`p-5 rounded-2xl text-[15px] shadow-sm ${
          isUser 
            ? 'bg-gradient-to-br from-indigo-600 to-violet-600 text-white rounded-tr-sm shadow-indigo-200 font-medium' 
            : 'bg-white border border-slate-100 text-slate-800 rounded-tl-sm ring-1 ring-slate-900/5'
        }`}>
          {isUser ? (
            msg.content
          ) : msg.content ? (
            <CustomMarkdown content={msg.content} />
          ) : (
            /* Beautiful Animated Shimmering Text for Loading State */
            <div className="flex items-center gap-2">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-slate-400 via-indigo-500 to-slate-400 bg-[length:200%_auto] animate-[pulse_2s_cubic-bezier(0.4,0,0.6,1)_infinite] font-medium tracking-wide">
                Synthesizing answer...
              </span>
            </div>
          )}
        </div>
        
        {/* Sleek Source Context Dropdown */}
        {!isUser && msg.context && (
          <div className="border border-slate-200/80 rounded-xl overflow-hidden bg-slate-50/50 text-xs shadow-sm transition-all duration-300">
            <button
              onClick={() => setShowSources(!showSources)}
              className="w-full px-4 py-2.5 flex items-center justify-between text-slate-600 hover:text-indigo-600 hover:bg-indigo-50/50 transition-colors"
            >
              <span className="font-semibold flex items-center gap-2 tracking-wide">
                <Sparkles size={13} className="text-indigo-500" />
                View Retrieved Knowledge Sources
              </span>
              {showSources ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
            
            {showSources && (
              <div className="p-4 bg-slate-900 text-slate-300 font-mono text-[11px] leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap border-t border-slate-200 shadow-inner">
                {msg.context}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;