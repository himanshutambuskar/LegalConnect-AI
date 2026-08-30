import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ChevronDown, 
  ExternalLink, 
  MessageSquare, 
  PhoneCall, 
  FileText, 
  Globe, 
  Shield, 
  CheckCircle2, 
  ArrowLeft 
} from 'lucide-react';
import { CATEGORIES, MOCK_FAQS } from '../data/mockResponses';

export default function CategoryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [openFaqIndex, setOpenFaqIndex] = useState(0);

  const category = CATEGORIES.find((c) => c.id === id) || CATEGORIES[0];
  const faqs = MOCK_FAQS[category.id] || MOCK_FAQS.cybercrime;

  const toggleFaq = (index) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  const handleAskCategory = () => {
    navigate(`/chat?category=${category.id}`);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col pb-24">
      {/* TRUST BLUE HEADER BAND */}
      <section className="bg-trust text-white py-12 px-4 sm:px-6 lg:px-8 shadow-sm">
        <div className="max-w-6xl mx-auto space-y-4">
          <Link to="/" className="inline-flex items-center space-x-1.5 text-xs text-trust-light/80 hover:text-white transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>

          <h1 className="font-serif text-4xl sm:text-5xl font-bold tracking-tight">
            {category.name}
          </h1>
          <p className="text-trust-light text-base sm:text-lg max-w-3xl leading-relaxed font-sans">
            {category.description}
          </p>
        </div>
      </section>

      {/* MAIN TWO-COLUMN CONTENT LAYOUT */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT COLUMN (2/3 Width) */}
          <div className="lg:col-span-2 space-y-10">
            
            {/* FAQ Accordion Section */}
            <section className="space-y-4">
              <h2 className="font-serif text-2xl font-bold text-slate-900">
                Common Questions
              </h2>

              <div className="space-y-3">
                {faqs.map((faq, index) => {
                  const isOpen = openFaqIndex === index;
                  return (
                    <div
                      key={index}
                      className="bg-white rounded-xl border border-slate-200 overflow-hidden transition-all shadow-2xs"
                    >
                      <button
                        onClick={() => toggleFaq(index)}
                        className="w-full p-4 text-left flex items-center justify-between font-medium text-slate-900 hover:text-trust transition-colors focus:outline-none"
                      >
                        <span className="font-semibold text-sm sm:text-base">{faq.q}</span>
                        <ChevronDown
                          className={`w-5 h-5 text-slate-400 shrink-0 transition-transform duration-200 ${
                            isOpen ? 'transform rotate-180 text-trust' : ''
                          }`}
                        />
                      </button>

                      {isOpen && (
                        <div className="px-4 pb-4 text-sm text-slate-600 border-t border-slate-100 pt-3 leading-relaxed bg-slate-50/50">
                          {faq.a}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Horizontal Numbered Stepper Section */}
            <section className="space-y-4">
              <h2 className="font-serif text-2xl font-bold text-slate-900">
                {category.stepperTitle || `Step-by-step: ${category.name} Procedure`}
              </h2>

              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
                  {category.stepperSteps.map((s, idx) => (
                    <div key={idx} className="space-y-3 relative">
                      <div className="w-10 h-10 rounded-full bg-trust text-white font-serif font-bold text-lg flex items-center justify-center shadow-xs">
                        {s.step}
                      </div>
                      <h3 className="font-bold text-slate-900 text-base">
                        {s.title}
                      </h3>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {s.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>

          {/* RIGHT COLUMN (1/3 Width - Verified Resources Card) */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs sticky top-24 space-y-6">
              <div className="flex items-center space-x-2 border-b border-slate-100 pb-4">
                <Shield className="w-5 h-5 text-trust" />
                <h3 className="font-serif text-xl font-bold text-slate-900">
                  Verified Resources
                </h3>
              </div>

              <div className="space-y-4">
                {category.verifiedResources.map((res, idx) => (
                  <div key={idx} className="space-y-1.5 p-3 rounded-xl hover:bg-slate-50 transition-colors border border-slate-100">
                    <div className="flex items-start justify-between">
                      <div className="font-semibold text-slate-900 text-sm flex items-center gap-1.5">
                        {res.link.startsWith('tel:') ? (
                          <PhoneCall className="w-4 h-4 text-trust shrink-0" />
                        ) : (
                          <Globe className="w-4 h-4 text-trust shrink-0" />
                        )}
                        <span>{res.title}</span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-500 leading-relaxed">
                      {res.desc}
                    </p>

                    <div className="pt-1">
                      <a
                        href={res.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-xs font-semibold text-trust hover:text-trust-hover"
                      >
                        <span>Open Resource</span>
                        <ExternalLink className="w-3 h-3 ml-1" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </main>

      {/* FLOATING STICKY BOTTOM BUTTON */}
      <div className="fixed bottom-6 left-0 right-0 z-30 flex justify-center px-4 pointer-events-none">
        <button
          onClick={handleAskCategory}
          className="pointer-events-auto bg-trust text-white px-6 py-3.5 rounded-full font-medium text-sm sm:text-base hover:bg-trust-hover active:bg-trust-dark transition-all shadow-lg hover:shadow-xl flex items-center space-x-2.5 focus:outline-none focus:ring-4 focus:ring-trust/30"
        >
          <MessageSquare className="w-5 h-5 fill-current opacity-90" />
          <span>Ask Legal Connect about {category.name}</span>
        </button>
      </div>
    </div>
  );
}
