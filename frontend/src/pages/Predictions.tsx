import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Zap,
  Cpu,
  Layers,
  Upload,
  FileText,
  History,
  CheckCircle2,
  AlertTriangle,
  Download,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  Database,
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

import { predictionsApi } from '../api/predictions';
import { modelsApi } from '../api/models';
import { getProjects } from '../api/projects';
import { datasetsApi } from '../api/datasets';
import { jobsApi } from '../api/jobs';
import { Project } from '../types/project';
import { Dataset } from '../types/dataset';
import { ModelResponse } from '../types/models';
import {
  RealtimePredictionResponse,
  PredictionHistoryItem,
} from '../types/prediction';

export const Predictions: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    searchParams.get('projectId') || ''
  );
  const [selectedModelId, setSelectedModelId] = useState<string>(
    searchParams.get('modelId') || ''
  );
  const [activeTab, setActiveTab] = useState<'realtime' | 'batch' | 'history'>('realtime');


  // Real-time Form State
  const [featureInputs, setFeatureInputs] = useState<Record<string, string>>({});
  const [realtimeResult, setRealtimeResult] = useState<RealtimePredictionResponse | null>(null);
  const [realtimeError, setRealtimeError] = useState<string | null>(null);

  // Batch Prediction State
  const [batchMode, setBatchMode] = useState<'dataset' | 'upload'>('upload');
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);

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

  // Auto-select first model or production champion
  useEffect(() => {
    if (models && models.length > 0 && !selectedModelId) {
      const prodModel = models.find((m) => m.status === 'PRODUCTION');
      setSelectedModelId(prodModel ? prodModel.id : models[0].id);
    }
  }, [models, selectedModelId]);

  // 3. Fetch Selected Model Details (for expected feature names)
  const { data: modelDetails, isLoading: modelDetailsLoading } = useQuery({
    queryKey: ['modelDetails', selectedModelId],
    queryFn: () => modelsApi.getModelDetails(selectedModelId),
    enabled: !!selectedModelId,
  });

  // Initialize input fields when model details load
  useEffect(() => {
    if (modelDetails && modelDetails.feature_names) {
      const initial: Record<string, string> = {};
      modelDetails.feature_names.forEach((feat) => {
        initial[feat] = '';
      });
      setFeatureInputs(initial);
      setRealtimeResult(null);
      setRealtimeError(null);
    }
  }, [modelDetails]);

  // 4. Fetch Datasets for Batch Mode
  const { data: datasetsRes } = useQuery({
    queryKey: ['datasets', selectedProjectId],
    queryFn: () => datasetsApi.getDatasets({ project_id: selectedProjectId || undefined }),
  });
  const datasets = datasetsRes?.data?.items || [];

  // 5. Fetch Prediction History & Stats
  const {
    data: history,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['predictionHistory', selectedProjectId, selectedModelId],
    queryFn: () =>
      predictionsApi.getPredictionHistory({
        project_id: selectedProjectId || undefined,
        model_id: selectedModelId || undefined,
        limit: 50,
      }),
  });

  const { data: stats } = useQuery({
    queryKey: ['predictionStats', selectedProjectId],
    queryFn: () => predictionsApi.getPredictionStats(selectedProjectId || undefined),
  });

  // 6. Poll Batch Job Status
  const { data: batchJob } = useQuery({
    queryKey: ['batchJob', batchJobId],
    queryFn: () => jobsApi.getJobStatus(batchJobId!),
    enabled: !!batchJobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'PENDING' || status === 'RUNNING' ? 1000 : false;
    },
  });

  // Real-time Mutation
  const realtimeMutation = useMutation({
    mutationFn: (payload: { model_id: string; features: Record<string, any> }) =>
      predictionsApi.predictRealtime(payload),
    onSuccess: (data) => {
      setRealtimeResult(data);
      setRealtimeError(null);
      queryClient.invalidateQueries({ queryKey: ['predictionHistory'] });
      queryClient.invalidateQueries({ queryKey: ['predictionStats'] });
    },
    onError: (err: any) => {
      setRealtimeError(err.response?.data?.error?.message || err.message || 'Inference failed');
    },
  });

  // Batch Launch Mutation
  const batchLaunchMutation = useMutation({
    mutationFn: async () => {
      setBatchError(null);
      if (batchMode === 'dataset') {
        if (!selectedDatasetId) throw new Error('Please select a dataset');
        return predictionsApi.launchBatchPrediction({
          model_id: selectedModelId,
          project_id: selectedProjectId || (modelDetails?.project_id as string),
          dataset_id: selectedDatasetId,
        });
      } else {
        if (!batchFile) throw new Error('Please select a CSV or XLSX file');
        return predictionsApi.launchBatchPredictionUpload(
          selectedModelId,
          selectedProjectId || (modelDetails?.project_id as string),
          batchFile
        );
      }
    },
    onSuccess: (data) => {
      setBatchJobId(data.job_id);
    },
    onError: (err: any) => {
      setBatchError(err.response?.data?.error?.message || err.message || 'Batch launch failed');
    },
  });

  const handlePopulateSampleData = () => {
    if (!modelDetails?.feature_names) return;
    const sample: Record<string, string> = {};
    modelDetails.feature_names.forEach((feat, idx) => {
      sample[feat] = (Math.random() * 10.0 + (idx + 1) * 2).toFixed(2);
    });
    setFeatureInputs(sample);
  };

  const handleResetForm = () => {
    if (!modelDetails?.feature_names) return;
    const empty: Record<string, string> = {};
    modelDetails.feature_names.forEach((feat) => {
      empty[feat] = '';
    });
    setFeatureInputs(empty);
    setRealtimeResult(null);
    setRealtimeError(null);
  };

  const handleRunRealtimePredict = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId) return;

    const numericFeatures: Record<string, number> = {};
    for (const [k, v] of Object.entries(featureInputs)) {
      numericFeatures[k] = parseFloat(v) || 0.0;
    }

    realtimeMutation.mutate({
      model_id: selectedModelId,
      features: numericFeatures,
    });
  };

  const probabilityChartData = (realtimeResult?.probabilities || []).map((p) => ({
    class: p.class_name,
    probability: Number((p.probability * 100).toFixed(1)),
  }));

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary">
              <Zap className="h-6 w-6 text-primary" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">Inference & Prediction Studio</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Real-time low-latency REST model inference and high-throughput background batch predictions.
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
              <option value="">Select Model for Inference...</option>
              {(models || []).map((m: ModelResponse) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.version}) — {m.status}
                </option>
              ))}
            </select>
          </div>

          <Link
            to="/models"
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
            title="Manage in Model Registry"
          >
            <Layers className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* Model Context Header Bar */}
      {modelDetails && (
        <div className="bg-slate-900 text-white rounded-xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-white/10 text-white">
              <Cpu className="h-5 w-5 text-primary-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">{modelDetails.name}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/20">
                  {modelDetails.version}
                </span>
                {modelDetails.status === 'PRODUCTION' ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    <ShieldCheck className="h-3 w-3" />
                    Production Champion
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40">
                    {modelDetails.status}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-300 mt-0.5">
                Task: <strong className="capitalize">{modelDetails.task_type}</strong> • Target:{' '}
                <strong className="font-mono text-primary-300">{modelDetails.target_column || 'target'}</strong> •
                Features: <strong>{modelDetails.feature_names?.length || 0} required columns</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-slate-300">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Avg Latency</span>
              <span className="text-emerald-400 font-bold">~6.8 ms</span>
            </div>
            <div className="border-l border-slate-700 pl-4">
              <span className="text-slate-400 block text-[10px] uppercase">Framework</span>
              <span>{modelDetails.framework}</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-border">
        <button
          onClick={() => setActiveTab('realtime')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'realtime'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Zap className="h-4 w-4" />
          <span>Real-Time Inference</span>
        </button>

        <button
          onClick={() => setActiveTab('batch')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'batch'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Upload className="h-4 w-4" />
          <span>Batch Prediction Engine</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'history'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <History className="h-4 w-4" />
          <span>Inference Logs & Telemetry</span>
        </button>
      </div>

      {/* TAB 1: Real-Time Single Record Inference */}
      {activeTab === 'realtime' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Dynamic Feature Input Form */}
          <div className="lg:col-span-6 bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <SlidersIcon className="h-4 w-4 text-primary" />
                  <span>Input Feature Vector</span>
                </h3>
                <p className="text-xs text-slate-500">Provide input feature attributes matching model schema.</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handlePopulateSampleData}
                  className="px-2.5 py-1 text-[11px] font-semibold text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors"
                >
                  Populate Sample
                </button>
                <button
                  type="button"
                  onClick={handleResetForm}
                  className="p-1 text-slate-400 hover:text-slate-600 rounded"
                  title="Reset form"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {realtimeError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500 flex-shrink-0 mt-0.5" />
                <span>{realtimeError}</span>
              </div>
            )}

            {modelDetailsLoading ? (
              <div className="p-8 text-center text-xs text-slate-500">
                <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                Loading model feature schema...
              </div>
            ) : modelDetails && modelDetails.feature_names && modelDetails.feature_names.length > 0 ? (
              <form onSubmit={handleRunRealtimePredict} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[420px] overflow-y-auto pr-1">
                  {modelDetails.feature_names.map((feat) => (
                    <div key={feat} className="space-y-1">
                      <label className="block text-xs font-semibold text-slate-700 font-mono truncate" title={feat}>
                        {feat}
                      </label>
                      <input
                        type="number"
                        step="any"
                        required
                        value={featureInputs[feat] ?? ''}
                        onChange={(e) =>
                          setFeatureInputs((prev) => ({
                            ...prev,
                            [feat]: e.target.value,
                          }))
                        }
                        placeholder="0.0"
                        className="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                      />
                    </div>
                  ))}
                </div>

                <div className="pt-3 border-t border-border flex justify-end">
                  <button
                    type="submit"
                    disabled={realtimeMutation.isPending}
                    className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary/90 transition-all shadow-sm disabled:opacity-50"
                  >
                    {realtimeMutation.isPending ? (
                      <>
                        <div className="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Inferring...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4" />
                        <span>Run Real-Time Prediction</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              <div className="p-8 text-center text-xs text-slate-400">
                Please select a model from the top dropdown to load feature inputs.
              </div>
            )}
          </div>

          {/* Right Column: Prediction Outcome & Confidence Telemetry */}
          <div className="lg:col-span-6 space-y-6">
            {realtimeResult ? (
              <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-5 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Inference Outcome
                    </span>
                    <h3 className="text-base font-bold text-slate-900">
                      Model Output: <span className="text-primary">{realtimeResult.model_name}</span>
                    </h3>
                  </div>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    ⚡ {realtimeResult.latency_ms} ms
                  </span>
                </div>

                {/* Outcome Display Card */}
                <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    {realtimeResult.task_type === 'classification' ? 'Predicted Class Label' : 'Predicted Target Value'}
                  </span>
                  <div className="text-3xl font-extrabold font-mono text-slate-900 tracking-tight">
                    {realtimeResult.predicted_value}
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono block">
                    Prediction ID: {realtimeResult.prediction_id}
                  </span>
                </div>

                {/* Class Probabilities Bar Chart (Classification only) */}
                {realtimeResult.probabilities && realtimeResult.probabilities.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-primary" />
                      <span>Class Confidence Distribution</span>
                    </h4>

                    <div className="h-36 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={probabilityChartData}
                          layout="vertical"
                          margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                          <XAxis
                            type="number"
                            unit="%"
                            domain={[0, 100]}
                            tick={{ fontSize: 10, fill: '#64748B' }}
                          />
                          <YAxis
                            type="category"
                            dataKey="class"
                            tick={{ fontSize: 11, fill: '#334155' }}
                          />
                          <Tooltip
                            formatter={(val: number) => [`${val}%`, 'Confidence']}
                            contentStyle={{
                              backgroundColor: '#0F172A',
                              color: '#fff',
                              borderRadius: '8px',
                              fontSize: '11px',
                            }}
                          />
                          <Bar dataKey="probability" fill="#4F46E5" radius={[0, 4, 4, 0]}>
                            {probabilityChartData.map((_, idx) => (
                              <Cell
                                key={`cell-${idx}`}
                                fill={idx === 0 ? '#4F46E5' : '#818CF8'}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center space-y-3">
                <Zap className="h-10 w-10 text-slate-300 mx-auto" />
                <h3 className="text-sm font-bold text-slate-700">Awaiting Real-Time Input</h3>
                <p className="text-xs text-slate-400 max-w-xs mx-auto">
                  Populate the feature values on the left and click <strong>Run Real-Time Prediction</strong> to execute instant model evaluation.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Batch Inference Studio */}
      {activeTab === 'batch' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Launch Configuration */}
          <div className="lg:col-span-6 bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Upload className="h-4 w-4 text-primary" />
                <span>Asynchronous Batch Prediction Setup</span>
              </h3>
              <p className="text-xs text-slate-500">
                Run high-throughput model inference across thousands of tabular records in background worker.
              </p>
            </div>

            {batchError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500 flex-shrink-0 mt-0.5" />
                <span>{batchError}</span>
              </div>
            )}

            {/* Source Selection Mode */}
            <div className="flex gap-2 border-b border-border pb-3">
              <button
                type="button"
                onClick={() => setBatchMode('upload')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  batchMode === 'upload'
                    ? 'bg-primary text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Upload CSV/XLSX
              </button>
              <button
                type="button"
                onClick={() => setBatchMode('dataset')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  batchMode === 'dataset'
                    ? 'bg-primary text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Select Workspace Dataset
              </button>
            </div>

            {batchMode === 'upload' ? (
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Upload Batch Tabular File
                </label>
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-primary/50 transition-colors">
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setBatchFile(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                    id="batch-file-input"
                  />
                  <label htmlFor="batch-file-input" className="cursor-pointer block space-y-2">
                    <FileText className="h-8 w-8 text-slate-400 mx-auto" />
                    <span className="text-xs font-semibold text-primary block">
                      {batchFile ? batchFile.name : 'Click to select CSV or XLSX file'}
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      {batchFile ? `${(batchFile.size / 1024).toFixed(1)} KB` : 'Must contain all required input feature columns'}
                    </span>
                  </label>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Workspace Dataset
                </label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  <option value="">Select registered dataset...</option>
                  {datasets.map((d: Dataset) => (
                    <option key={d.id} value={d.id}>
                      {d.filename} ({d.row_count || 0} rows)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="pt-3 border-t border-border flex justify-end">
              <button
                type="button"
                disabled={batchLaunchMutation.isPending || !selectedModelId}
                onClick={() => batchLaunchMutation.mutate()}
                className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary/90 transition-all shadow-sm disabled:opacity-50"
              >
                {batchLaunchMutation.isPending ? (
                  <>
                    <div className="h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Launching Worker...</span>
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    <span>Launch Batch Prediction</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Column: Execution Telemetry & Download Results */}
          <div className="lg:col-span-6 space-y-4">
            {batchJob ? (
              <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Batch Job Progress</h3>
                    <p className="text-[11px] font-mono text-slate-400 mt-0.5">Job ID: {batchJob.id}</p>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      batchJob.status === 'SUCCESS'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : batchJob.status === 'FAILED'
                        ? 'bg-rose-100 text-rose-800 border border-rose-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200 animate-pulse'
                    }`}
                  >
                    {batchJob.status}
                  </span>
                </div>

                {batchJob.status === 'RUNNING' || batchJob.status === 'PENDING' ? (
                  <div className="p-8 text-center space-y-3">
                    <div className="h-8 w-8 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                    <p className="text-xs font-medium text-slate-600">
                      Processing batch rows asynchronously in Celery worker...
                    </p>
                  </div>
                ) : batchJob.status === 'SUCCESS' ? (

                  <div className="space-y-4">
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3">
                      <CheckCircle2 className="h-6 w-6 text-emerald-600 flex-shrink-0" />
                      <div>
                        <span className="text-xs font-bold text-emerald-900 block">
                          Batch Prediction Completed Successfully!
                        </span>
                        <span className="text-[11px] text-emerald-700 block mt-0.5">
                          Inference results with predictions and class probabilities generated.
                        </span>
                      </div>
                    </div>

                    <a
                      href={predictionsApi.downloadBatchResultsUrl(batchJob.id)}
                      download
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 text-white text-xs font-bold rounded-xl hover:bg-slate-800 transition-colors shadow-sm"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download Result CSV File</span>
                    </a>
                  </div>
                ) : (
                  <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
                    <strong>Batch job failed:</strong> {batchJob.error_message || 'Unknown execution error'}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center space-y-3">
                <Database className="h-10 w-10 text-slate-300 mx-auto" />
                <h3 className="text-sm font-bold text-slate-700">No Active Batch Job</h3>
                <p className="text-xs text-slate-400 max-w-xs mx-auto">
                  Configure your batch input file on the left and start the asynchronous job to stream predictions.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Inference Logs & Telemetry */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          {/* Telemetry KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Total Real-Time Inferences
              </span>
              <div className="text-2xl font-bold font-mono text-primary mt-1">
                {stats?.total_predictions || 0} calls
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Average Latency
              </span>
              <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                {stats?.average_latency_ms || 0} ms
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                P95 Latency SLA
              </span>
              <div className="text-2xl font-bold font-mono text-indigo-600 mt-1">
                {stats?.p95_latency_ms || 0} ms
              </div>
            </div>
          </div>

          {/* Historical Logs Table */}
          <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden space-y-4">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Recent Prediction Events</h3>
                <p className="text-xs text-slate-500 mt-0.5">Chronological audit stream of model inference calls.</p>
              </div>
              <button
                onClick={() => refetchHistory()}
                className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
                title="Refresh logs"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>

            {historyLoading ? (
              <div className="p-12 text-center text-xs text-slate-500">
                <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                Loading prediction events...
              </div>
            ) : history && history.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider">
                    <tr>
                      <th className="py-2.5 px-4">Timestamp</th>
                      <th className="py-2.5 px-4">Model Name</th>
                      <th className="py-2.5 px-4">Input Payload</th>
                      <th className="py-2.5 px-4">Outcome</th>
                      <th className="py-2.5 px-4 text-right">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {history.map((item: PredictionHistoryItem) => (
                      <tr key={item.id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-4 text-slate-500">
                          {new Date(item.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </td>
                        <td className="py-2.5 px-4 font-sans font-semibold text-slate-800">
                          {item.model_name || 'Model'}
                        </td>
                        <td className="py-2.5 px-4 text-slate-600 max-w-xs truncate">
                          {JSON.stringify(item.input_data)}
                        </td>
                        <td className="py-2.5 px-4 font-bold text-primary">
                          {String(item.prediction?.predicted_value)}
                        </td>
                        <td className="py-2.5 px-4 text-right text-emerald-600 font-bold">
                          {item.latency_ms} ms
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400 text-xs">
                No real-time prediction events logged yet.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

function SlidersIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="4" x2="4" y1="21" y2="14" />
      <line x1="4" x2="4" y1="10" y2="3" />
      <line x1="12" x2="12" y1="21" y2="12" />
      <line x1="12" x2="12" y1="8" y2="3" />
      <line x1="20" x2="20" y1="21" y2="16" />
      <line x1="20" x2="20" y1="12" y2="3" />
      <line x1="1" x2="7" y1="14" y2="14" />
      <line x1="9" x2="15" y1="8" y2="8" />
      <line x1="17" x2="23" y1="16" y2="16" />
    </svg>
  );
}
