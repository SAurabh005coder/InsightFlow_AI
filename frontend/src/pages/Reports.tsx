import React, { useState } from 'react';
import axios from 'axios';
import { 
  FileDown, 
  FileSpreadsheet, 
  FileText, 
  Loader2, 
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

export const Reports: React.FC = () => {
  const [downloading, setDownloading] = useState<'pdf' | 'excel' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleDownload = async (type: 'pdf' | 'excel') => {
    setDownloading(type);
    setError(null);
    setSuccess(null);

    const datasetId = localStorage.getItem('active_dataset_id') || '';
    const url = type === 'pdf' 
      ? `/api/v1/reports/export/pdf?dataset_id=${datasetId}` 
      : `/api/v1/reports/export/excel?dataset_id=${datasetId}`;
    const filename = type === 'pdf' ? 'insightflow_executive_report.pdf' : 'insightflow_business_report.xlsx';

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(url, {
        responseType: 'blob',
        headers: { Authorization: `Bearer ${token}` }
      });

      // Browser download trigger
      const blob = new Blob([response.data], {
        type: type === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      setSuccess(`${type.toUpperCase()} report downloaded successfully!`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(`Failed to compile ${type.toUpperCase()} report. Ensure sales data is uploaded and databases are connected.`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-black text-white flex items-center">
          Reports & Export
          <FileDown className="text-cyan-400 ml-2.5" size={24} />
        </h1>
        <p className="text-slate-400 text-sm mt-1">Export formatted executive summaries and comprehensive spreadsheet ledgers</p>
      </div>

      {success && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center space-x-3 text-emerald-300 text-xs font-semibold">
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center space-x-3 text-rose-300 text-xs font-semibold">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Exporters grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* PDF Card */}
        <div className="glass-card p-6 rounded-xl flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
              <FileText size={24} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-200">Executive PDF Briefing</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                A highly formatted, printable business summary compiled using ReportLab.
              </p>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-400">
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mr-2" /> AI-Generated Executive insights</li>
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mr-2" /> Key Metadata KPIs (Revenue, Volume, etc.)</li>
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mr-2" /> Schema profiling details ledger</li>
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mr-2" /> Clean document layout structure</li>
            </ul>
          </div>
          <button
            onClick={() => handleDownload('pdf')}
            disabled={downloading !== null}
            className="w-full py-3 bg-slate-900 border border-slate-800 hover:border-cyan-500/40 text-slate-200 hover:text-white rounded-lg text-xs font-semibold tracking-wide transition-all active:scale-[0.98] flex items-center justify-center space-x-2 shadow-sm"
          >
            {downloading === 'pdf' ? (
              <>
                <Loader2 className="animate-spin text-cyan-400" size={14} />
                <span>Compiling Document...</span>
              </>
            ) : (
              <span>Download PDF Briefing</span>
            )}
          </button>
        </div>

        {/* Excel Card */}
        <div className="glass-card p-6 rounded-xl flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
              <FileSpreadsheet size={24} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-200">Analytical Excel Workbook</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                A multi-sheet spreadsheet ledger built dynamically using OpenPyXL.
              </p>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-400">
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2" /> Dynamic multi-tab worksheets</li>
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2" /> Ingested raw records workbook sheet</li>
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2" /> Detected Column Schema Profile tab</li>
              <li className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2" /> Sized columns & formatted masks</li>
            </ul>
          </div>
          <button
            onClick={() => handleDownload('excel')}
            disabled={downloading !== null}
            className="w-full py-3 bg-slate-900 border border-slate-800 hover:border-emerald-500/40 text-slate-200 hover:text-white rounded-lg text-xs font-semibold tracking-wide transition-all active:scale-[0.98] flex items-center justify-center space-x-2 shadow-sm"
          >
            {downloading === 'excel' ? (
              <>
                <Loader2 className="animate-spin text-emerald-400" size={14} />
                <span>Generating Workbook...</span>
              </>
            ) : (
              <span>Download Excel Workbook</span>
            )}
          </button>
        </div>

      </div>
    </div>
  );
};
export default Reports;
