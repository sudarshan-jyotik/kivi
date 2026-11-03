import React from 'react';
import { ShieldCheck, Plus, History } from 'lucide-react';

interface NavbarProps {
  currentView: 'upload' | 'reviews' | 'detail';
  setCurrentView: (view: 'upload' | 'reviews') => void;
  serverStatus: 'checking' | 'online' | 'offline';
  onNewAuditClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  setCurrentView,
  serverStatus,
  onNewAuditClick,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentView('reviews')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
              <ShieldCheck className="w-6 h-6 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-slate-900">AP Agent</span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-sky-100 text-sky-800">
                  Sarvam AI
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Autonomous 2-Way Match & Compliance</p>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center space-x-3">
            {/* Server Status Indicator */}
            <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border border-slate-200 bg-slate-50">
              <span className={`w-2 h-2 rounded-full ${
                serverStatus === 'online' ? 'bg-emerald-500 animate-pulse' :
                serverStatus === 'checking' ? 'bg-amber-400 animate-ping' : 'bg-rose-500'
              }`} />
              <span className="text-slate-600">
                {serverStatus === 'online' ? 'API Ready' :
                 serverStatus === 'checking' ? 'Waking Server...' : 'API Offline'}
              </span>
            </div>

            {/* View Switching */}
            <button
              onClick={() => setCurrentView('reviews')}
              className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                currentView === 'reviews'
                  ? 'bg-slate-100 text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <History className="w-4 h-4" />
              <span>Audit History</span>
            </button>

            {/* New Audit Button */}
            <button
              onClick={onNewAuditClick}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-sm shadow-sky-600/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              <span>New Audit</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
