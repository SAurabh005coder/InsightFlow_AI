import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { 
  DollarSign, 
  Percent, 
  ShoppingBag, 
  ArrowUpRight, 
  Brain, 
  Sparkles,
  Inbox,
  Loader2,
  Database,
  Award
} from 'lucide-react';

interface DynamicKPI {
  name: string;
  value: string;
  formula: string;
}

interface DynamicChart {
  type: string;
  title: string;
  x_axis: string;
  y_axis: string;
  data: Array<{ name?: string; date?: string; value: number }>;
}

interface DashboardData {
  dataset_id: string;
  filename: string;
  domain: string;
  confidence_score: number;
  record_count: number;
  kpis: DynamicKPI[];
  charts: DynamicChart[];
  insights: string[];
}

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const datasetId = localStorage.getItem('active_dataset_id') || '';
      const url = datasetId 
        ? `/api/v1/analytics/dashboard?dataset_id=${datasetId}`
        : '/api/v1/analytics/dashboard';
        
      const res = await axios.get(url);
      setData(res.data);
    } catch (err: any) {
      setError('Failed to load metadata dashboard. Please make sure the backend is running and datasets exist.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] space-y-4">
        <Loader2 className="animate-spin text-cyan-400" size={48} />
        <p className="text-slate-400 text-sm">Running DuckDB analytical cubes...</p>
      </div>
    );
  }

  if (error || !data || data.dataset_id === "") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-8 border border-dashed border-slate-800 rounded-2xl bg-slate-900/10">
        <Inbox className="text-slate-600 mb-4" size={64} />
        <h3 className="text-2xl font-bold text-slate-300">No Datasets Uploaded</h3>
        <p className="text-slate-400 text-sm max-w-md mt-1 mb-6">
          To generate dynamic dashboard analytics, KPIs, ML forecasts, and data quality insights, upload a CSV or Excel dataset.
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold rounded-lg text-sm shadow-lg shadow-cyan-500/10 active:scale-98 transition-all flex items-center space-x-2 animate-pulse"
        >
          <span>Upload Your First Dataset</span>
          <ArrowUpRight size={18} />
        </button>
      </div>
    );
  }

  // Visual helper colors for dynamic borders
  const borderColors = [
    'border-l-cyan-500',
    'border-l-indigo-500',
    'border-l-emerald-500',
    'border-l-purple-500',
    'border-l-amber-500'
  ];

  const textColors = [
    'text-cyan-400',
    'text-indigo-400',
    'text-emerald-400',
    'text-purple-400',
    'text-amber-400'
  ];

  const bgColors = [
    'bg-cyan-500/10',
    'bg-indigo-500/10',
    'bg-emerald-500/10',
    'bg-purple-500/10',
    'bg-amber-500/10'
  ];

  return (
    <div className="space-y-8">
      {/* Dynamic Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white flex items-center">
            {data.filename.split('.')[0].replace(/_/g, ' ').toUpperCase()} Strategy Room
          </h1>
          <div className="flex flex-wrap items-center gap-2.5 mt-1.5 text-slate-400 text-xs font-semibold">
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400 flex items-center">
              <Database size={12} className="mr-1" /> Ingested Rows: {data.record_count.toLocaleString()}
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-400 flex items-center">
              <Award size={12} className="mr-1" /> Domain: {data.domain} ({data.confidence_score}% Confidence)
            </span>
          </div>
        </div>
        <button
          onClick={() => navigate('/reports')}
          className="px-4 py-2.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-xs font-semibold text-slate-200 shadow-sm transition-colors"
        >
          Download Dynamic Report
        </button>
      </div>

      {/* Dynamic KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {data.kpis.map((kpi, idx) => {
          const colorIdx = idx % borderColors.length;
          return (
            <div 
              key={idx} 
              className={`glass-card p-6 rounded-xl relative overflow-hidden flex flex-col justify-between min-h-[140px] border-l-4 ${borderColors[colorIdx]}`}
            >
              <div className="flex justify-between items-start">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{kpi.name}</span>
                <span className={`p-1.5 rounded-lg ${bgColors[colorIdx]} ${textColors[colorIdx]}`}>
                  {kpi.name.toLowerCase().includes('percentage') || kpi.name.toLowerCase().includes('rate') || kpi.name.toLowerCase().includes('margin') ? (
                    <Percent size={18} />
                  ) : kpi.name.toLowerCase().includes('count') || kpi.name.toLowerCase().includes('volume') ? (
                    <ShoppingBag size={18} />
                  ) : (
                    <DollarSign size={18} />
                  )}
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-3xl font-bold tracking-tight text-white">{kpi.value}</h3>
                <p className="text-[10px] text-slate-500 font-semibold mt-1">Aggregated via {kpi.formula}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dynamic AI Insights */}
      {data.insights.length > 0 && (
        <div className="p-6 rounded-xl border border-indigo-500/20 bg-indigo-950/20 shadow-lg shadow-indigo-500/5">
          <div className="flex items-center space-x-2.5 mb-4">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400"><Brain size={20} /></div>
            <div>
              <h3 className="text-lg font-bold text-slate-100 flex items-center">
                Statistical Briefing
                <Sparkles size={14} className="text-indigo-400 ml-1.5 animate-pulse" />
              </h3>
              <p className="text-xs text-slate-500">Heuristic schema analysis and data quality signals</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.insights.map((insight, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 text-sm leading-relaxed text-slate-300">
                <span className="inline-block w-1.5 h-1.5 bg-indigo-400 rounded-full mr-2.5" />
                {insight.split('**').map((text, i) => i % 2 === 1 ? <strong key={i} className="text-cyan-400">{text}</strong> : text)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dynamic Charts Grid */}
      {data.charts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {data.charts.map((chart, idx) => (
            <div key={idx} className="glass-card p-6 rounded-xl flex flex-col justify-between min-h-[380px]">
              <div className="mb-4">
                <h3 className="text-base font-bold text-slate-200">{chart.title}</h3>
                <p className="text-xs text-slate-500">
                  Aggregated grouping: {chart.x_axis} vs {chart.y_axis}
                </p>
              </div>
              <div className="w-full h-80 overflow-hidden">
                {chart.type === 'Line Chart' ? (
                  <Plot
                    data={[
                      {
                        x: chart.data.map(d => d.date || d.name || ''),
                        y: chart.data.map(d => d.value),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: chart.y_axis,
                        marker: { color: '#06b6d4' },
                        line: { width: 3 }
                      }
                    ]}
                    layout={{
                      autosize: true,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      margin: { l: 45, r: 15, t: 15, b: 40 },
                      xaxis: { gridcolor: '#1e293b', tickfont: { color: '#64748b' } },
                      yaxis: { gridcolor: '#1e293b', tickfont: { color: '#64748b' } },
                      showlegend: false
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    style={{ width: '100%', height: '100%' }}
                  />
                ) : chart.type === 'Pie Chart' ? (
                  <Plot
                    data={[
                      {
                        labels: chart.data.map(d => d.name || d.date || ''),
                        values: chart.data.map(d => d.value),
                        type: 'pie',
                        hole: 0.4,
                        marker: { colors: ['#06b6d4', '#6366f1', '#10b981', '#a855f7', '#f59e0b', '#ec4899', '#f43f5e'] }
                      }
                    ]}
                    layout={{
                      autosize: true,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      margin: { l: 20, r: 20, t: 15, b: 30 },
                      legend: { font: { color: '#94a3b8' }, orientation: 'h', x: 0, y: -0.15 }
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    style={{ width: '100%', height: '100%' }}
                  />
                ) : (
                  // Bar Chart fallback
                  <Plot
                    data={[
                      {
                        x: chart.data.map(d => d.name || d.date || ''),
                        y: chart.data.map(d => d.value),
                        type: 'bar',
                        marker: { color: '#6366f1' }
                      }
                    ]}
                    layout={{
                      autosize: true,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      margin: { l: 45, r: 15, t: 15, b: 40 },
                      xaxis: { gridcolor: '#1e293b', tickfont: { color: '#64748b' } },
                      yaxis: { gridcolor: '#1e293b', tickfont: { color: '#64748b' } },
                      showlegend: false
                    }}
                    config={{ displayModeBar: false, responsive: true }}
                    style={{ width: '100%', height: '100%' }}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default Dashboard;
