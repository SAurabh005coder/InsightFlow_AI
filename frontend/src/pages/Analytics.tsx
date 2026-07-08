import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { 
  BarChart3, 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Loader2, 
  Inbox
} from 'lucide-react';

export const Analytics: React.FC = () => {
  const [columns, setColumns] = useState<string[]>([]);
  const [records, setRecords] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setCurrentPage(1);
    }, 450);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const datasetId = localStorage.getItem('active_dataset_id') || '';
      const offset = (currentPage - 1) * itemsPerPage;
      
      const url = `/api/v1/analytics/records?dataset_id=${datasetId}&limit=${itemsPerPage}&offset=${offset}&search=${encodeURIComponent(debouncedSearch)}`;
      const token = localStorage.getItem('token');
      const res = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setColumns(res.data.columns);
      setRecords(res.data.records);
      setTotal(res.data.total);
    } catch (err: any) {
      setError('Could not query raw database records. Ensure a business dataset is active.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [currentPage, debouncedSearch]);

  const totalPages = Math.ceil(total / itemsPerPage);

  if (loading && records.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] space-y-4">
        <Loader2 className="animate-spin text-cyan-400" size={48} />
        <p className="text-slate-400 text-sm">Querying database rows...</p>
      </div>
    );
  }

  if (error || columns.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-8 border border-dashed border-slate-800 rounded-2xl bg-slate-900/10">
        <Inbox className="text-slate-600 mb-4" size={64} />
        <h3 className="text-2xl font-bold text-slate-300">Analytical Vault Empty</h3>
        <p className="text-slate-400 text-sm max-w-md mt-1 mb-6">
          To query data tables and run dynamic filters, please upload a dataset first.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-black text-white flex items-center">
          Data Explorer
          <BarChart3 className="text-cyan-400 ml-2" size={24} />
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Raw transactional logs and dimensions for the active dataset ({total.toLocaleString()} rows total)
        </p>
      </div>

      {/* Control Console */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
        <div className="relative w-full md:max-w-md">
          <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
            <Search size={16} />
          </span>
          <input
            type="text"
            placeholder="Search across all fields..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 pl-10 pr-4 py-2 text-sm rounded-lg focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
          />
        </div>
        <div className="text-xs text-slate-500 font-medium">
          Showing {records.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0} to {Math.min(currentPage * itemsPerPage, total)} of {total.toLocaleString()} rows
        </div>
      </div>

      {/* Dynamic Data Table */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/40 text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                {columns.map((col) => (
                  <th key={col} className="p-4 border-r border-slate-800/30">
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {records.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-900/30 transition-colors text-slate-300">
                  {columns.map((col) => {
                    const val = row[col];
                    return (
                      <td key={col} className="p-4 border-r border-slate-800/20 max-w-[200px] truncate font-mono text-xs">
                        {val === null || val === undefined ? (
                          <span className="text-slate-600 italic">null</span>
                        ) : typeof val === 'number' ? (
                          val.toLocaleString()
                        ) : (
                          String(val)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
          <button
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1 || loading}
            className="flex items-center space-x-1 px-3.5 py-2 border border-slate-800 rounded-lg text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40 disabled:hover:bg-transparent"
          >
            <ChevronLeft size={14} />
            <span>Previous</span>
          </button>
          
          <div className="text-xs text-slate-400 font-semibold">
            Page {currentPage} of {totalPages}
          </div>

          <button
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages || loading}
            className="flex items-center space-x-1 px-3.5 py-2 border border-slate-800 rounded-lg text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40 disabled:hover:bg-transparent"
          >
            <span>Next</span>
            <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
};
export default Analytics;
