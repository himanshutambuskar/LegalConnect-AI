import React from 'react';
import { Link } from 'react-router-dom';
import { Scale } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-100 border-t border-slate-200 mt-auto text-slate-600 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-trust flex items-center justify-center text-white">
              <Scale className="w-4 h-4" />
            </div>
            <span className="font-serif text-xl font-bold text-trust">
              Legal Connect
            </span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-medium text-slate-500">
            <Link to="/about" className="hover:text-trust transition-colors">Legal Disclaimer</Link>
            <span>•</span>
            <Link to="/about" className="hover:text-trust transition-colors">Privacy Policy</Link>
            <span>•</span>
            <Link to="/about" className="hover:text-trust transition-colors">Terms of Service</Link>
            <span>•</span>
            <Link to="/about" className="hover:text-trust transition-colors">Institutional Credits</Link>
          </div>
        </div>

        <div className="text-center text-xs text-slate-500 max-w-3xl mx-auto space-y-1">
          <p>© 2026 Legal Connect. All rights reserved.</p>
          <p className="text-slate-400">
            This AI-powered capstone project provides plain-language legal awareness and educational information, not professional legal advice. Consult a qualified advocate or attorney for court proceedings.
          </p>
        </div>
      </div>
    </footer>
  );
}
