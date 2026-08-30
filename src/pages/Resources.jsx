import React, { useState } from 'react';
import { 
  AlertTriangle, 
  ExternalLink, 
  ChevronDown, 
  Shield, 
  FileText, 
  ShoppingCart, 
  HeartHandshake, 
  BookOpen, 
  Car,
  Globe
} from 'lucide-react';
import { CATEGORIES } from '../data/mockResponses';

export default function Resources() {
  const [openSections, setOpenSections] = useState({
    cybercrime: true,
    'fir-police': true,
    'consumer-rights': false,
    'womens-safety': false,
    'constitutional-rights': false,
    'traffic-rules': false
  });

  const toggleSection = (id) => {
    setOpenSections(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const getIcon = (iconName) => {
    switch (iconName) {
      case 'Shield': return <Shield className="w-5 h-5 text-trust" />;
      case 'FileText': return <FileText className="w-5 h-5 text-trust" />;
      case 'ShoppingCart': return <ShoppingCart className="w-5 h-5 text-trust" />;
      case 'HeartHandshake': return <HeartHandshake className="w-5 h-5 text-trust" />;
      case 'BookOpen': return <BookOpen className="w-5 h-5 text-trust" />;
      case 'Car': return <Car className="w-5 h-5 text-trust" />;
      default: return <Shield className="w-5 h-5 text-trust" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto w-full space-y-10">
        
        {/* PINNED EMERGENCY CONTACTS CARD (Image 4 Error Container Styling) */}
        <div className="bg-emergency-bg border border-emergency-border/60 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xs">
          <div className="space-y-1 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start space-x-2 text-emergency-text font-serif text-2xl font-bold">
              <AlertTriangle className="w-6 h-6 shrink-0" />
              <h2>Emergency Contacts</h2>
            </div>
            <p className="text-emergency-text/80 text-sm font-sans">
              Immediate assistance helplines for critical situations.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 w-full md:w-auto">
            {/* Box 1 */}
            <div className="bg-white/80 border border-emergency-border/40 p-3 rounded-xl text-center min-w-[100px]">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-emergency-text/70">
                Women in Distress
              </span>
              <span className="font-serif text-2xl sm:text-3xl font-bold text-emergency-text">
                181
              </span>
            </div>

            {/* Box 2 */}
            <div className="bg-white/80 border border-emergency-border/40 p-3 rounded-xl text-center min-w-[100px]">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-emergency-text/70">
                Cyber Crime
              </span>
              <span className="font-serif text-2xl sm:text-3xl font-bold text-emergency-text">
                1930
              </span>
            </div>

            {/* Box 3 */}
            <div className="bg-white/80 border border-emergency-border/40 p-3 rounded-xl text-center min-w-[100px]">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-emergency-text/70">
                Consumer Helpline
              </span>
              <span className="font-serif text-2xl sm:text-3xl font-bold text-emergency-text">
                1915
              </span>
            </div>
          </div>
        </div>

        {/* VERIFIED RESOURCES HEADING */}
        <div className="space-y-2">
          <h1 className="font-serif text-4xl sm:text-5xl font-bold text-slate-900">
            Verified Resources
          </h1>
          <p className="text-slate-600 text-base sm:text-lg max-w-3xl leading-relaxed">
            A curated directory of official legal resources, statutory portals, and trusted advisory bodies for comprehensive legal research.
          </p>
        </div>

        {/* 6 COLLAPSIBLE CATEGORY RESOURCE SECTIONS */}
        <div className="space-y-4">
          {CATEGORIES.map((cat) => {
            const isOpen = openSections[cat.id];
            return (
              <div
                key={cat.id}
                className="bg-white rounded-2xl border border-slate-200 overflow-hidden transition-all shadow-2xs"
              >
                {/* Header Toggle */}
                <button
                  onClick={() => toggleSection(cat.id)}
                  className="w-full p-5 text-left flex items-center justify-between font-serif text-lg font-bold text-slate-900 hover:text-trust transition-colors bg-white hover:bg-slate-50/50"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-trust-light flex items-center justify-center">
                      {getIcon(cat.iconName)}
                    </div>
                    <span>{cat.name} Directory</span>
                  </div>
                  <ChevronDown
                    className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${
                      isOpen ? 'transform rotate-180 text-trust' : ''
                    }`}
                  />
                </button>

                {/* Collapsible Content */}
                {isOpen && (
                  <div className="p-5 border-t border-slate-100 bg-slate-50/50 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {cat.verifiedResources.map((res, rIdx) => (
                        <div
                          key={rIdx}
                          className="bg-white p-4 rounded-xl border border-slate-200 flex flex-col justify-between space-y-3 hover:border-trust/40 transition-colors"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <h4 className="font-bold text-slate-900 text-sm">
                                {res.title}
                              </h4>
                              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-trust-light text-trust">
                                {res.type || 'Official'}
                              </span>
                            </div>
                            <p className="text-xs text-slate-600 leading-relaxed">
                              {res.desc}
                            </p>
                          </div>

                          <div className="pt-2 border-t border-slate-100 flex justify-end">
                            <a
                              href={res.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center space-x-1.5 bg-trust text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-trust-hover transition-colors"
                            >
                              <span>Open Portal</span>
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
