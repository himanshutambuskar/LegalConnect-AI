import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Scale, MessageSquare } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'Categories', path: '/category/cybercrime' },
    { name: 'Resources', path: '/resources' },
    { name: 'About', path: '/about' },
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    if (path.startsWith('/category')) return location.pathname.startsWith('/category');
    return location.pathname === path;
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center space-x-2.5 group">
          <div className="w-9 h-9 rounded-lg bg-trust flex items-center justify-center text-white shadow-sm group-hover:bg-trust-dark transition-colors">
            <Scale className="w-5 h-5 stroke-[2.2]" />
          </div>
          <span className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-trust group-hover:text-trust-dark transition-colors">
            Legal Connect
          </span>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'text-trust bg-trust-light/60 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Action Button */}
        <div className="flex items-center space-x-3">
          <Link
            to="/chat"
            className="inline-flex items-center space-x-2 bg-trust text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-trust-hover active:bg-trust-dark transition-all shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-trust focus:ring-offset-2"
          >
            <MessageSquare className="w-4 h-4 fill-current opacity-90" />
            <span>Start Chat</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
