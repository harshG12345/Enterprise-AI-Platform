import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  FlaskConical,
  Plus,
  GitCompare,
  BarChart2,
  Layers,
  FileText,
  X,
  ChevronRight,
  Sparkles,
  Activity,
  FolderArchive,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

import { experimentsApi } from '../api/experiments';
import { getProjects } from '../api/projects';
import { Project } from '../types/project';
import {
  Experiment,
  RunDetail,
} from '../types/experiment';

export const Experiments: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    searchParams.get('projectId') || ''
  );
  const [selectedExperimentId, setSelectedExperimentId] = useState<string>('');
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'runs' | 'compare' | 'learning_curves'>('runs');
  const [inspectedRunId, setInspectedRunId] = useState<string | null>(null);

  // New Experiment Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [newExpName, setNewExpName] = useState<string>('');
  const [createError, setCreateError] = useState<string | null>(null);

  // Selected Metric for Learning Curves
  const [selectedMetricKey, setSelectedMetricKey] = useState<string>('accuracy');

  // 1. Fetch Projects
  const { data: projectsRes, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({ page: 1, page_size: 100 }),
  });
  const projects = projectsRes?.data?.items || [];

  // Auto-select first project
  useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  // 2. Fetch Experiments for Project
  const { data: experiments, isLoading: experimentsLoading, refetch: refetchExperiments } = useQuery({
    queryKey: ['experiments', selectedProjectId],
    queryFn: () => experimentsApi.getExperiments(selectedProjectId || undefined),
    enabled: !!selectedProjectId,
  });

  // Auto-select first experiment
  useEffect(() => {
    if (experiments && experiments.length > 0) {
      if (!selectedExperimentId || !experiments.some((e: Experiment) => e.id === selectedExperimentId)) {
        setSelectedExperimentId(experiments[0].id);
      }
    } else {
      setSelectedExperimentId('');
    }
  }, [experiments, selectedExperimentId]);

  // 3. Fetch Runs for Selected Experiment
  const {
    data: runs,
    isLoading: runsLoading,
    refetch: refetchRuns,
  } = useQuery({
    queryKey: ['experimentRuns', selectedExperimentId],
    queryFn: () => experimentsApi.getExperimentRuns(selectedExperimentId),
    enabled: !!selectedExperimentId,
  });

  // 4. Fetch Run Comparison when 2+ runs selected
  const { data: comparisonData, isLoading: comparisonLoading } = useQuery({
    queryKey: ['runComparison', selectedRunIds],
    queryFn: () => experimentsApi.compareRuns(selectedRunIds),
    enabled: selectedRunIds.length >= 2 && activeTab === 'compare',
  });

  // 5. Fetch Inspected Run Details
  const { data: inspectedRun } = useQuery({
    queryKey: ['runDetail', inspectedRunId],
    queryFn: () => experimentsApi.getRunDetails(inspectedRunId!),
    enabled: !!inspectedRunId,
  });

  // 6. Fetch Learning Curves for selected metric
  const { data: metricHistory } = useQuery({
    queryKey: ['metricHistory', selectedRunIds[0], selectedMetricKey],
    queryFn: () => experimentsApi.getMetricHistory(selectedRunIds[0], selectedMetricKey),
    enabled: selectedRunIds.length > 0 && activeTab === 'learning_curves',
  });

  // Create Experiment Mutation
  const createExpMutation = useMutation({
    mutationFn: (name: string) =>
      experimentsApi.createExperiment({
        project_id: selectedProjectId,
        name,
      }),
    onSuccess: (newExp) => {
      setIsCreateModalOpen(false);
      setNewExpName('');
      setCreateError(null);
      queryClient.invalidateQueries({ queryKey: ['experiments', selectedProjectId] });
      setSelectedExperimentId(newExp.id);
    },
    onError: (err: any) => {
      setCreateError(err.response?.data?.error?.message || err.message || 'Failed to create experiment');
    },
  });

  const handleToggleRunSelection = (runId: string) => {
    setSelectedRunIds((prev) =>
      prev.includes(runId) ? prev.filter((id) => id !== runId) : [...prev, runId]
    );
  };

  const handleSelectAllRuns = () => {
    if (!runs) return;
    if (selectedRunIds.length === runs.length) {
      setSelectedRunIds([]);
    } else {
      setSelectedRunIds(runs.map((r) => r.run_id));
    }
  };

  const currentExperiment: Experiment | undefined = experiments?.find(
    (e: Experiment) => e.id === selectedExperimentId
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary">
              <FlaskConical className="h-6 w-6 text-primary" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">MLflow Experiment Tracking</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Track parameters, step-wise metrics, artifact repositories, and compare multi-run performance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              refetchExperiments();
              refetchRuns();
            }}
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
            title="Refresh runs"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-all shadow-sm"
          >
            <Plus className="h-4 w-4" />
            <span>New Experiment</span>
          </button>
        </div>
      </div>

      {/* Workspace & Experiment Selector Banner */}
      <div className="bg-white rounded-xl border border-border p-4 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Project Workspace
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => {
              setSelectedProjectId(e.target.value);
              setSelectedRunIds([]);
            }}
            disabled={projectsLoading}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          >
            {projects.map((p: Project) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Experiment Workspace
          </label>
          <select
            value={selectedExperimentId}
            onChange={(e) => {
              setSelectedExperimentId(e.target.value);
              setSelectedRunIds([]);
            }}
            disabled={experimentsLoading || !experiments || experiments.length === 0}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          >
            {experiments?.map((e: Experiment) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.run_count} runs)
              </option>
            ))}
            {(!experiments || experiments.length === 0) && (
              <option value="">No experiments created</option>
            )}
          </select>
        </div>

        <div className="flex items-center justify-between md:justify-end gap-3 pt-4 md:pt-0">
          {currentExperiment && (
            <div className="text-right">
              <span className="text-[11px] text-slate-400 font-mono block">
                ID: {currentExperiment.mlflow_experiment_id?.slice(0, 12)}...
              </span>
              <span className="text-xs font-semibold text-slate-700">
                {runs?.length || 0} Total Runs Logged
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Studio Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-border">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('runs')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'runs'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>Runs Explorer ({runs?.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('compare')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'compare'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <GitCompare className="h-4 w-4" />
            <span>Compare Runs ({selectedRunIds.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('learning_curves')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'learning_curves'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Metric Progression</span>
          </button>
        </div>

        {selectedRunIds.length >= 2 && activeTab !== 'compare' && (
          <button
            onClick={() => setActiveTab('compare')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-xs font-semibold rounded-lg hover:bg-primary/20 transition-colors"
          >
            <GitCompare className="h-3.5 w-3.5" />
            <span>Compare {selectedRunIds.length} Selected Runs</span>
          </button>
        )}
      </div>

      {/* Tab 1: Runs Table View */}
      {activeTab === 'runs' && (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          {runsLoading ? (
            <div className="p-12 text-center text-sm text-slate-500">
              <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading MLflow runs...
            </div>
          ) : runs && runs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 w-10">
                      <input
                        type="checkbox"
                        checked={selectedRunIds.length === runs.length && runs.length > 0}
                        onChange={handleSelectAllRuns}
                        className="rounded accent-primary"
                      />
                    </th>
                    <th className="py-3 px-4">Run Name</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Algorithm</th>
                    <th className="py-3 px-4">Accuracy / Score</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4">Artifacts</th>
                    <th className="py-3 px-4">Logged At</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {runs.map((r: RunDetail) => {
                    const isSelected = selectedRunIds.includes(r.run_id);
                    const algo = (r.parameters?.algorithm as string) || 'Model';
                    const score =
                      r.metrics?.accuracy !== undefined
                        ? `${(r.metrics.accuracy * 100).toFixed(1)}%`
                        : r.metrics?.r2_score !== undefined
                        ? r.metrics.r2_score.toFixed(4)
                        : Object.values(r.metrics)[0]?.toFixed(4) || '—';

                    return (
                      <tr
                        key={r.run_id}
                        className={`hover:bg-slate-50 transition-colors ${
                          isSelected ? 'bg-primary/5' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleToggleRunSelection(r.run_id)}
                            className="rounded accent-primary"
                          />
                        </td>
                        <td className="py-3 px-4">
                          <button
                            onClick={() => setInspectedRunId(r.run_id)}
                            className="font-bold text-slate-900 hover:text-primary transition-colors flex items-center gap-1.5"
                          >
                            <span>{r.run_name}</span>
                            <ChevronRight className="h-3 w-3 text-slate-400" />
                          </button>
                          <span className="font-mono text-[10px] text-slate-400 block">
                            {r.run_id.slice(0, 8)}...
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              r.status === 'FINISHED'
                                ? 'bg-emerald-100 text-emerald-800'
                                : r.status === 'RUNNING'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {r.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-700 capitalize">
                          {algo.replace(/_/g, ' ')}
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-primary">{score}</td>
                        <td className="py-3 px-4 text-slate-500 font-mono">
                          {r.duration_ms ? `${r.duration_ms} ms` : '—'}
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          <span className="flex items-center gap-1">
                            <FolderArchive className="h-3.5 w-3.5 text-slate-400" />
                            {r.artifacts?.length || 0} files
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-500">
                          {new Date(r.started_at).toLocaleString([], {
                            dateStyle: 'short',
                            timeStyle: 'short',
                          })}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setInspectedRunId(r.run_id)}
                            className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition-colors"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center">
              <FlaskConical className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No MLflow Runs in this Experiment</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                Train a model in the ML Training Studio or initialize a run to log parameters, metrics, and model artifacts.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Run Comparison Matrix */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          {selectedRunIds.length < 2 ? (
            <div className="bg-white rounded-xl border border-border p-12 text-center shadow-sm">
              <GitCompare className="h-10 w-10 text-primary/40 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">Select at least 2 runs to compare</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                Return to the Runs Explorer tab and select two or more runs using checkboxes to compare parameters and metrics.
              </p>
              <button
                onClick={() => setActiveTab('runs')}
                className="mt-4 px-4 py-2 text-xs font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
              >
                Go to Runs Explorer
              </button>
            </div>
          ) : comparisonLoading ? (
            <div className="p-12 text-center text-sm text-slate-500 bg-white rounded-xl border border-border">
              <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Generating side-by-side comparison...
            </div>
          ) : comparisonData ? (
            <div className="space-y-6">
              {/* Metric Benchmarking Chart */}
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm space-y-4">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
                  <BarChart2 className="h-4 w-4 text-primary" />
                  <span>Metric Benchmarking Comparison</span>
                </h3>

                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={comparisonData.runs.map((r) => ({
                        name: r.run_name,
                        ...r.metrics,
                      }))}
                      margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis dataKey="name" stroke="#64748B" fontSize={12} />
                      <YAxis stroke="#64748B" fontSize={12} />
                      <Tooltip />
                      {comparisonData.all_metrics.slice(0, 4).map((m, idx) => {
                        const colors = ['#2563EB', '#8B5CF6', '#10B981', '#F59E0B'];
                        return (
                          <Bar
                            key={m}
                            dataKey={m}
                            fill={colors[idx % colors.length]}
                            radius={[4, 4, 0, 0]}
                          />
                        );
                      })}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Parameter Differences Table */}
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm space-y-4">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span>Differing Hyperparameters & Configurations</span>
                </h3>

                {comparisonData.differing_parameters.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs text-left border border-slate-200">
                      <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-2.5 px-3 border-r border-slate-200">Parameter</th>
                          {comparisonData.runs.map((r) => (
                            <th key={r.run_id} className="py-2.5 px-3 border-r border-slate-200 font-bold">
                              {r.run_name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {comparisonData.differing_parameters.map((paramKey) => (
                          <tr key={paramKey} className="hover:bg-slate-50">
                            <td className="py-2 px-3 font-mono font-bold text-slate-800 bg-slate-50 border-r border-slate-200">
                              {paramKey}
                            </td>
                            {comparisonData.runs.map((r) => (
                              <td
                                key={r.run_id}
                                className="py-2 px-3 font-mono text-primary font-semibold border-r border-slate-200"
                              >
                                {String(r.parameters[paramKey] ?? '—')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">All evaluated runs shared identical hyperparameters.</p>
                )}
              </div>

              {/* Metric Matrix Table */}
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm space-y-4">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
                  <Activity className="h-4 w-4 text-primary" />
                  <span>Complete Metric Matrix</span>
                </h3>

                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs text-left border border-slate-200">
                    <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3 border-r border-slate-200">Metric</th>
                        {comparisonData.runs.map((r) => (
                          <th key={r.run_id} className="py-2.5 px-3 border-r border-slate-200 font-bold">
                            {r.run_name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {comparisonData.all_metrics.map((mKey) => (
                        <tr key={mKey} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-mono font-bold text-slate-800 bg-slate-50 border-r border-slate-200 uppercase">
                            {mKey}
                          </td>
                          {comparisonData.runs.map((r) => {
                            const val = r.metrics[mKey];
                            return (
                              <td
                                key={r.run_id}
                                className="py-2 px-3 font-mono font-bold text-slate-900 border-r border-slate-200"
                              >
                                {val !== undefined && val !== null ? val.toFixed(4) : '—'}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Tab 3: Learning Curves / Step Progression */}
      {activeTab === 'learning_curves' && (
        <div className="bg-white rounded-xl border border-border p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <span>Step-wise Metric Convergence</span>
            </h3>

            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-600">Metric:</label>
              <select
                value={selectedMetricKey}
                onChange={(e) => setSelectedMetricKey(e.target.value)}
                className="px-2.5 py-1 text-xs rounded border border-slate-300"
              >
                <option value="accuracy">Accuracy</option>
                <option value="f1_score">F1 Score</option>
                <option value="train_loss">Train Loss</option>
                <option value="r2_score">R2 Score</option>
              </select>
            </div>
          </div>

          {metricHistory && metricHistory.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metricHistory} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="step" stroke="#64748B" fontSize={12} label={{ value: 'Step / Epoch', position: 'insideBottom', offset: -5 }} />
                  <YAxis stroke="#64748B" fontSize={12} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-500">
              No step-wise convergence points recorded for metric &quot;{selectedMetricKey}&quot; in the selected run.
            </div>
          )}
        </div>
      )}

      {/* Run Inspector Drawer */}
      {inspectedRunId && inspectedRun && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-white w-full max-w-xl h-full shadow-2xl p-6 overflow-y-auto space-y-6 animate-in slide-in-from-right duration-300">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-2.5">
                <span className="p-2 rounded-lg bg-primary/10 text-primary">
                  <FlaskConical className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{inspectedRun.run_name}</h3>
                  <p className="text-xs font-mono text-slate-400">ID: {inspectedRun.run_id}</p>
                </div>
              </div>
              <button
                onClick={() => setInspectedRunId(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Run Status & Timing */}
            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-500 block">Status</span>
                <span className="font-bold text-emerald-600">{inspectedRun.status}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Duration</span>
                <span className="font-mono text-slate-800">
                  {inspectedRun.duration_ms ? `${inspectedRun.duration_ms} ms` : '—'}
                </span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500 block">Started</span>
                <span className="text-slate-700">{new Date(inspectedRun.started_at).toLocaleString()}</span>
              </div>
            </div>

            {/* Hyperparameters */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-900">Hyperparameters & Config</h4>
              <div className="bg-slate-50 rounded-xl border border-slate-200 divide-y divide-slate-200 overflow-hidden text-xs">
                {Object.entries(inspectedRun.parameters).map(([k, v]) => (
                  <div key={k} className="flex justify-between p-2.5">
                    <span className="font-mono text-slate-600">{k}</span>
                    <span className="font-mono font-bold text-slate-900">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Metrics */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-900">Evaluated Metrics</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(inspectedRun.metrics).map(([k, v]) => (
                  <div key={k} className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <span className="text-slate-500 font-mono block uppercase">{k}</span>
                    <span className="text-base font-bold text-primary">{v.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Artifact Repository */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <FolderArchive className="h-4 w-4 text-primary" />
                <span>Logged Artifacts</span>
              </h4>
              <div className="bg-slate-50 rounded-xl border border-slate-200 divide-y divide-slate-200 overflow-hidden text-xs">
                {inspectedRun.artifacts.length > 0 ? (
                  inspectedRun.artifacts.map((a) => (
                    <div key={a.path} className="flex items-center justify-between p-2.5">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-slate-400" />
                        <span className="font-mono text-slate-800">{a.path}</span>
                      </div>
                      <span className="text-slate-400 font-mono text-[11px]">
                        {(a.file_size_bytes / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="p-3 text-slate-400 text-center">No artifacts logged in this run.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Experiment Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-slate-900">Create MLflow Experiment</h3>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {createError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {createError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Experiment Name
              </label>
              <input
                type="text"
                value={newExpName}
                onChange={(e) => setNewExpName(e.target.value)}
                placeholder="e.g. Random Forest Hyperparameter Sweep"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!newExpName.trim() || createExpMutation.isPending}
                onClick={() => createExpMutation.mutate(newExpName.trim())}
                className="px-4 py-2 text-xs font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                {createExpMutation.isPending ? 'Creating...' : 'Create Experiment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
