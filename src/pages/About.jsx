import React from 'react';
import { 
  Scale, 
  HelpCircle, 
  Database, 
  ShieldCheck, 
  GraduationCap, 
  Users, 
  Award,
  Building2
} from 'lucide-react';

export default function About() {
  const teamMembers = [
    { name: 'Diya Arjnani', role: 'BTech Student Developer', area: 'NLP & Knowledge Retrieval' },
    { name: 'Ronit Gandhi', role: 'BTech Student Developer', area: 'Full Stack & Data Engineering' },
    { name: 'Himanshu Tambuskar', role: 'BTech Student Developer', area: 'UI/UX Architecture & AI Integration' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto w-full space-y-16">
        
        {/* HERO MISSION STATEMENT */}
        <section className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center space-x-2 bg-trust-light text-trust px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
            <Scale className="w-4 h-4" />
            <span>BTech Capstone Project</span>
          </div>
          <h1 className="font-serif text-4xl sm:text-5xl font-bold text-slate-900 leading-tight">
            Democratizing Legal Awareness for Every Indian Citizen
          </h1>
          <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
            Legal Connect is an AI-powered legal awareness platform designed to simplify complex Indian statutes, constitutional rights, and procedural codes into instant, plain-language guidance.
          </p>
        </section>

        {/* HOW IT WORKS (3-STEP ICON FLOW) */}
        <section className="space-y-8 bg-white p-8 sm:p-10 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="text-center max-w-xl mx-auto space-y-2">
            <h2 className="font-serif text-3xl font-bold text-slate-900">
              How Legal Connect Works
            </h2>
            <p className="text-slate-500 text-sm">
              Our 3-step retrieval system ensures accurate, grounded answers without legal hallucination.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-4 relative">
            {/* Step 1 */}
            <div className="text-center space-y-3 p-4">
              <div className="w-14 h-14 rounded-2xl bg-trust-light text-trust flex items-center justify-center mx-auto shadow-xs">
                <HelpCircle className="w-7 h-7" />
              </div>
              <span className="inline-block text-xs font-bold font-mono text-trust uppercase">Step 1: Ask</span>
              <h3 className="font-serif text-xl font-bold text-slate-900">Citizen Query</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                The user inputs a legal query in plain everyday language regarding fraud, police rights, or consumer disputes.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center space-y-3 p-4">
              <div className="w-14 h-14 rounded-2xl bg-trust-light text-trust flex items-center justify-center mx-auto shadow-xs">
                <Database className="w-7 h-7" />
              </div>
              <span className="inline-block text-xs font-bold font-mono text-trust uppercase">Step 2: Retrieve</span>
              <h3 className="font-serif text-xl font-bold text-slate-900">Statutory Retrieval</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                The AI system searches official Indian legal repositories including IT Act, BNSS, CPA 2019, and Supreme Court rulings.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center space-y-3 p-4">
              <div className="w-14 h-14 rounded-2xl bg-trust-light text-trust flex items-center justify-center mx-auto shadow-xs">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <span className="inline-block text-xs font-bold font-mono text-trust uppercase">Step 3: Answer</span>
              <h3 className="font-serif text-xl font-bold text-slate-900">Grounded Answer</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Renders a structured response with summary, numbered procedural steps, and verified source citations.
              </p>
            </div>
          </div>
        </section>

        {/* TEAM & GUIDE CARDS */}
        <section className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="font-serif text-3xl font-bold text-slate-900">
              Project Authors & Mentorship
            </h2>
            <p className="text-slate-500 text-sm">
              Developed as a BTech Major Capstone Project at SVKM's NMIMS Shirpur.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {teamMembers.map((member, idx) => (
              <div key={idx} className="bg-white p-6 rounded-2xl border border-slate-200 text-center space-y-3 shadow-2xs hover:border-trust/40 transition-colors">
                <div className="w-16 h-16 rounded-full bg-slate-100 text-trust font-serif font-bold text-xl flex items-center justify-center mx-auto border border-slate-200">
                  {member.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <h3 className="font-serif text-xl font-bold text-slate-900">{member.name}</h3>
                  <p className="text-xs font-semibold text-trust">{member.role}</p>
                </div>
                <p className="text-xs text-slate-500 bg-slate-50 py-1.5 px-3 rounded-lg border border-slate-100">
                  Focus: {member.area}
                </p>
              </div>
            ))}
          </div>

          {/* Guide Card */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-trust-tint bg-gradient-to-r from-trust-light/40 to-white max-w-2xl mx-auto text-center space-y-3 shadow-2xs">
            <div className="w-12 h-12 rounded-full bg-trust text-white flex items-center justify-center mx-auto">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-trust">Project Faculty Guide</span>
              <h3 className="font-serif text-2xl font-bold text-slate-900 mt-1">Prof. Piyush Kumar Soni</h3>
              <p className="text-xs font-medium text-slate-600">Department of Information Technology</p>
            </div>
          </div>
        </section>

        {/* INSTITUTION CREDIT STRIP */}
        <section className="bg-slate-900 text-white rounded-2xl p-8 text-center space-y-3 shadow-md">
          <Building2 className="w-8 h-8 text-trust-light mx-auto" />
          <h3 className="font-serif text-2xl font-bold">Mukesh Patel School of Technology Management & Engineering (MPSTME)</h3>
          <p className="text-slate-300 text-sm">
            SVKM's NMIMS University, Shirpur Campus
          </p>
          <p className="text-xs font-mono text-trust-light/70 pt-2">
            Academic Year 2026–2027 • BTech Capstone Project
          </p>
        </section>

      </div>
    </div>
  );
}
