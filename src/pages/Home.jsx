import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Search, 
  ArrowRight, 
  Shield, 
  FileText, 
  ShoppingCart, 
  HeartHandshake, 
  BookOpen, 
  Car,
  ShieldCheck, 
  Languages, 
  ListOrdered 
} from 'lucide-react';
import { CATEGORIES } from '../data/mockResponses';

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/chat?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleChipClick = (phrase) => {
    navigate(`/chat?q=${encodeURIComponent(phrase)}`);
  };

  const getCategoryIcon = (iconName) => {
    switch (iconName) {
      case 'Shield': return <Shield className="w-6 h-6 text-trust" />;
      case 'FileText': return <FileText className="w-6 h-6 text-trust" />;
      case 'ShoppingCart': return <ShoppingCart className="w-6 h-6 text-trust" />;
      case 'HeartHandshake': return <HeartHandshake className="w-6 h-6 text-trust" />;
      case 'BookOpen': return <BookOpen className="w-6 h-6 text-trust" />;
      case 'Car': return <Car className="w-6 h-6 text-trust" />;
      default: return <Shield className="w-6 h-6 text-trust" />;
    }
  };

  const sampleChips = [
    "How do I file an FIR?",
    "Tenant rights eviction",
    "Domestic violence help"
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* HERO SECTION */}
      <section className="pt-12 pb-16 px-4 sm:px-6 lg:px-8 text-center max-w-4xl mx-auto w-full">
        <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.15] mb-4">
          Understand Your Legal Rights, Instantly.
        </h1>
        <p className="text-slate-600 text-lg sm:text-xl max-w-2xl mx-auto font-sans leading-relaxed mb-8">
          Access verified, plain-language legal information to guide your next steps with confidence.
        </p>

        {/* Functional Search Bar */}
        <form onSubmit={handleSearchSubmit} className="max-w-2xl mx-auto mb-6">
          <div className="relative flex items-center bg-white rounded-2xl shadow-sm border border-slate-300 focus-within:border-trust focus-within:ring-2 focus-within:ring-trust/20 transition-all p-2">
            <Search className="w-5 h-5 text-slate-400 ml-3 shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask a legal question..."
              className="w-full px-3 py-2.5 text-slate-800 placeholder-slate-400 bg-transparent focus:outline-none text-base"
            />
            <button
              type="submit"
              className="bg-trust text-white px-5 py-2.5 rounded-xl font-medium text-sm hover:bg-trust-hover transition-colors flex items-center space-x-1 shrink-0"
            >
              <span>Ask</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* 3 Clickable Example Prompt Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto">
          {sampleChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleChipClick(chip)}
              className="bg-white border border-slate-200 text-slate-700 hover:border-trust hover:text-trust text-xs sm:text-sm px-3.5 py-1.5 rounded-full font-medium transition-all shadow-xs hover:shadow-sm"
            >
              {chip}
            </button>
          ))}
        </div>
      </section>

      {/* SIX WAYS WE CAN HELP GRID */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto w-full">
        <div className="text-center mb-10">
          <h2 className="font-serif text-3xl font-bold text-slate-900">
            Six ways we can help
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CATEGORIES.map((cat) => (
            <Link
              key={cat.id}
              to={`/category/${cat.id}`}
              className="bg-white p-6 rounded-2xl border border-slate-200 hover:border-trust/40 hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div>
                <div className="w-12 h-12 rounded-xl bg-trust-light/70 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  {getCategoryIcon(cat.iconName)}
                </div>
                <h3 className="font-serif text-xl font-bold text-slate-900 group-hover:text-trust transition-colors mb-2">
                  {cat.name}
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed mb-4">
                  {cat.tagline || cat.description}
                </p>
              </div>

              <div className="flex items-center text-trust text-sm font-semibold pt-2 group-hover:translate-x-1 transition-transform">
                <span>Explore category</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* WHY LEGAL CONNECT (3-COLUMN FEATURE BLOCK) */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white border-t border-b border-slate-200 mt-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {/* Feature 1 */}
            <div className="p-4 space-y-3">
              <div className="w-12 h-12 rounded-full bg-trust-light text-trust flex items-center justify-center mx-auto mb-2">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="font-serif text-xl font-bold text-slate-900">
                Grounded in Verified Sources
              </h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Information curated directly from official government databases, updated legal codes, and statutory frameworks.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-4 space-y-3">
              <div className="w-12 h-12 rounded-full bg-trust-light text-trust flex items-center justify-center mx-auto mb-2">
                <Languages className="w-6 h-6" />
              </div>
              <h3 className="font-serif text-xl font-bold text-slate-900">
                Plain-Language Answers
              </h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Complex legal jargon simplified into clear, digestible guidance for immediate citizen comprehension.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-4 space-y-3">
              <div className="w-12 h-12 rounded-full bg-trust-light text-trust flex items-center justify-center mx-auto mb-2">
                <ListOrdered className="w-6 h-6" />
              </div>
              <h3 className="font-serif text-xl font-bold text-slate-900">
                Step-by-Step Guidance
              </h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Clear, actionable steps on how to proceed with legal filings, police complaints, and grievance portals.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
