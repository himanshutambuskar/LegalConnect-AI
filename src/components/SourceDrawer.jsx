import React from 'react';
import { X, ExternalLink, BookOpen, ShieldCheck } from 'lucide-react';

export default function SourceDrawer({ source, onClose }) {
  if (!source) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end transition-opacity">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out border-l border-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-trust-light text-trust flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-serif text-lg font-bold text-slate-900">Verified Source Citation</h3>
              <p className="text-xs text-slate-500">Official legal statute / reference</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          <div>
            <span className="inline-block px-2.5 py-1 rounded-md text-xs font-semibold bg-trust-light text-trust mb-2">
              Official Reference
            </span>
            <h4 className="text-xl font-bold font-serif text-slate-900 leading-snug">
              {source.name}
            </h4>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <BookOpen className="w-3.5 h-3.5 text-trust" />
              <span>Statutory Excerpt / Provisions</span>
            </div>
            <p className="text-sm text-slate-700 italic leading-relaxed border-l-2 border-trust pl-3 py-1">
              "{source.excerpt}"
            </p>
          </div>

          <div className="space-y-3">
            <h5 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Verification Details</h5>
            <div className="text-sm text-slate-600 space-y-2 bg-white p-3 rounded-lg border border-slate-200 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Source Credibility</span>
                <span className="font-semibold text-emerald-700 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Verified Official
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Jurisdiction</span>
                <span className="font-semibold text-slate-800">Republic of India</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Access Type</span>
                <span className="font-semibold text-slate-800">Public Domain / Statutory</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Link */}
        <div className="p-5 border-t border-slate-200 bg-slate-50">
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full inline-flex items-center justify-center space-x-2 bg-trust text-white px-4 py-3 rounded-xl font-medium text-sm hover:bg-trust-hover transition-all shadow-sm"
          >
            <span>Open Official Document / Portal</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
