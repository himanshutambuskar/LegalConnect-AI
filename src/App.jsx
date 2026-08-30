import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import EmergencyBanner from './components/EmergencyBanner';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

import Home from './pages/Home';
import Chat from './pages/Chat';
import CategoryDetail from './pages/CategoryDetail';
import Resources from './pages/Resources';
import About from './pages/About';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <Router>
      <ScrollToTop />
      <div className="min-h-screen flex flex-col font-sans bg-slate-50 text-slate-800 antialiased selection:bg-trust-light selection:text-trust">
        <EmergencyBanner />
        <Navbar />
        
        <div className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/category/:id" element={<CategoryDetail />} />
            <Route path="/resources" element={<Resources />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>

        <Footer />
      </div>
    </Router>
  );
}
