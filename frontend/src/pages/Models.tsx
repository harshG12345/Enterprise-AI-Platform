import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Boxes,
  Trophy,
  ShieldCheck,
  AlertTriangle,
  Archive,
  ChevronRight,
  GitCompare,
  Sparkles,
  RefreshCw,
  Search,
} from 'lucide-react';

import { modelsApi } from '../api/models';
import { getProjects } from '../api/projects';
import { Project } from '../types/project';
import {
  ModelLeaderboardItem,
  ModelLifecycleStatus,
  ModelResponse,
} from '../types/models';

export const Models: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();


  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    searchParams.get('projectId') || ''
  );
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [taskTypeFilter, setTaskTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'registry' | 'leaderboard'>('registry');

  // Promotion Modal State
  const [promotingModel, setPromotingModel] = useState<ModelResponse | null>(null);
  const [targetStatus, setTargetStatus] = useState<ModelLifecycleStatus>('STAGING');
  const [promotionNotes, setPromotionNotes] = useState<string>('');
  const [promotionError, setPromotionError] = useState<string | null>(null);

  // Selected Models for Comparison
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);

  // 1. Fetch Projects
  const { data: projectsRes, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({ page: 1, page_size: 100 }),
  });
  const projects = projectsRes?.data?.items || [];

  // 2. Fetch Models
  const {
    data: models,
    isLoading: modelsLoading,
    refetch: refetchModels,
  } = useQuery({
    queryKey: ['models', selectedProjectId, taskTypeFilter, statusFilter],
    queryFn: () =>
      modelsApi.listModels({
        project_id: selectedProjectId || undefined,
        task_type: taskTypeFilter !== 'ALL' ? taskTypeFilter : undefined,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
      }),
  });

  // 3. Fetch Leaderboard
  const {
    data: leaderboard,
    isLoading: leaderboardLoading,
    refetch: refetchLeaderboard,
  } = useQuery({
    queryKey: ['leaderboard', selectedProjectId, taskTypeFilter],
    queryFn: () =>
      modelsApi.getLeaderboard({
        project_id: selectedProjectId || undefined,
        task_type: taskTypeFilter !== 'ALL' ? taskTypeFilter : undefined,
      }),
  });

  // Promotion Mutation
  const promoteMutation = useMutation({
    mutationFn: ({ modelId, status, notes }: { modelId: string; status: ModelLifecycleStatus; notes?: string }) =>
      modelsApi.promoteModel(modelId, { status, notes }),
    onSuccess: () => {
      setPromotingModel(null);
      setPromotionNotes('');
      setPromotionError(null);
      queryClient.invalidateQueries({ queryKey: ['models'] });
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] });
    },
    onError: (err: any) => {
      setPromotionError(err.response?.data?.error?.message || err.message || 'Promotion failed');
    },
  });

  const handleToggleSelectModel = (id: string) => {
    setSelectedModelIds((prev) =>
      prev.includes(id) ? prev.filter((mId) => mId !== id) : [...prev, id]
    );
  };

  const filteredModels = (models || []).filter((m) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      m.name.toLowerCase().includes(q) ||
      m.version.toLowerCase().includes(q) ||
      m.task_type.toLowerCase().includes(q) ||
      (m.project_name && m.project_name.toLowerCase().includes(q))
    );
  });

  const getStatusBadge = (status: ModelLifecycleStatus) => {
    switch (status) {
      case 'PRODUCTION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            Production
          </span>
        );
      case 'STAGING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
            <Sparkles className="h-3.5 w-3.5 text-amber-600" />
            Staging
          </span>
        );
      case 'DEVELOPMENT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
            <Boxes className="h-3.5 w-3.5 text-blue-600" />
            Development
          </span>
        );
      case 'ARCHIVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
            <Archive className="h-3.5 w-3.5 text-slate-500" />
            Archived
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary">
              <Boxes className="h-6 w-6 text-primary" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">Model Registry & Governance</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Enterprise model catalog, versioning, performance leaderboards, and promotion audit governance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              refetchModels();
              refetchLeaderboard();
            }}
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
            title="Refresh models"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <Link
            to="/training"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-all shadow-sm"
          >
            <Sparkles className="h-4 w-4" />
            <span>Train New Model</span>
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-border p-4 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Project Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Project Filter
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            disabled={projectsLoading}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          >
            <option value="">All Projects</option>
            {projects.map((p: Project) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Task Type Filter */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Task Type
          </label>
          <select
            value={taskTypeFilter}
            onChange={(e) => setTaskTypeFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          >
            <option value="ALL">All Tasks</option>
            <option value="classification">Classification</option>
            <option value="regression">Regression</option>
          </select>
        </div>

        {/* Status Stage Filter */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Lifecycle Stage
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          >
            <option value="ALL">All Stages</option>
            <option value="PRODUCTION">Production</option>
            <option value="STAGING">Staging</option>
            <option value="DEVELOPMENT">Development</option>
            <option value="ARCHIVED">Archived</option>
          </select>
        </div>

        {/* Search */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Search Models
          </label>
          <div className="relative">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center justify-between border-b border-border">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('registry')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'registry'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Boxes className="h-4 w-4" />
            <span>Registered Models ({filteredModels.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'leaderboard'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Trophy className="h-4 w-4" />
            <span>Leaderboard Benchmark ({leaderboard?.length || 0})</span>
          </button>
        </div>

        {selectedModelIds.length >= 2 && (
          <button
            onClick={() => {
              // Trigger comparison view or navigate
              alert(`Comparing ${selectedModelIds.length} models`);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
          >
            <GitCompare className="h-3.5 w-3.5" />
            <span>Compare {selectedModelIds.length} Models</span>
          </button>
        )}
      </div>

      {/* View 1: Registered Models Explorer */}
      {activeTab === 'registry' && (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          {modelsLoading ? (
            <div className="p-12 text-center text-sm text-slate-500">
              <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading registered models...
            </div>
          ) : filteredModels.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 w-10">
                      <input
                        type="checkbox"
                        checked={
                          selectedModelIds.length === filteredModels.length &&
                          filteredModels.length > 0
                        }
                        onChange={() => {
                          if (selectedModelIds.length === filteredModels.length) {
                            setSelectedModelIds([]);
                          } else {
                            setSelectedModelIds(filteredModels.map((m) => m.id));
                          }
                        }}
                        className="rounded accent-primary"
                      />
                    </th>
                    <th className="py-3 px-4">Model Name & Version</th>
                    <th className="py-3 px-4">Stage</th>
                    <th className="py-3 px-4">Task</th>
                    <th className="py-3 px-4">Test Accuracy / Score</th>
                    <th className="py-3 px-4">Project</th>
                    <th className="py-3 px-4">Registered</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredModels.map((m: ModelResponse) => {
                    const isSelected = selectedModelIds.includes(m.id);
                    const testMetrics = m.metrics?.test || {};
                    const score =
                      testMetrics.accuracy !== undefined
                        ? `${(testMetrics.accuracy * 100).toFixed(1)}%`
                        : testMetrics.r2_score !== undefined
                        ? testMetrics.r2_score.toFixed(4)
                        : '—';

                    return (
                      <tr
                        key={m.id}
                        className={`hover:bg-slate-50 transition-colors ${
                          isSelected ? 'bg-primary/5' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleToggleSelectModel(m.id)}
                            className="rounded accent-primary"
                          />
                        </td>
                        <td className="py-3 px-4">
                          <Link
                            to={`/models/${m.id}`}
                            className="font-bold text-slate-900 hover:text-primary transition-colors flex items-center gap-1.5"
                          >
                            <span>{m.name}</span>
                            <span className="px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded text-[10px] font-mono">
                              {m.version}
                            </span>
                            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                          </Link>
                          <span className="font-mono text-[10px] text-slate-400 block">
                            ID: {m.id.slice(0, 8)}...
                          </span>
                        </td>
                        <td className="py-3 px-4">{getStatusBadge(m.status)}</td>
                        <td className="py-3 px-4 font-medium text-slate-700 capitalize">
                          {m.task_type}
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-primary">{score}</td>
                        <td className="py-3 px-4 text-slate-600 font-medium">
                          {m.project_name || '—'}
                        </td>
                        <td className="py-3 px-4 text-slate-500">
                          {new Date(m.created_at).toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => {
                                setPromotingModel(m);
                                setTargetStatus(
                                  m.status === 'DEVELOPMENT'
                                    ? 'STAGING'
                                    : m.status === 'STAGING'
                                    ? 'PRODUCTION'
                                    : 'DEVELOPMENT'
                                );
                              }}
                              className="px-2.5 py-1 text-[11px] font-semibold text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors"
                            >
                              Promote
                            </button>
                            <Link
                              to={`/models/${m.id}`}
                              className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition-colors"
                            >
                              Details
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center">
              <Boxes className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No Models Found in Registry</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                Train a model in the ML Training Studio to automatically register versions, track metrics, and promote through lifecycle stages.
              </p>
              <Link
                to="/training"
                className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Go to ML Training Studio</span>
              </Link>
            </div>
          )}
        </div>
      )}

      {/* View 2: Performance Leaderboard */}
      {activeTab === 'leaderboard' && (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden space-y-4">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Trophy className="h-4 w-4 text-amber-500" />
                <span>Model Generalization Leaderboard</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Models ranked by primary test set validation score.
              </p>
            </div>
          </div>

          {leaderboardLoading ? (
            <div className="p-12 text-center text-sm text-slate-500">
              <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Calculating leaderboard rankings...
            </div>
          ) : leaderboard && leaderboard.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 w-16 text-center">Rank</th>
                    <th className="py-3 px-4">Model Name</th>
                    <th className="py-3 px-4">Stage</th>
                    <th className="py-3 px-4">Task</th>
                    <th className="py-3 px-4">Primary Score</th>
                    <th className="py-3 px-4">Secondary Metric</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {leaderboard.map((item: ModelLeaderboardItem) => (
                    <tr
                      key={item.id}
                      className={`hover:bg-slate-50 transition-colors ${
                        item.rank === 1 ? 'bg-amber-50/40' : ''
                      }`}
                    >
                      <td className="py-3 px-4 text-center">
                        {item.rank === 1 ? (
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-amber-100 text-amber-800 font-bold text-xs border border-amber-300">
                            🥇
                          </span>
                        ) : item.rank === 2 ? (
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-slate-100 text-slate-800 font-bold text-xs border border-slate-300">
                            🥈
                          </span>
                        ) : item.rank === 3 ? (
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-orange-100 text-orange-800 font-bold text-xs border border-orange-300">
                            🥉
                          </span>
                        ) : (
                          <span className="font-bold text-slate-500 font-mono">#{item.rank}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        <Link
                          to={`/models/${item.id}`}
                          className="hover:text-primary transition-colors flex items-center gap-1.5"
                        >
                          <span>{item.name}</span>
                          <span className="px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded text-[10px] font-mono">
                            {item.version}
                          </span>
                        </Link>
                      </td>
                      <td className="py-3 px-4">{getStatusBadge(item.status)}</td>
                      <td className="py-3 px-4 font-medium text-slate-700 capitalize">
                        {item.task_type}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-primary text-sm">
                            {item.primary_metric_name === 'accuracy'
                              ? `${(item.primary_metric_value * 100).toFixed(1)}%`
                              : item.primary_metric_value.toFixed(4)}
                          </span>
                          <span className="text-[10px] uppercase font-mono text-slate-400">
                            ({item.primary_metric_name})
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-600">
                        {item.secondary_metric_value !== null && item.secondary_metric_value !== undefined
                          ? `${item.secondary_metric_value.toFixed(4)} (${item.secondary_metric_name})`
                          : '—'}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-500">
                        {item.training_duration_ms ? `${item.training_duration_ms} ms` : '—'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          to={`/models/${item.id}`}
                          className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition-colors"
                        >
                          Inspect
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 text-xs">
              No ranked models available for the selected filters.
            </div>
          )}
        </div>
      )}

      {/* Promotion Modal */}
      {promotingModel && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Promote Model Stage</h3>
                <p className="text-xs text-slate-500 mt-0.5">{promotingModel.name} ({promotingModel.version})</p>
              </div>
              <button
                onClick={() => setPromotingModel(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                ✕
              </button>
            </div>

            {promotionError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {promotionError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Target Lifecycle Stage
                </label>
                <select
                  value={targetStatus}
                  onChange={(e) => setTargetStatus(e.target.value as ModelLifecycleStatus)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  <option value="DEVELOPMENT">Development</option>
                  <option value="STAGING">Staging</option>
                  <option value="PRODUCTION">Production</option>
                  <option value="ARCHIVED">Archived</option>
                </select>
              </div>

              {targetStatus === 'PRODUCTION' && (
                <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-lg flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span>
                    Promoting to <strong>PRODUCTION</strong> will automatically demote any currently active production model for this project slot to <strong>STAGING</strong>.
                  </span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Audit Governance Rationale (Required)
                </label>
                <textarea
                  value={promotionNotes}
                  onChange={(e) => setPromotionNotes(e.target.value)}
                  placeholder="e.g. Model passed F1 benchmark and validated against production holdout set."
                  rows={3}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setPromotingModel(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={promoteMutation.isPending}
                onClick={() =>
                  promoteMutation.mutate({
                    modelId: promotingModel.id,
                    status: targetStatus,
                    notes: promotionNotes,
                  })
                }
                className="px-4 py-2 text-xs font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                {promoteMutation.isPending ? 'Promoting...' : `Promote to ${targetStatus}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
