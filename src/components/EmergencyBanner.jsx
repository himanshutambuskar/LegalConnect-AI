import React, { useState } from 'react';
import { AlertTriangle, X, PhoneCall } from 'lucide-react';

export default function EmergencyBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="bg-emergency-bg border-b border-emergency-border text-emergency-text text-xs sm:text-sm font-medium py-2 px-4 flex items-center justify-between transition-all">
      <div className="max-w-7xl mx-auto w-full flex flex-wrap items-center justify-center sm:justify-between gap-2 text-center sm:text-left">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-emergency-text shrink-0 animate-pulse" />
          <span className="font-semibold tracking-wide uppercase text-[11px] sm:text-xs">Emergency Helplines</span>
          <span className="hidden md:inline text-emergency-text/60">|</span>
          <span className="text-xs font-sans">Immediate assistance for critical situations</span>
        </div>

        <div className="flex items-center space-x-3 text-xs font-semibold">
          <a href="tel:1930" className="hover:underline flex items-center gap-1 bg-white/70 px-2 py-0.5 rounded border border-emergency-border/50">
            <PhoneCall className="w-3 h-3" /> Cyber Crime: <span className="font-mono font-bold">1930</span>
          </a>
          <a href="tel:181" className="hover:underline flex items-center gap-1 bg-white/70 px-2 py-0.5 rounded border border-emergency-border/50">
            <PhoneCall className="w-3 h-3" /> Women Helpline: <span className="font-mono font-bold">181</span>
          </a>
          <a href="tel:112" className="hidden lg:flex items-center gap-1 bg-white/70 px-2 py-0.5 rounded border border-emergency-border/50">
            National Emergency: <span className="font-mono font-bold">112</span>
          </a>
        </div>

        <button 
          onClick={() => setDismissed(true)} 
          className="text-emergency-text/70 hover:text-emergency-text p-1 rounded hover:bg-emergency-border/30 transition-colors"
          title="Dismiss banner"
          aria-label="Dismiss banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
