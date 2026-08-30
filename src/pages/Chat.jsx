import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Send, 
  Paperclip, 
  Mic, 
  Shield, 
  FileText, 
  ShoppingCart, 
  HeartHandshake, 
  BookOpen, 
  Car, 
  Sparkles, 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  Check, 
  ExternalLink,
  BookMarked
} from 'lucide-react';
import { CATEGORIES, MOCK_RESPONSES, DEFAULT_FALLBACK_RESPONSE } from '../data/mockResponses';
import DisclaimerStrip from '../components/DisclaimerStrip';
import SourceDrawer from '../components/SourceDrawer';

export default function Chat() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const categoryParam = searchParams.get('category');
  const queryParam = searchParams.get('q');

  const [activeCategory, setActiveCategory] = useState(categoryParam || null);
  const [inputQuery, setInputQuery] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [likedMap, setLikedMap] = useState({});

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isAnalyzing]);

  // Handle URL search parameters on mount
  useEffect(() => {
    if (categoryParam) {
      setActiveCategory(categoryParam);
    }

    if (queryParam) {
      handleInitialQuery(queryParam, categoryParam);
    } else if (chatHistory.length === 0) {
      // Seed initial sample interaction if chat is empty
      const initialCat = categoryParam || 'cybercrime';
      const sampleResponse = MOCK_RESPONSES.find(r => r.category === initialCat) || MOCK_RESPONSES[0];
      setChatHistory([
        {
          id: 'user-init',
          sender: 'user',
          text: sampleResponse.question,
          time: 'Today, 10:42 AM'
        },
        {
          id: 'ai-init',
          sender: 'ai',
          data: sampleResponse,
          time: 'Today, 10:42 AM'
        }
      ]);
    }
  }, [queryParam, categoryParam]);

  const handleInitialQuery = (queryText, categoryFilter) => {
    const matched = findMatchingResponse(queryText, categoryFilter);
    setChatHistory([
      {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: queryText,
        time: getCurrentTime()
      },
      {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        data: matched,
        time: getCurrentTime()
      }
    ]);
  };

  const getCurrentTime = () => {
    const now = new Date();
    return `Today, ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  const findMatchingResponse = (query, categoryFilter) => {
    const lowerQuery = query.toLowerCase();
    
    // Filter by category if sidebar category is selected
    let candidates = MOCK_RESPONSES;
    if (categoryFilter) {
      candidates = candidates.filter(r => r.category === categoryFilter);
    }

    // Try matching trigger phrases
    for (const item of candidates) {
      if (item.triggerPhrases.some(phrase => lowerQuery.includes(phrase.toLowerCase()))) {
        return item;
      }
    }

    // Try fuzzy word overlap in question or summary
    for (const item of candidates) {
      const qWords = item.question.toLowerCase().split(' ');
      const matchingWords = qWords.filter(w => w.length > 3 && lowerQuery.includes(w));
      if (matchingWords.length >= 2) {
        return item;
      }
    }

    // Return category default or overall fallback
    if (categoryFilter) {
      const catMatch = MOCK_RESPONSES.find(r => r.category === categoryFilter);
      if (catMatch) return catMatch;
    }

    return {
      ...DEFAULT_FALLBACK_RESPONSE,
      question: query
    };
  };

  const handleSendMessage = (e) => {
    e?.preventDefault();
    if (!inputQuery.trim() || isAnalyzing) return;

    const userText = inputQuery.trim();
    setInputQuery('');

    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userText,
      time: getCurrentTime()
    };

    setChatHistory(prev => [...prev, userMsg]);
    setIsAnalyzing(true);

    // Simulate AI response delay (~800ms)
    setTimeout(() => {
      const matched = findMatchingResponse(userText, activeCategory);
      const aiMsg = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        data: matched,
        time: getCurrentTime()
      };
      setChatHistory(prev => [...prev, aiMsg]);
      setIsAnalyzing(false);
    }, 850);
  };

  const handleFollowupClick = (chipText) => {
    setInputQuery(chipText);
  };

  const handleNewChat = () => {
    setChatHistory([]);
    setActiveCategory(null);
    setSearchParams({});
    // Seed default sample
    const sample = MOCK_RESPONSES[0];
    setChatHistory([
      {
        id: 'user-new',
        sender: 'user',
        text: "What are my rights if my banking OTP is intercepted?",
        time: getCurrentTime()
      },
      {
        id: 'ai-new',
        sender: 'ai',
        data: sample,
        time: getCurrentTime()
      }
    ]);
  };

  const handleCategorySelect = (catId) => {
    const newCat = activeCategory === catId ? null : catId;
    setActiveCategory(newCat);
    if (newCat) {
      setSearchParams({ category: newCat });
    } else {
      setSearchParams({});
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleLike = (id, type) => {
    setLikedMap(prev => ({
      ...prev,
      [id]: prev[id] === type ? null : type
    }));
  };

  const getSidebarIcon = (iconName) => {
    switch (iconName) {
      case 'Shield': return <Shield className="w-4 h-4" />;
      case 'FileText': return <FileText className="w-4 h-4" />;
      case 'ShoppingCart': return <ShoppingCart className="w-4 h-4" />;
      case 'HeartHandshake': return <HeartHandshake className="w-4 h-4" />;
      case 'BookOpen': return <BookOpen className="w-4 h-4" />;
      case 'Car': return <Car className="w-4 h-4" />;
      default: return <Shield className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-slate-50 overflow-hidden">
      {/* Persistent Disclaimer Banner */}
      <DisclaimerStrip />

      <div className="flex-1 flex overflow-hidden">
        {/* LEFT SIDEBAR */}
        <aside className="w-64 bg-slate-100/90 border-r border-slate-200 flex flex-col p-4 shrink-0 hidden md:flex">
          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center space-x-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 py-2.5 px-4 rounded-xl font-medium text-sm transition-all shadow-2xs hover:shadow-xs mb-6"
          >
            <Plus className="w-4 h-4 text-trust" />
            <span>New Chat</span>
          </button>

          {/* Categories List Header */}
          <div className="px-2 mb-3">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Filter by Category
            </span>
          </div>

          {/* 6 Category Items */}
          <div className="space-y-1 flex-1 overflow-y-auto pr-1">
            {CATEGORIES.map((cat) => {
              const active = activeCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => handleCategorySelect(cat.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all text-left ${
                    active
                      ? 'bg-trust text-white shadow-xs font-semibold'
                      : 'text-slate-700 hover:bg-slate-200/70'
                  }`}
                >
                  <span className={active ? 'text-white' : 'text-slate-500'}>
                    {getSidebarIcon(cat.iconName)}
                  </span>
                  <span className="truncate">{cat.name}</span>
                </button>
              );
            })}
          </div>

          {/* Category Scope Indicator */}
          {activeCategory && (
            <div className="mt-4 p-3 bg-trust-light/60 border border-trust-tint/60 rounded-xl text-xs text-trust space-y-1">
              <div className="font-semibold flex items-center justify-between">
                <span>Active Scope:</span>
                <button onClick={() => handleCategorySelect(activeCategory)} className="text-[10px] underline">Clear</button>
              </div>
              <p className="truncate font-medium capitalize">{activeCategory.replace('-', ' ')}</p>
            </div>
          )}
        </aside>

        {/* MAIN CHAT AREA (Centered 720px column) */}
        <main className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
          {/* Scrollable Conversation Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
            <div className="max-w-[720px] mx-auto space-y-6">
              
              {/* Date Header Pill */}
              <div className="text-center my-4">
                <span className="inline-block bg-slate-200/70 text-slate-600 text-[11px] font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
                  Today, 10:42 AM
                </span>
              </div>

              {/* Chat Message Trajectory */}
              {chatHistory.map((item) => {
                if (item.sender === 'user') {
                  return (
                    <div key={item.id} className="flex justify-end">
                      <div className="bg-trust text-white font-sans text-sm sm:text-base leading-relaxed px-5 py-3.5 rounded-2xl rounded-tr-xs max-w-[85%] shadow-sm">
                        {item.text}
                      </div>
                    </div>
                  );
                }

                // AI Response Card
                const res = item.data;
                return (
                  <div key={item.id} className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-sm space-y-5 transition-all">
                    {/* Card Header Badge */}
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div className="flex items-center space-x-2 text-trust text-xs sm:text-sm font-semibold">
                        <Sparkles className="w-4 h-4 fill-trust/20 text-trust" />
                        <span>Legal Connect AI</span>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">Grounded Answer</span>
                    </div>

                    {/* Summary Heading & Overview */}
                    <div>
                      <h3 className="font-serif text-xl sm:text-2xl font-bold text-slate-900 leading-snug mb-2">
                        {res.summary}
                      </h3>
                      <p className="text-slate-700 text-sm sm:text-base leading-relaxed">
                        {res.summaryText}
                      </p>
                    </div>

                    {/* Numbered Recommended Steps */}
                    {res.steps && res.steps.length > 0 && (
                      <div className="space-y-3 pt-2">
                        <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                          <BookMarked className="w-3.5 h-3.5 text-trust" />
                          <span>Recommended Steps</span>
                        </div>
                        <div className="space-y-2.5">
                          {res.steps.map((step, idx) => (
                            <div key={idx} className="flex items-start space-x-3 bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                              <span className="w-6 h-6 rounded-full bg-trust-light text-trust font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                                {idx + 1}
                              </span>
                              <div className="text-xs sm:text-sm">
                                <span className="font-semibold text-slate-900">{step.title}: </span>
                                <span className="text-slate-600 leading-relaxed">{step.detail}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Sources Referenced Row */}
                    {res.sources && res.sources.length > 0 && (
                      <div className="pt-2 border-t border-slate-100 space-y-2">
                        <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider">
                          SOURCES REFERENCED
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {res.sources.map((src, idx) => (
                            <button
                              key={idx}
                              onClick={() => setSelectedSource(src)}
                              className="inline-flex items-center space-x-1.5 bg-trust-light/80 hover:bg-trust-light border border-trust-tint/80 text-trust text-xs font-medium px-3 py-1.5 rounded-lg transition-colors text-left"
                            >
                              <Shield className="w-3.5 h-3.5 text-trust" />
                              <span className="truncate max-w-[240px]">{src.name}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions & Feedback */}
                    <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-slate-400 text-xs">
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => toggleLike(item.id, 'up')}
                          className={`p-1.5 rounded-md hover:bg-slate-100 transition-colors ${
                            likedMap[item.id] === 'up' ? 'text-trust bg-trust-light' : ''
                          }`}
                          title="Helpful"
                        >
                          <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => toggleLike(item.id, 'down')}
                          className={`p-1.5 rounded-md hover:bg-slate-100 transition-colors ${
                            likedMap[item.id] === 'down' ? 'text-emergency-text bg-emergency-bg' : ''
                          }`}
                          title="Not helpful"
                        >
                          <ThumbsDown className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => copyToClipboard(`${res.summary}\n\n${res.summaryText}`, item.id)}
                          className="p-1.5 rounded-md hover:bg-slate-100 transition-colors flex items-center space-x-1"
                          title="Copy response"
                        >
                          {copiedId === item.id ? (
                            <Check className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      <span className="text-[11px] text-slate-400 font-sans">Verified Indian Legal Code</span>
                    </div>

                    {/* Suggested Follow-up Chips */}
                    {res.suggestedFollowups && (
                      <div className="pt-2 space-y-1.5">
                        <span className="text-[11px] font-medium text-slate-400">Suggested follow-ups:</span>
                        <div className="flex flex-wrap gap-2">
                          {res.suggestedFollowups.map((chip, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() => handleFollowupClick(chip)}
                              className="text-xs bg-slate-100 hover:bg-trust-light hover:text-trust text-slate-700 px-3 py-1.5 rounded-full font-medium transition-colors border border-slate-200/70"
                            >
                              {chip}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Status Indicator "Analyzing..." */}
              {isAnalyzing && (
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex items-center space-x-3 text-trust animate-pulse">
                  <div className="w-4 h-4 border-2 border-trust border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm font-medium">Analyzing legal sources & Indian statutes...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Sticky Bottom Input Column (Centered 720px) */}
          <div className="p-4 sm:p-6 bg-white border-t border-slate-200/80">
            <div className="max-w-[720px] mx-auto space-y-2">
              <form onSubmit={handleSendMessage} className="relative flex items-center bg-slate-50 border border-slate-300 rounded-2xl p-2 focus-within:border-trust focus-within:ring-2 focus-within:ring-trust/20 transition-all shadow-xs">
                <button
                  type="button"
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-200/50 transition-colors"
                  title="Attach document (demo)"
                >
                  <Paperclip className="w-4 h-4" />
                </button>

                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask a follow-up question..."
                  className="w-full px-3 py-2 text-slate-800 placeholder-slate-400 bg-transparent focus:outline-none text-sm sm:text-base"
                />

                <button
                  type="button"
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-200/50 transition-colors mr-1"
                  title="Voice input (demo)"
                >
                  <Mic className="w-4 h-4" />
                </button>

                <button
                  type="submit"
                  disabled={!inputQuery.trim() || isAnalyzing}
                  className="bg-trust text-white p-2.5 rounded-xl hover:bg-trust-hover active:bg-trust-dark disabled:opacity-40 transition-all shadow-xs shrink-0"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>

              <p className="text-center text-[11px] text-slate-400">
                AI can make mistakes. Verify important information with legal professionals.
              </p>
            </div>
          </div>
        </main>
      </div>

      {/* Citation Slide-in Drawer */}
      <SourceDrawer source={selectedSource} onClose={() => setSelectedSource(null)} />
    </div>
  );
}
