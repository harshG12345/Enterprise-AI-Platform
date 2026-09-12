import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  Table,
  Columns,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Cpu,
  LineChart,
  Loader2,
  AlertCircle,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Wand2,
} from 'lucide-react';
import { getDataset, getDatasetPreview } from '../api/datasets';

export const DatasetDetails: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'preview' | 'schema' | 'missing'>('overview');
  const [previewPage, setPreviewPage] = useState<number>(1);
  const previewPageSize = 50;

  // Dataset details query
  const { data: detailData, isLoading: isDetailLoading, isError: isDetailError, error: detailError } = useQuery({
    queryKey: ['dataset', datasetId],
    queryFn: () => getDataset(datasetId!),
    enabled: !!datasetId,
  });

  // Dataset paginated preview query
  const { data: previewData, isLoading: isPreviewLoading } = useQuery({
    queryKey: ['dataset_preview', datasetId, previewPage],
    queryFn: () => getDatasetPreview(datasetId!, previewPage, previewPageSize),
    enabled: !!datasetId && activeTab === 'preview',
  });

  if (isDetailLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center bg-white rounded-xl border border-border">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="text-xs font-medium text-slate-500 mt-2">Loading dataset metadata...</span>
      </div>
    );
  }

  if (isDetailError || !detailData?.data) {
    return (
      <div className="p-8 max-w-xl mx-auto bg-white border border-red-200 rounded-xl shadow-sm text-center">
        <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
        <h2 className="text-sm font-bold text-slate-900">Dataset Not Found</h2>
        <p className="text-xs text-slate-500 mt-1">
          {(detailError as { message?: string })?.message || 'Could not load dataset details.'}
        </p>
        <Link
          to="/datasets"
          className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Datasets
        </Link>
      </div>
    );
  }

  const dataset = detailData.data;
  const columns = dataset.columns || [];

  const getTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'numeric':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'categorical':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'datetime':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'boolean':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link to="/datasets" className="hover:text-primary transition-colors">
          Datasets
        </Link>
        <span>/</span>
        <span className="font-semibold text-slate-900 truncate">{dataset.filename}</span>
      </div>

      {/* Dataset Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-blue-50 text-primary">
            <FileSpreadsheet className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">{dataset.filename}</h1>
              <span className="px-2 py-0.5 rounded-full bg-green-50 text-status-success font-semibold text-[10px] border border-green-200">
                {dataset.status}
              </span>
            </div>
            <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-500">
              <span className="font-mono">
                {dataset.row_count?.toLocaleString() || 0} rows × {dataset.column_count || 0} columns
              </span>
              <span>•</span>
              <span className="font-mono">
                {(dataset.file_size / (1024 * 1024)).toFixed(2)} MB on disk
              </span>
              <span>•</span>
              <div className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Uploaded: {new Date(dataset.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Link
            to={`/datasets/${dataset.id}/eda`}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold hover:bg-indigo-100 transition-colors shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            EDA Studio
          </Link>
          <Link
            to={`/datasets/${dataset.id}/preprocess`}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold hover:bg-emerald-100 transition-colors shadow-2xs"
          >
            <Wand2 className="w-3.5 h-3.5 text-emerald-600" />
            Feature Engineering
          </Link>
          <Link
            to="/training"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold transition-colors shadow-sm"
          >
            <Cpu className="w-3.5 h-3.5" />
            Train Model
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-border flex gap-6 text-xs font-semibold">
        {[
          { id: 'overview', label: 'Overview', icon: Database },
          { id: 'preview', label: 'Data Preview', icon: Table },
          { id: 'schema', label: 'Schema & Types', icon: Columns },
          { id: 'missing', label: 'Missing Values', icon: AlertTriangle },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`pb-3 relative transition-colors flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'text-primary border-b-2 border-primary font-bold'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
                <span className="text-xs text-slate-500 font-medium">Total Rows</span>
                <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                  {dataset.row_count?.toLocaleString() || 0}
                </div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
                <span className="text-xs text-slate-500 font-medium">Feature Columns</span>
                <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                  {dataset.column_count || 0}
                </div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
                <span className="text-xs text-slate-500 font-medium">Memory Usage</span>
                <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                  {dataset.memory_bytes
                    ? `${(dataset.memory_bytes / (1024 * 1024)).toFixed(2)} MB`
                    : 'N/A'}
                </div>
              </div>
            </div>

            {/* Feature Type Breakdown */}
            <div className="bg-white p-5 rounded-xl border border-border shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Feature Dtype Distribution</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {['numeric', 'categorical', 'datetime', 'boolean'].map((t) => {
                  const count = columns.filter((c) => c.inferred_type === t).length;
                  return (
                    <div key={t} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-center">
                      <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
                        {t}
                      </span>
                      <div className="text-lg font-bold text-slate-900 font-mono mt-0.5">{count}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Quick Actions Card */}
          <div className="bg-white p-5 rounded-xl border border-border shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 mb-2">Automated Data Science</h3>
              <p className="text-xs text-slate-500 mb-4">
                Run automated exploratory data analysis or launch the model training wizard.
              </p>
              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-100 text-[11px] text-blue-900 flex items-start gap-2">
                  <Sparkles className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                  <span>
                    Preprocessing pipelines will fit scalers and encoders on training folds strictly without data leakage.
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-2 mt-6">
              <button
                type="button"
                onClick={() => navigate(`/eda/${dataset.id}`)}
                className="w-full py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center justify-center gap-1.5"
              >
                <LineChart className="w-3.5 h-3.5" /> Run Exploratory Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Data Preview */}
      {activeTab === 'preview' && (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Table className="w-4 h-4 text-primary" />
              <h3 className="text-xs font-semibold text-slate-900">
                Paginated Data Preview (Showing 50 rows per page)
              </h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-600">
              <span>
                Page {previewData?.data?.page || 1} of {previewData?.data?.total_pages || 1}
              </span>
              <button
                type="button"
                onClick={() => setPreviewPage((p) => Math.max(1, p - 1))}
                disabled={previewPage <= 1 || isPreviewLoading}
                className="p-1 rounded border border-border hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setPreviewPage((p) => p + 1)}
                disabled={
                  !previewData?.data ||
                  previewPage >= previewData.data.total_pages ||
                  isPreviewLoading
                }
                className="p-1 rounded border border-border hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {isPreviewLoading ? (
            <div className="p-16 flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <span className="text-xs font-medium text-slate-500 mt-2">Loading row preview...</span>
            </div>
          ) : (
            <div className="overflow-x-auto max-h-[500px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 sticky top-0 border-b border-border text-slate-600">
                  <tr>
                    <th className="py-2.5 px-3 font-mono text-[10px] text-slate-400">#</th>
                    {previewData?.data?.columns.map((col) => (
                      <th key={col} className="py-2.5 px-4 font-semibold whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {previewData?.data?.rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2 px-3 font-mono text-[10px] text-slate-400">
                        {(previewPage - 1) * previewPageSize + idx + 1}
                      </td>
                      {previewData?.data?.columns.map((col) => (
                        <td key={col} className="py-2 px-4 whitespace-nowrap font-mono text-slate-700">
                          {row[col] !== null && row[col] !== undefined ? (
                            String(row[col])
                          ) : (
                            <span className="text-amber-500 italic text-[10px]">null</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab: Schema */}
      {activeTab === 'schema' && (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-border text-slate-500">
                  <th className="py-3 px-5 font-semibold">Column Name</th>
                  <th className="py-3 px-4 font-semibold">Pandas Dtype</th>
                  <th className="py-3 px-4 font-semibold">Inferred Semantic Type</th>
                  <th className="py-3 px-4 font-semibold">Missing Count (%)</th>
                  <th className="py-3 px-5 font-semibold text-right">Unique Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {columns.map((col) => (
                  <tr key={col.name} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-5 font-semibold text-slate-800">{col.name}</td>
                    <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">{col.dtype}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getTypeBadgeClass(
                          col.inferred_type
                        )}`}
                      >
                        {col.inferred_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-700">
                      {col.missing_count} ({col.missing_percentage}%)
                    </td>
                    <td className="py-3 px-5 text-right font-mono text-slate-700">
                      {col.unique_count.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Missing Values */}
      {activeTab === 'missing' && (
        <div className="bg-white p-6 rounded-xl border border-border shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-slate-900">Missing Values Summary</h3>
          <div className="space-y-3">
            {columns.map((col) => (
              <div key={col.name} className="space-y-1">
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span>{col.name}</span>
                  <span className="font-mono text-slate-500">
                    {col.missing_count} missing ({col.missing_percentage}%)
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      col.missing_percentage > 20
                        ? 'bg-status-error'
                        : col.missing_percentage > 0
                        ? 'bg-status-warning'
                        : 'bg-status-success'
                    }`}
                    style={{ width: `${Math.max(col.missing_percentage, 0)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
