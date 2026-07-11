import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  UploadCloud, 
  BarChart3, 
  BrainCircuit, 
  FileDown, 
  Settings as SettingsIcon, 
  LogOut,
  User as UserIcon,
  Menu,
  X,
  Database
} from 'lucide-react';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, role, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [datasets, setDatasets] = React.useState<any[]>([]);
  const [activeDataset, setActiveDataset] = React.useState<string>('');

  React.useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const res = await axios.get('/api/v1/analytics/datasets', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setDatasets(res.data);
        const stored = localStorage.getItem('active_dataset_id');
        const datasetExists = res.data.some((d: any) => d.dataset_id === stored);
        if (stored && datasetExists) {
          setActiveDataset(stored);
        } else if (res.data.length > 0) {
          const firstId = res.data[0].dataset_id;
          localStorage.setItem('active_dataset_id', firstId);
          setActiveDataset(firstId);
        } else {
          localStorage.removeItem('active_dataset_id');
          setActiveDataset('');
        }
      } catch (err) {
        console.error('Failed to load datasets list', err);
      }
    };
    fetchDatasets();
  }, []);

  const handleDatasetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    localStorage.setItem('active_dataset_id', val);
    setActiveDataset(val);
    window.location.reload();
  };

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard, roles: ['CEO', 'Store_Manager', 'Sales_Manager', 'Data_Analyst'] },
    { name: 'Upload Dataset', href: '/upload', icon: UploadCloud, roles: ['CEO', 'Data_Analyst'] },
    { name: 'Business Analytics', href: '/analytics', icon: BarChart3, roles: ['CEO', 'Store_Manager', 'Sales_Manager', 'Data_Analyst'] },
    { name: 'Machine Learning', href: '/ml', icon: BrainCircuit, roles: ['CEO', 'Data_Analyst'] },
    { name: 'Reports & Export', href: '/reports', icon: FileDown, roles: ['CEO', 'Store_Manager', 'Sales_Manager', 'Data_Analyst'] },
    { name: 'Settings', href: '/settings', icon: SettingsIcon, roles: ['CEO', 'Store_Manager', 'Sales_Manager', 'Data_Analyst'] },
  ];

  const handleLogout = () => {
    logout();
    localStorage.removeItem('active_dataset_id');
    navigate('/login');
  };

  const filteredNav = navigation.filter(item => item.roles.includes(role || ''));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded bg-cyan-500 flex items-center justify-center font-bold text-slate-950">IF</div>
          <span className="text-xl font-bold tracking-wider text-cyan-400">InsightFlow AI</span>
        </div>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-slate-400 hover:text-white">
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Sidebar Navigation */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-slate-900/90 border-r border-slate-800/80 p-5 flex flex-col justify-between
        transform transition-transform duration-300 md:translate-x-0 md:static md:inset-auto md:w-64 md:h-screen
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="space-y-6">
          {/* Logo */}
          <div className="hidden md:flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center font-extrabold text-slate-950 text-lg shadow-lg shadow-cyan-500/20">IF</div>
            <div>
              <span className="text-2xl font-black tracking-wider bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">InsightFlow AI</span>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest -mt-1">Business Intelligence</p>
            </div>
          </div>

          {/* Dataset Switcher */}
          {datasets.length > 0 && (
            <div className="px-1 py-2 bg-slate-950/40 border border-slate-800/60 rounded-lg p-2.5 space-y-1.5 shadow-inner">
              <label className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block flex items-center">
                <Database size={10} className="mr-1 text-cyan-500" /> Active Dataset
              </label>
              <select
                value={activeDataset}
                onChange={handleDatasetChange}
                className="w-full bg-slate-900 border border-slate-800/60 text-slate-200 text-xs rounded p-1.5 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 cursor-pointer"
              >
                {datasets.map((d) => (
                  <option key={d.dataset_id} value={d.dataset_id}>
                    {d.filename.length > 18 ? d.filename.substring(0, 15) + '...' : d.filename}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="space-y-1">
            {filteredNav.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`
                    flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive 
                      ? 'bg-cyan-500/10 text-cyan-400 border-l-2 border-cyan-400 font-semibold shadow-inner shadow-cyan-500/5' 
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}
                  `}
                >
                  <Icon size={18} className={isActive ? 'text-cyan-400' : 'text-slate-400'} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card & Logout */}
        <div className="border-t border-slate-800/80 pt-4 mt-6">
          <div className="flex items-center space-x-3 px-2 py-2 mb-4 bg-slate-950/40 rounded-lg border border-slate-800/30">
            <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-cyan-400 border border-cyan-500/20">
              <UserIcon size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate">{user?.first_name} {user?.last_name}</p>
              <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
              <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
                {role?.replace('_', ' ')}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-screen overflow-y-auto bg-slate-950">
        <div className="p-4 md:p-8 max-w-7xl w-full mx-auto flex-1">
          {children}
        </div>
      </main>
    </div>
  );
};
export default Layout;
