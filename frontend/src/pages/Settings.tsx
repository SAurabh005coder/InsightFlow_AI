import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  User as UserIcon, 
  Database, 
  Settings as SettingsIcon, 
  Check, 
  Lock,
  Moon,
  Laptop
} from 'lucide-react';

export const Settings: React.FC = () => {
  const { user, role } = useAuth();
  const [dbStatus] = useState({ postgres: 'Connected', duckdb: 'Initialized' });
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg('Settings updated successfully!');
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-black text-white flex items-center">
          Settings
          <SettingsIcon className="text-cyan-400 ml-2.5" size={24} />
        </h1>
        <p className="text-slate-400 text-sm mt-1">Configure your personal workspace and verify database clustering states</p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center space-x-2 text-emerald-300 text-xs font-semibold">
          <Check size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Profile Settings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 rounded-xl">
            <h3 className="text-base font-bold text-slate-200 mb-6 flex items-center space-x-2">
              <UserIcon size={18} className="text-cyan-400" />
              <span>User Profile Details</span>
            </h3>
            
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">First Name</label>
                  <input
                    type="text"
                    disabled
                    value={user?.first_name || ''}
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 cursor-not-allowed"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Last Name</label>
                  <input
                    type="text"
                    disabled
                    value={user?.last_name || ''}
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Email Address</label>
                <input
                  type="email"
                  disabled
                  value={user?.email || ''}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Workspace Role Badge</label>
                <input
                  type="text"
                  disabled
                  value={role?.replace('_', ' ') || ''}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 cursor-not-allowed uppercase font-bold tracking-wider"
                />
              </div>
            </form>
          </div>

          {/* Change password mock card */}
          <div className="glass-card p-6 rounded-xl">
            <h3 className="text-base font-bold text-slate-200 mb-6 flex items-center space-x-2">
              <Lock size={18} className="text-indigo-400" />
              <span>Change Security Credentials</span>
            </h3>
            
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Current Password</label>
                  <input
                    type="password"
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">New Password</label>
                  <input
                    type="password"
                    placeholder="Min 8 characters"
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg"
                >
                  Change Password
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Database Clustering State */}
        <div className="space-y-6">
          <div className="glass-card p-6 rounded-xl space-y-6">
            <h3 className="text-base font-bold text-slate-200 flex items-center space-x-2">
              <Database size={18} className="text-cyan-400" />
              <span>Database Cluster State</span>
            </h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3.5 bg-slate-900 border border-slate-800/80 rounded-lg text-xs">
                <div className="space-y-1">
                  <p className="font-semibold text-slate-200">PostgreSQL (OLTP)</p>
                  <p className="text-[10px] text-slate-500">Port 5432, 15 relational tables</p>
                </div>
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                  {dbStatus.postgres}
                </span>
              </div>

              <div className="flex justify-between items-center p-3.5 bg-slate-900 border border-slate-800/80 rounded-lg text-xs">
                <div className="space-y-1">
                  <p className="font-semibold text-slate-200">DuckDB (OLAP)</p>
                  <p className="text-[10px] text-slate-500">Vectorized columnar execution</p>
                </div>
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 uppercase">
                  {dbStatus.duckdb}
                </span>
              </div>
            </div>
          </div>

          {/* Theme card */}
          <div className="glass-card p-6 rounded-xl space-y-4">
            <h3 className="text-base font-bold text-slate-200 flex items-center space-x-2">
              <Moon size={18} className="text-purple-400" />
              <span>Application Theme</span>
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              RetailIQ defaults to a premium dark theme.
            </p>
            <div className="flex items-center space-x-2 p-2 bg-slate-900 border border-slate-800 rounded-lg w-fit">
              <button className="p-2 rounded bg-slate-950 text-cyan-400 shadow flex items-center space-x-1.5 text-xs font-semibold">
                <Moon size={14} />
                <span>Dark (Glass)</span>
              </button>
              <button disabled className="p-2 rounded text-slate-500 cursor-not-allowed flex items-center space-x-1.5 text-xs">
                <Laptop size={14} />
                <span>Light</span>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
export default Settings;
