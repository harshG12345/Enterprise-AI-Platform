import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Boxes,
  ArrowLeft,
  ShieldCheck,
  Sparkles,
  Archive,
  Download,
  RotateCcw,
  AlertTriangle,
  GitBranch,
  Layers,
  FileCode,
  Activity,
  History,
  TrendingUp,
  Sliders,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

import { modelsApi } from '../api/models';
import { ModelLifecycleStatus } from '../types/models';

export const ModelDetails: React.FC = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'metrics' | 'features' | 'hyperparameters' | 'audit'>('metrics');

  // Promotion Modal State
  const [isPromoteModalOpen, setIsPromoteModalOpen] = useState<boolean>(false);
  const [targetStatus, setTargetStatus] = useState<ModelLifecycleStatus>('STAGING');
  const [promotionNotes, setPromotionNotes] = useState<string>('');
  const [promotionError, setPromotionError] = useState<string | null>(null);

  // Fetch Model Details
  const {
    data: model,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['modelDetails', modelId],
    queryFn: () => modelsApi.getModelDetails(modelId!),
    enabled: !!modelId,
  });


  // Promote Mutation
  const promoteMutation = useMutation({
    mutationFn: ({ status, notes }: { status: ModelLifecycleStatus; notes?: string }) =>
      modelsApi.promoteModel(modelId!, { status, notes }),
    onSuccess: () => {
      setIsPromoteModalOpen(false);
      setPromotionNotes('');
      setPromotionError(null);
      queryClient.invalidateQueries({ queryKey: ['modelDetails', modelId] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (err: any) => {
      setPromotionError(err.response?.data?.error?.message || err.message || 'Promotion failed');
    },
  });

  // Rollback Mutation
  const rollbackMutation = useMutation({
    mutationFn: () => modelsApi.rollbackModel(modelId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelDetails', modelId] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  // Archive Mutation
  const archiveMutation = useMutation({
    mutationFn: () => modelsApi.archiveModel(modelId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelDetails', modelId] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="h-8 w-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium text-slate-500">Loading model governance telemetry...</p>
      </div>
    );
  }

  if (error || !model) {
    return (
      <div className="bg-white rounded-xl border border-rose-200 p-8 text-center max-w-lg mx-auto mt-12 space-y-4">
        <AlertTriangle className="h-10 w-10 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Model Not Found</h2>
        <p className="text-xs text-slate-500">
          The requested model version could not be found or you do not have permission to inspect it.
        </p>
        <Link
          to="/models"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-lg hover:bg-slate-800"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Model Registry</span>
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: ModelLifecycleStatus) => {
    switch (status) {
      case 'PRODUCTION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            Production Champion
          </span>
        );
      case 'STAGING':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 shadow-sm">
            <Sparkles className="h-4 w-4 text-amber-600" />
            Staging Candidate
          </span>
        );
      case 'DEVELOPMENT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-300 shadow-sm">
            <Boxes className="h-4 w-4 text-blue-600" />
            Development Run
          </span>
        );
      case 'ARCHIVED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-300">
            <Archive className="h-4 w-4 text-slate-500" />
            Archived Version
          </span>
        );
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100">{status}</span>;
    }
  };

  const trainMetrics = model.metrics?.train || {};
  const testMetrics = model.metrics?.test || {};
  const cvMetrics = model.metrics?.cv;
  const isClassification = model.task_type === 'classification';

  // Feature Importance Chart Data
  const featureChartData = (model.feature_importances || [])
    .slice(0, 15)
    .map((fi) => ({
      name: fi.feature,
      importance: Number((fi.importance * 100).toFixed(2)),
    }))
    .reverse();

  return (
    <div className="space-y-6 pb-16">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <Link
            to="/models"
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">{model.name}</h1>
              <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs font-mono font-bold">
                {model.version}
              </span>
              {getStatusBadge(model.status)}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Project: <span className="font-semibold text-slate-700">{model.project_name || 'General Project'}</span>
              {' • '}
              Framework: <span className="font-mono text-slate-700">{model.framework}</span>
              {' • '}
              Registered: {new Date(model.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {model.status !== 'ARCHIVED' && (
            <button
              onClick={() => {
                setTargetStatus(
                  model.status === 'DEVELOPMENT'
                    ? 'STAGING'
                    : model.status === 'STAGING'
                    ? 'PRODUCTION'
                    : 'STAGING'
                );
                setIsPromoteModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary/90 transition-all shadow-sm"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Promote Stage</span>
            </button>
          )}

          {model.status !== 'DEVELOPMENT' && model.status !== 'ARCHIVED' && (
            <button
              onClick={() => {
                if (confirm('Roll back model to DEVELOPMENT stage?')) {
                  rollbackMutation.mutate();
                }
              }}
              disabled={rollbackMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors"
              title="Rollback model to Development"
            >
              <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
              <span>Rollback</span>
            </button>
          )}

          {model.status !== 'ARCHIVED' && (
            <button
              onClick={() => {
                if (confirm('Archive this model version?')) {
                  archiveMutation.mutate();
                }
              }}
              disabled={archiveMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors"
              title="Archive model"
            >
              <Archive className="h-3.5 w-3.5 text-slate-500" />
              <span>Archive</span>
            </button>
          )}

          <a
            href={modelsApi.downloadArtifactUrl(model.id)}
            download
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-primary/20 bg-primary/5 text-primary text-xs font-semibold hover:bg-primary/10 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download .pkl</span>
          </a>
        </div>
      </div>

      {/* Primary KPI Header Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {isClassification ? (
          <>
            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Test Accuracy
              </span>
              <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                {testMetrics.accuracy !== undefined ? `${(testMetrics.accuracy * 100).toFixed(2)}%` : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                Train: {trainMetrics.accuracy !== undefined ? `${(trainMetrics.accuracy * 100).toFixed(2)}%` : '—'}
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                F1 Score (Weighted)
              </span>
              <div className="text-2xl font-bold font-mono text-primary mt-1">
                {testMetrics.f1_score !== undefined ? testMetrics.f1_score.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                Precision: {testMetrics.precision !== undefined ? testMetrics.precision.toFixed(3) : '—'} • Recall: {testMetrics.recall !== undefined ? testMetrics.recall.toFixed(3) : '—'}
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                ROC-AUC Score
              </span>
              <div className="text-2xl font-bold font-mono text-indigo-600 mt-1">
                {testMetrics.roc_auc !== undefined ? testMetrics.roc_auc.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                Log Loss: {testMetrics.log_loss !== undefined ? testMetrics.log_loss.toFixed(4) : '—'}
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Cross-Validation (Mean ± Std)
              </span>
              <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
                {cvMetrics?.mean_val_score !== undefined
                  ? `${cvMetrics.mean_val_score.toFixed(4)}`
                  : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                ± {cvMetrics?.std_val_score !== undefined ? cvMetrics.std_val_score.toFixed(4) : '0.000'} across {cvMetrics?.folds?.length || 5} folds
              </span>
            </div>
          </>
        ) : (
          <>
            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                R² Determination Score
              </span>
              <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                {testMetrics.r2_score !== undefined ? testMetrics.r2_score.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                Train R²: {trainMetrics.r2_score !== undefined ? trainMetrics.r2_score.toFixed(4) : '—'}
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Mean Absolute Error (MAE)
              </span>
              <div className="text-2xl font-bold font-mono text-primary mt-1">
                {testMetrics.mae !== undefined ? testMetrics.mae.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                MSE: {testMetrics.mse !== undefined ? testMetrics.mse.toFixed(4) : '—'}
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Root Mean Squared Error (RMSE)
              </span>
              <div className="text-2xl font-bold font-mono text-indigo-600 mt-1">
                {testMetrics.rmse !== undefined ? testMetrics.rmse.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                MAPE: {testMetrics.mape !== undefined ? `${(testMetrics.mape * 100).toFixed(2)}%` : '—'}
              </span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Cross-Validation (Mean ± Std)
              </span>
              <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
                {cvMetrics?.mean_val_score !== undefined ? cvMetrics.mean_val_score.toFixed(4) : '—'}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">
                ± {cvMetrics?.std_val_score !== undefined ? cvMetrics.std_val_score.toFixed(4) : '0.000'} across {cvMetrics?.folds?.length || 5} folds
              </span>
            </div>
          </>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'metrics'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Activity className="h-4 w-4" />
          <span>Evaluation Diagnostics</span>
        </button>

        <button
          onClick={() => setActiveTab('features')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'features'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <TrendingUp className="h-4 w-4" />
          <span>Feature Importance ({model.feature_importances?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('hyperparameters')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'hyperparameters'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Sliders className="h-4 w-4" />
          <span>Hyperparameters & Specs</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'audit'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <History className="h-4 w-4" />
          <span>Governance Audit Trail ({model.audit_history?.length || 0})</span>
        </button>
      </div>

      {/* TAB 1: Evaluation Diagnostics */}
      {activeTab === 'metrics' && (
        <div className="space-y-6">
          {/* Detailed Metric Split Table */}
          <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <span>Dataset Split Performance Benchmarks</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4">Split Partition</th>
                    {isClassification ? (
                      <>
                        <th className="py-2.5 px-4">Accuracy</th>
                        <th className="py-2.5 px-4">Precision</th>
                        <th className="py-2.5 px-4">Recall</th>
                        <th className="py-2.5 px-4">F1 Score</th>
                        <th className="py-2.5 px-4">ROC-AUC</th>
                        <th className="py-2.5 px-4">Log Loss</th>
                      </>
                    ) : (
                      <>
                        <th className="py-2.5 px-4">R² Score</th>
                        <th className="py-2.5 px-4">MAE</th>
                        <th className="py-2.5 px-4">MSE</th>
                        <th className="py-2.5 px-4">RMSE</th>
                        <th className="py-2.5 px-4">MAPE</th>
                        <th className="py-2.5 px-4">Explained Var</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="py-2.5 px-4 font-semibold text-slate-800">Training Holdout</td>
                    {isClassification ? (
                      <>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.accuracy !== undefined ? (trainMetrics.accuracy * 100).toFixed(2) + '%' : '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.precision?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.recall?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.f1_score?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.roc_auc?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.log_loss?.toFixed(4) || '—'}</td>
                      </>
                    ) : (
                      <>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.r2_score?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.mae?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.mse?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.rmse?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.mape ? (trainMetrics.mape * 100).toFixed(2) + '%' : '—'}</td>
                        <td className="py-2.5 px-4 font-mono">{trainMetrics.explained_variance?.toFixed(4) || '—'}</td>
                      </>
                    )}
                  </tr>
                  <tr className="bg-primary/5">
                    <td className="py-2.5 px-4 font-bold text-primary">Test Generalization</td>
                    {isClassification ? (
                      <>
                        <td className="py-2.5 px-4 font-mono font-bold text-emerald-600">{testMetrics.accuracy !== undefined ? (testMetrics.accuracy * 100).toFixed(2) + '%' : '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.precision?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.recall?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-bold text-primary">{testMetrics.f1_score?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.roc_auc?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.log_loss?.toFixed(4) || '—'}</td>
                      </>
                    ) : (
                      <>
                        <td className="py-2.5 px-4 font-mono font-bold text-emerald-600">{testMetrics.r2_score?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-bold text-primary">{testMetrics.mae?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.mse?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.rmse?.toFixed(4) || '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.mape ? (testMetrics.mape * 100).toFixed(2) + '%' : '—'}</td>
                        <td className="py-2.5 px-4 font-mono font-semibold">{testMetrics.explained_variance?.toFixed(4) || '—'}</td>
                      </>
                    )}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Confusion Matrix (Classification only) */}
          {isClassification && model.confusion_matrix && (
            <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="h-4 w-4 text-primary" />
                <span>Confusion Matrix (Test Evaluation)</span>
              </h3>
              <p className="text-xs text-slate-500">
                Ground truth classes vs model predicted classes on holdout validation.
              </p>

              <div className="overflow-x-auto">
                <table className="text-xs border-collapse">
                  <thead>
                    <tr>
                      <th className="p-2 border border-slate-200 bg-slate-50 text-slate-500 font-normal">
                        Actual \ Predicted
                      </th>
                      {model.confusion_matrix.labels.map((label, idx) => (
                        <th key={idx} className="p-2 border border-slate-200 bg-slate-100 font-bold text-slate-800 text-center">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {model.confusion_matrix.matrix.map((row, rIdx) => (
                      <tr key={rIdx}>
                        <th className="p-2 border border-slate-200 bg-slate-100 font-bold text-slate-800 text-left">
                          {model.confusion_matrix?.labels[rIdx] || `Class ${rIdx}`}
                        </th>
                        {row.map((val, cIdx) => {
                          const isDiagonal = rIdx === cIdx;
                          return (
                            <td
                              key={cIdx}
                              className={`p-3 border border-slate-200 text-center font-mono font-bold ${
                                isDiagonal
                                  ? 'bg-emerald-50 text-emerald-800'
                                  : val > 0
                                  ? 'bg-rose-50/50 text-rose-700'
                                  : 'text-slate-400'
                              }`}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cross-Validation Folds Breakdown */}
          {cvMetrics && cvMetrics.folds && cvMetrics.folds.length > 0 && (
            <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-primary" />
                <span>$K$-Fold Cross-Validation Scores</span>
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {cvMetrics.folds.map((f) => (
                  <div key={f.fold} className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-center">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase block">
                      Fold {f.fold}
                    </span>
                    <span className="text-base font-bold font-mono text-primary block mt-1">
                      {f.val_score.toFixed(4)}
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      Train: {f.train_score.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Feature Importance */}
      {activeTab === 'features' && (
        <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <span>Feature Relative Importance Attribution</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Relative contribution of each independent feature to the model's prediction decisions.
            </p>
          </div>

          {featureChartData.length > 0 ? (
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={featureChartData}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 100, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                  <XAxis
                    type="number"
                    unit="%"
                    tick={{ fontSize: 11, fill: '#64748B' }}
                    domain={[0, 'dataMax + 5']}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 11, fill: '#334155' }}
                    width={90}
                  />
                  <Tooltip
                    formatter={(val: number) => [`${val}%`, 'Importance']}
                    contentStyle={{ backgroundColor: '#0F172A', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="importance" fill="#4F46E5" radius={[0, 4, 4, 0]}>
                    {featureChartData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={index >= featureChartData.length - 3 ? '#6366F1' : '#818CF8'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400 text-xs">
              No feature importances logged for this algorithm structure.
            </div>
          )}

          {/* Table list of features */}
          <div className="border-t border-border pt-4">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3">
              Full Feature Ranking Table ({model.feature_importances?.length || 0} Features)
            </h4>
            <div className="max-h-60 overflow-y-auto">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold sticky top-0">
                  <tr>
                    <th className="py-2 px-3 w-16">Rank</th>
                    <th className="py-2 px-3">Feature Name</th>
                    <th className="py-2 px-3 text-right">Relative Weight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(model.feature_importances || []).map((fi) => (
                    <tr key={fi.feature} className="hover:bg-slate-50">
                      <td className="py-2 px-3 font-mono font-bold text-slate-500">#{fi.rank}</td>
                      <td className="py-2 px-3 font-medium text-slate-800">{fi.feature}</td>
                      <td className="py-2 px-3 font-mono text-right text-primary font-semibold">
                        {(fi.importance * 100).toFixed(3)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Hyperparameters & Specs */}
      {activeTab === 'hyperparameters' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="h-4 w-4 text-primary" />
              <span>Trained Hyperparameters</span>
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2 px-3">Parameter</th>
                    <th className="py-2 px-3">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {Object.entries(model.hyperparameters || {}).map(([k, v]) => (
                    <tr key={k}>
                      <td className="py-2 px-3 font-mono text-slate-700">{k}</td>
                      <td className="py-2 px-3 font-mono font-semibold text-slate-900">
                        {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileCode className="h-4 w-4 text-primary" />
              <span>Model Artifact Specifications</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Model Unique ID:</span>
                  <span className="font-mono text-slate-800">{model.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Target Column:</span>
                  <span className="font-mono font-semibold text-primary">{model.target_column || 'target'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Input Feature Count:</span>
                  <span className="font-mono text-slate-800">{model.feature_names?.length || 0} columns</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Artifact File Path:</span>
                  <span className="font-mono text-slate-600 truncate max-w-xs">{model.artifact_path}</span>
                </div>
                {model.mlflow_run_id && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">MLflow Run ID:</span>
                    <span className="font-mono text-indigo-600">{model.mlflow_run_id}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Governance Audit Trail */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <History className="h-4 w-4 text-primary" />
              <span>Model Promotion & Lifecycle Audit History</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Immutable enterprise audit log of all promotion state changes, authorizations, and rationale.
            </p>
          </div>

          {model.audit_history && model.audit_history.length > 0 ? (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {model.audit_history.map((item, idx) => (
                <div key={item.id || idx} className="relative group">
                  <div className="absolute -left-[27px] top-1.5 h-3.5 w-3.5 rounded-full border-2 border-white bg-primary shadow-sm" />
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 capitalize">
                          {item.action.replace(/_/g, ' ')}
                        </span>
                        {item.metadata?.target_status && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary">
                            → {item.metadata.target_status}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>

                    {item.metadata?.notes && (
                      <p className="text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-slate-100 italic">
                        "{item.metadata.notes}"
                      </p>
                    )}

                    <div className="text-[10px] text-slate-400 flex items-center gap-2">
                      <span>User ID: {item.user_id}</span>
                      {item.metadata?.previous_status && (
                        <span>• Previous: {item.metadata.previous_status}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400 text-xs">
              No audit transition logs recorded yet.
            </div>
          )}
        </div>
      )}

      {/* Promotion Modal */}
      {isPromoteModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Promote Model Lifecycle</h3>
                <p className="text-xs text-slate-500 mt-0.5">{model.name} ({model.version})</p>
              </div>
              <button
                onClick={() => setIsPromoteModalOpen(false)}
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
                  Target Stage
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
                    Promoting to <strong>PRODUCTION</strong> will automatically demote any existing production champion for this project slot to <strong>STAGING</strong>.
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
                  placeholder="State the validation benchmark results justifying this promotion..."
                  rows={3}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setIsPromoteModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={promoteMutation.isPending}
                onClick={() =>
                  promoteMutation.mutate({
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
