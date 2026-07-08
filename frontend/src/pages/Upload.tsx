import React, { useState } from 'react';
import axios from 'axios';
import { 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  FileSpreadsheet, 
  Trash2, 
  HelpCircle,
  Loader2,
  TableProperties,
  Award,
  ListFilter
} from 'lucide-react';

interface ColumnProfile {
  column_name: string;
  data_type: string;
  semantic_type: string;
  null_percentage: number;
  distinct_count: number;
}

interface CleaningReport {
  upload_id: string;
  filename: string;
  status: string;
  total_records: number;
  processed_records: number;
  null_report: Record<string, number>;
  duplicates_removed: number;
  outliers_detected: number;
  cleaning_time_seconds: number;
  domain: string;
  confidence_score: number;
  columns: ColumnProfile[];
}

export const Upload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<CleaningReport | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragging(true);
    } else if (e.type === 'dragleave') {
      setDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    setError(null);
    setReport(null);
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx' && ext !== 'xls') {
      setError('Unsupported file type. Please upload a CSV (.csv) or Excel spreadsheet (.xlsx, .xls).');
      setFile(null);
      return;
    }
    setFile(f);
  };

  const removeFile = () => {
    setFile(null);
    setError(null);
    setReport(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      await axios.get('/api/v1/analytics/datasets', {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch(e){}

    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('/api/v1/datasets/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
      });
      setReport(res.data);
      // Save newly uploaded dataset as active
      if (res.data.upload_id) {
        localStorage.setItem('active_dataset_id', res.data.upload_id);
      }
      setFile(null);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'An error occurred during dataset ingestion. Please check the spreadsheet schema structure.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black text-white">Intelligent Dataset Ingestion</h1>
        <p className="text-slate-400 text-sm mt-1">Upload any structured CSV or Excel file. Our engine automatically profiles schemas and infers business models.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card rounded-xl p-6">
            <h3 className="text-base font-bold text-slate-200 mb-4">Ingestion Console</h3>
            
            {/* Drag Drop Area */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`
                border-2 border-dashed rounded-xl p-8 text-center transition-all flex flex-col items-center justify-center min-h-[220px] relative
                ${dragging ? 'border-cyan-500 bg-cyan-950/10' : 'border-slate-800 hover:border-slate-700 bg-slate-900/10'}
              `}
            >
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileInput}
              />
              
              {!file ? (
                <>
                  <div className="p-4 rounded-full bg-slate-900 border border-slate-800 text-cyan-400 mb-4 shadow-inner">
                    <UploadCloud size={32} />
                  </div>
                  <label htmlFor="file-upload" className="cursor-pointer text-sm font-semibold text-cyan-400 hover:text-cyan-300">
                    Click to select file
                  </label>
                  <span className="text-xs text-slate-500 mt-2">or drag and drop spreadsheet here</span>
                  <span className="text-[10px] text-slate-600 mt-4 uppercase font-bold tracking-widest">CSV, XLS, XLSX (Max 100MB)</span>
                </>
              ) : (
                <div className="w-full max-w-sm p-4 bg-slate-900/60 border border-slate-800 rounded-lg flex items-center space-x-3 text-left">
                  <div className="p-2.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
                    <FileSpreadsheet size={24} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{file.name}</p>
                    <p className="text-[10px] text-slate-500 font-bold">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                  <button onClick={removeFile} className="p-1.5 rounded hover:bg-slate-800 text-slate-500 hover:text-rose-400 transition-colors">
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            </div>

            {/* Upload Buttons */}
            {file && (
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={removeFile}
                  disabled={loading}
                  className="px-4 py-2 border border-slate-800 rounded-lg text-slate-400 hover:bg-slate-800 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={loading}
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg text-xs font-bold shadow-lg shadow-cyan-500/10 flex items-center space-x-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={14} />
                      <span>Running Profiling Engine...</span>
                    </>
                  ) : (
                    <span>Execute Data Clean</span>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Success Cleaning Report */}
          {report && (
            <div className="space-y-6">
              <div className="glass-card rounded-xl p-6 border-l-4 border-l-emerald-500 space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="text-emerald-400 animate-bounce" size={24} />
                    <div>
                      <h3 className="text-base font-bold text-slate-200">ETL Pipeline Completed</h3>
                      <p className="text-xs text-slate-500">File processed and registered as active dataset</p>
                    </div>
                  </div>
                  <div className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-xs font-semibold text-cyan-400 flex items-center">
                    <Award size={14} className="mr-1.5" /> Domain: {report.domain} ({report.confidence_score}% Confidence)
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-slate-900 border border-slate-800/80 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest block">Original Records</span>
                    <span className="text-xl font-bold text-slate-200">{report.total_records.toLocaleString()}</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900 border border-slate-800/80 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest block">Cleaned & Saved</span>
                    <span className="text-xl font-bold text-emerald-400">{report.processed_records.toLocaleString()}</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900 border border-slate-800/80 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest block">Duplicates Pruned</span>
                    <span className="text-xl font-bold text-amber-500">{report.duplicates_removed.toLocaleString()}</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900 border border-slate-800/80 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest block">Clean Duration</span>
                    <span className="text-xl font-bold text-indigo-400">{report.cleaning_time_seconds}s</span>
                  </div>
                </div>

                {/* Null Reports */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center">
                    <TableProperties size={14} className="mr-1.5 text-cyan-400" />
                    Imputation Analysis (Original Null Percentage)
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-56 overflow-y-auto pr-1">
                    {Object.entries(report.null_report).map(([col, val]) => (
                      <div key={col} className="flex justify-between items-center text-xs p-2.5 rounded bg-slate-900/60 border border-slate-800/40">
                        <span className="text-slate-400 font-mono">{col}</span>
                        {val > 0 ? (
                          <span className="font-bold text-amber-500">{val}% filled</span>
                        ) : (
                          <span className="font-bold text-emerald-400">0% (clean)</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Dynamic Column Schema Profile Ledger */}
              {report.columns && report.columns.length > 0 && (
                <div className="glass-card rounded-xl p-6 border-l-4 border-l-cyan-500 space-y-4">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center">
                    <ListFilter size={14} className="mr-1.5 text-cyan-400" />
                    Auto-Detected Metadata Profile Ledger
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-500 font-bold uppercase tracking-wider">
                          <th className="pb-2">Column Name</th>
                          <th className="pb-2">Storage Datatype</th>
                          <th className="pb-2">Semantic Classification</th>
                          <th className="pb-2 text-right">Missing %</th>
                          <th className="pb-2 text-right">Distinct Cnt</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40 text-slate-300">
                        {report.columns.map((col, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/30 transition-colors">
                            <td className="py-2.5 font-semibold text-slate-200">{col.column_name}</td>
                            <td className="py-2.5 font-mono text-slate-400">{col.data_type}</td>
                            <td className="py-2.5">
                              <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                {col.semantic_type}
                              </span>
                            </td>
                            <td className="py-2.5 text-right">{col.null_percentage}%</td>
                            <td className="py-2.5 text-right">{col.distinct_count.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start space-x-3 text-rose-300 text-sm">
              <AlertCircle className="shrink-0 mt-0.5" size={18} />
              <div className="space-y-1">
                <p className="font-bold">Ingestion Blocked</p>
                <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Data Schema Guidelines Panel */}
        <div className="glass-card rounded-xl p-6 h-fit space-y-6">
          <div className="flex items-center space-x-2.5">
            <HelpCircle className="text-cyan-400" size={20} />
            <h3 className="text-base font-bold text-slate-200">Intelligent ETL Engine</h3>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Our schema-aware analytics platform is completely **metadata-driven**. We support raw business data uploads from any domain:
          </p>
          <div className="space-y-3">
            <div className="p-3 bg-slate-900/80 rounded border border-slate-800 text-xs">
              <p className="font-bold text-indigo-400 uppercase tracking-wider text-[10px]">Data Profiling</p>
              <p className="text-slate-400 mt-1 leading-relaxed">Automatically calculates null frequencies, duplicate items, cardinality stats, and standard deviations.</p>
            </div>
            <div className="p-3 bg-slate-900/80 rounded border border-slate-800 text-xs">
              <p className="font-bold text-cyan-400 uppercase tracking-wider text-[10px]">Semantic Typing</p>
              <p className="text-slate-400 mt-1 leading-relaxed">Detects business logic meanings like Monetary flows, Quantity measures, Dates, and Geographic labels.</p>
            </div>
            <div className="p-3 bg-slate-900/80 rounded border border-slate-800 text-xs">
              <p className="font-bold text-emerald-400 uppercase tracking-wider text-[10px]">Extensible Domain Recognition</p>
              <p className="text-slate-400 mt-1 leading-relaxed">Intelligently classifies datasets into Retail, Finance, HR, Healthcare, Marketing, or General Business.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Upload;
