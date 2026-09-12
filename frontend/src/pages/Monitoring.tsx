import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  ActivitySquare,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  Sliders,
  Search,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import { monitoringApi } from '../api/monitoring';
import { modelsApi } from '../api/models';
import { getProjects } from '../api/projects';
import { datasetsApi } from '../api/datasets';
import { Project } from '../types/project';
import { Dataset } from '../types/dataset';
import { ModelResponse } from '../types/models';
import { FeatureDriftReport } from '../types/monitoring';

export const Monitoring: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    searchParams.get('projectId') || ''
  );
  const [selectedModelId, setSelectedModelId] = useState<string>(
    searchParams.get('modelId') || ''
  );
  const [selectedFeatureName, setSelectedFeatureName] = useState<string>('');
  const [searchFeatureQuery, setSearchFeatureQuery] = useState<string>('');

  // Custom Drift Drawer State
  const [isCustomModalOpen, setIsCustomModalOpen] = useState<boolean>(false);
  const [evalDatasetId, setEvalDatasetId] = useState<string>('');
  const [alphaThreshold, setAlphaThreshold] = useState<number>(0.05);
  const [psiThreshold, setPsiThreshold] = useState<number>(0.2);

  // 1. Fetch Projects
  const { data: projectsRes } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({ page: 1, page_size: 100 }),
  });
  const projects = projectsRes?.data?.items || [];

  // 2. Fetch Models
  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['models', selectedProjectId],
    queryFn: () => modelsApi.listModels({ project_id: selectedProjectId || undefined }),
  });

  // Auto-select first model or production model
  useEffect(() => {
    if (models && models.length > 0 && !selectedModelId) {
      const prodModel = models.find((m) => m.status === 'PRODUCTION');
      setSelectedModelId(prodModel ? prodModel.id : models[0].id);
    }
  }, [models, selectedModelId]);

  // 3. Fetch Datasets for Custom Drift
  const { data: datasetsRes } = useQuery({
    queryKey: ['datasets', selectedProjectId],
    queryFn: () => datasetsApi.getDatasets({ project_id: selectedProjectId || undefined }),
  });
  const datasets = datasetsRes?.data?.items || [];


  // 4. Fetch Model Drift Analysis
  const {
    data: driftData,
    isLoading: driftLoading,
    refetch: refetchDrift,
  } = useQuery({
    queryKey: ['modelDrift', selectedModelId, alphaThreshold, psiThreshold],
    queryFn: () =>
      monitoringApi.getModelDrift(selectedModelId, {
        alpha: alphaThreshold,
        psi_threshold: psiThreshold,
      }),
    enabled: !!selectedModelId,
  });

  // Auto-select first feature for distribution visualization
  useEffect(() => {
    if (driftData && driftData.feature_reports && driftData.feature_reports.length > 0) {
      if (!selectedFeatureName || !driftData.feature_reports.some((f) => f.feature_name === selectedFeatureName)) {
        setSelectedFeatureName(driftData.feature_reports[0].feature_name);
      }
    }
  }, [driftData, selectedFeatureName]);

  // Custom Drift Mutation
  const customDriftMutation = useMutation({
    mutationFn: (payload: { current_dataset_id?: string; alpha: number; psi_threshold: number }) =>
      monitoringApi.analyzeCustomDrift(selectedModelId, payload),
    onSuccess: (data) => {
      setIsCustomModalOpen(false);
      queryClient.setQueryData(
        ['modelDrift', selectedModelId, alphaThreshold, psiThreshold],
        data
      );
    },
  });

  const selectedFeatureReport = (driftData?.feature_reports || []).find(
    (f) => f.feature_name === selectedFeatureName
  );

  const filteredFeatures = (driftData?.feature_reports || []).filter((f) =>
    f.feature_name.toLowerCase().includes(searchFeatureQuery.toLowerCase())
  );

  const getHealthBadge = (status?: string) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            Stable & Healthy
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 shadow-sm">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            Moderate Shift (Warning)
          </span>
        );
      case 'DRIFT_DETECTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 shadow-sm animate-pulse">
            <AlertOctagon className="h-4 w-4 text-rose-600" />
            Drift Alert Triggered
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100">
            {status || 'Unknown'}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary">
              <ActivitySquare className="h-6 w-6 text-primary" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">Drift & Observability Engine</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Statistical data drift detection, Kolmogorov-Smirnov hypothesis testing, and Population Stability Index (PSI).
          </p>
        </div>

        {/* Global Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="w-56">
            <select
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value);
                setSelectedModelId('');
              }}
              className="w-full px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary shadow-sm"
            >
              <option value="">All Projects</option>
              {projects.map((p: Project) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="w-64">
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              disabled={modelsLoading}
              className="w-full px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary shadow-sm"
            >
              <option value="">Select Monitored Model...</option>
              {(models || []).map((m: ModelResponse) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.version}) — {m.status}
                </option>
              ))}
            </select>
          </div>


          <button
            onClick={() => refetchDrift()}
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
            title="Refresh drift statistics"
          >
            <RefreshCw className="h-4 w-4" />
          </button>

          <button
            onClick={() => setIsCustomModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary/90 transition-all shadow-sm"
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>Custom Evaluation</span>
          </button>
        </div>
      </div>

      {/* Model Observability KPI Cards */}
      {driftData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-border shadow-sm flex flex-col justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Overall Model Health
            </span>
            <div className="mt-2">{getHealthBadge(driftData.health_status)}</div>
            <span className="text-[10px] text-slate-400 mt-2 block font-mono">
              Evaluated: {new Date(driftData.analyzed_at).toLocaleTimeString()}
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Max Population Stability (PSI)
            </span>
            <div
              className={`text-2xl font-bold font-mono mt-1 ${
                driftData.max_psi >= 0.2
                  ? 'text-rose-600'
                  : driftData.max_psi >= 0.1
                  ? 'text-amber-600'
                  : 'text-emerald-600'
              }`}
            >
              {driftData.max_psi.toFixed(4)}
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {driftData.max_psi < 0.1 ? 'Stable (< 0.10)' : driftData.max_psi < 0.2 ? 'Moderate Shift (0.10 - 0.20)' : 'Drift Triggered (>= 0.20)'}
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Drifted Features Count
            </span>
            <div className="text-2xl font-bold font-mono text-primary mt-1">
              {driftData.drifted_features_count} / {driftData.total_features}
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {driftData.drift_percentage}% of feature space shifted
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Sample Comparison Size
            </span>
            <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
              {driftData.current_sample_count} rows
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Baseline: {driftData.baseline_sample_count} training rows
            </span>
          </div>
        </div>
      )}

      {/* Main Studio View: Table on Left + Visual HUD on Right */}
      {driftLoading ? (
        <div className="bg-white rounded-xl border border-border p-12 text-center text-xs text-slate-500">
          <div className="h-7 w-7 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          Calculating Kolmogorov-Smirnov and Population Stability Index scores...
        </div>
      ) : driftData ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Feature Drift Breakdown Table */}
          <div className="lg:col-span-6 bg-white rounded-xl border border-border shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border flex items-center justify-between gap-3">
              <div className="relative flex-1">
                <Search className="h-4 w-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchFeatureQuery}
                  onChange={(e) => setSearchFeatureQuery(e.target.value)}
                  placeholder="Filter feature names..."
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
              <span className="text-xs font-semibold text-slate-500">
                {filteredFeatures.length} features
              </span>
            </div>

            <div className="overflow-x-auto flex-1 max-h-[500px]">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider sticky top-0">
                  <tr>
                    <th className="py-2.5 px-4">Feature Name</th>
                    <th className="py-2.5 px-3">Test</th>
                    <th className="py-2.5 px-3">PSI Score</th>
                    <th className="py-2.5 px-3">$p$-Value</th>
                    <th className="py-2.5 px-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredFeatures.map((f: FeatureDriftReport) => {
                    const isSelected = f.feature_name === selectedFeatureName;
                    return (
                      <tr
                        key={f.feature_name}
                        onClick={() => setSelectedFeatureName(f.feature_name)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-primary/10 font-semibold'
                            : 'hover:bg-slate-50'
                        }`}
                      >
                        <td className="py-2.5 px-4 font-mono text-slate-800 flex items-center gap-1.5">
                          <span className="truncate max-w-[130px]" title={f.feature_name}>
                            {f.feature_name}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-500">{f.primary_test}</td>
                        <td className="py-2.5 px-3 font-mono font-bold">
                          <span
                            className={
                              f.psi_score >= 0.2
                                ? 'text-rose-600'
                                : f.psi_score >= 0.1
                                ? 'text-amber-600'
                                : 'text-slate-700'
                            }
                          >
                            {f.psi_score.toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-500">
                          {f.p_value.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          {f.drift_detected ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                              Drifted
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                              Stable
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Distribution Comparison Overlay HUD */}
          <div className="lg:col-span-6 space-y-6">
            {selectedFeatureReport ? (
              <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Feature Distribution Comparison
                    </span>
                    <h3 className="text-base font-bold text-slate-900 font-mono">
                      {selectedFeatureReport.feature_name}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-500">
                      PSI: <strong className="text-primary">{selectedFeatureReport.psi_score.toFixed(4)}</strong>
                    </span>
                    {selectedFeatureReport.drift_detected ? (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                        Shift Alert
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                        No Drift
                      </span>
                    )}
                  </div>
                </div>

                {/* Overlaid Histogram Chart */}
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={selectedFeatureReport.histogram_bins}
                      margin={{ top: 10, right: 10, left: -10, bottom: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis
                        dataKey="bin_label"
                        tick={{ fontSize: 10, fill: '#64748B' }}
                        angle={-20}
                        textAnchor="end"
                      />
                      <YAxis
                        unit="%"
                        domain={[0, 'dataMax + 10']}
                        tick={{ fontSize: 10, fill: '#64748B' }}
                      />
                      <Tooltip
                        formatter={(val: number) => [`${val}%`, '']}
                        contentStyle={{
                          backgroundColor: '#0F172A',
                          color: '#fff',
                          borderRadius: '8px',
                          fontSize: '11px',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Bar
                        dataKey="baseline_pct"
                        name="Baseline (Training Data)"
                        fill="#3B82F6"
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar
                        dataKey="current_pct"
                        name="Current (Inference Stream)"
                        fill={selectedFeatureReport.drift_detected ? '#F43F5E' : '#10B981'}
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Statistics Summary Grid */}
                {selectedFeatureReport.feature_type === 'numerical' && (
                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border text-xs">
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                      <span className="font-bold text-slate-700 block text-[11px] uppercase">
                        Baseline Distribution
                      </span>
                      <div className="flex justify-between text-slate-500 font-mono">
                        <span>Mean:</span> <strong>{selectedFeatureReport.baseline_stats.mean}</strong>
                      </div>
                      <div className="flex justify-between text-slate-500 font-mono">
                        <span>Std Dev:</span> <strong>{selectedFeatureReport.baseline_stats.std}</strong>
                      </div>
                      <div className="flex justify-between text-slate-500 font-mono">
                        <span>Range:</span> [{selectedFeatureReport.baseline_stats.min} .. {selectedFeatureReport.baseline_stats.max}]
                      </div>
                    </div>

                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                      <span className="font-bold text-slate-700 block text-[11px] uppercase">
                        Current Inference Stream
                      </span>
                      <div className="flex justify-between text-slate-500 font-mono">
                        <span>Mean:</span> <strong>{selectedFeatureReport.current_stats.mean}</strong>
                      </div>
                      <div className="flex justify-between text-slate-500 font-mono">
                        <span>Std Dev:</span> <strong>{selectedFeatureReport.current_stats.std}</strong>
                      </div>
                      <div className="flex justify-between text-slate-500 font-mono">
                        <span>Range:</span> [{selectedFeatureReport.current_stats.min} .. {selectedFeatureReport.current_stats.max}]
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center text-xs text-slate-400">
                Select a feature from the table to view the statistical distribution comparison.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-border p-12 text-center">
          <ActivitySquare className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Monitored Models Available</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Train and register models in the ML Studio to begin tracking continuous feature and concept drift.
          </p>
        </div>
      )}

      {/* Custom Evaluation Drift Modal */}
      {isCustomModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Custom Drift Evaluation</h3>
                <p className="text-xs text-slate-500 mt-0.5">Test distribution shifts against custom datasets</p>
              </div>
              <button
                onClick={() => setIsCustomModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Evaluation Dataset (Optional)
                </label>
                <select
                  value={evalDatasetId}
                  onChange={(e) => setEvalDatasetId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  <option value="">Use Live Production Predictions Stream</option>
                  {datasets.map((d: Dataset) => (
                    <option key={d.id} value={d.id}>
                      {d.filename} ({d.row_count || 0} rows)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  KS / Chi-Square Significance Level ($\alpha$)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.001"
                  max="0.2"
                  value={alphaThreshold}
                  onChange={(e) => setAlphaThreshold(parseFloat(e.target.value) || 0.05)}
                  className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  PSI Drift Alert Threshold
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0.05"
                  max="0.5"
                  value={psiThreshold}
                  onChange={(e) => setPsiThreshold(parseFloat(e.target.value) || 0.2)}
                  className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setIsCustomModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={customDriftMutation.isPending}
                onClick={() =>
                  customDriftMutation.mutate({
                    current_dataset_id: evalDatasetId || undefined,
                    alpha: alphaThreshold,
                    psi_threshold: psiThreshold,
                  })
                }
                className="px-4 py-2 text-xs font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                {customDriftMutation.isPending ? 'Analyzing...' : 'Run Analysis'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
