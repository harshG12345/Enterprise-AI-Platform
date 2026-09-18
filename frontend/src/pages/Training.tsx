import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  BrainCircuit,
  Play,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Award,
  BarChart3,
  GitBranch,
  Table,
  LineChart as LineChartIcon,
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
  ScatterChart,
  Scatter,
} from 'recharts';

import { trainingApi } from '../api/training';
import { getProjects } from '../api/projects';
import { getDatasets, getDataset } from '../api/datasets';
import { Project } from '../types/project';
import { Dataset, ColumnMeta } from '../types/dataset';
import {
  AlgorithmInfo,
  TrainingJobCreate,
  TrainingJobDetailResponse,
  TaskType,
} from '../types/training';

export const Training: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    searchParams.get('projectId') || ''
  );
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    searchParams.get('datasetId') || ''
  );
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [taskType, setTaskType] = useState<TaskType>('classification');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('random_forest_classifier');
  const [hyperparameters, setHyperparameters] = useState<Record<string, number | string>>({
    n_estimators: 25,
    max_depth: 6,
    min_samples_split: 2,
  });
  const [cvSplits, setCvSplits] = useState<number>(5);
  const [stratify, setStratify] = useState<boolean>(true);
  const [modelName, setModelName] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'metrics' | 'cv' | 'importance' | 'matrix' | 'roc' | 'artifact'>('metrics');

  const [trainingResult, setTrainingResult] = useState<TrainingJobDetailResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [trainingElapsed, setTrainingElapsed] = useState<number>(0);

  // 1. Fetch Projects
  const { data: projectsRes, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({ page: 1, page_size: 100 }),
  });
  const projectsData = projectsRes?.data;

  // 2. Fetch Datasets
  const { data: datasetsRes, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets', selectedProjectId],
    queryFn: () => getDatasets({ project_id: selectedProjectId || undefined, page: 1, page_size: 100 }),
    enabled: true,
  });
  const datasetsData = datasetsRes?.data;

  // 3. Fetch Selected Dataset Details (for column schema)
  const { data: datasetDetailRes } = useQuery({
    queryKey: ['dataset', selectedDatasetId],
    queryFn: () => getDataset(selectedDatasetId),
    enabled: !!selectedDatasetId,
  });
  const datasetDetail = datasetDetailRes?.data;

  // 4. Fetch Algorithms Catalog
  const { data: algorithms, isLoading: algorithmsLoading } = useQuery({
    queryKey: ['algorithms'],
    queryFn: trainingApi.getAlgorithms,
  });

  // 5. Fetch Training Jobs History
  const { data: trainingJobs, refetch: refetchJobs } = useQuery({
    queryKey: ['trainingJobs', selectedProjectId],
    queryFn: () => trainingApi.getTrainingJobs(selectedProjectId || undefined),
  });

  // Auto-select first project & dataset if available
  useEffect(() => {
    if (!selectedProjectId && projectsData?.items && projectsData.items.length > 0) {
      setSelectedProjectId(projectsData.items[0].id);
    }
  }, [projectsData, selectedProjectId]);

  useEffect(() => {
    if (!selectedDatasetId && datasetsData?.items && datasetsData.items.length > 0) {
      setSelectedDatasetId(datasetsData.items[0].id);
    }
  }, [datasetsData, selectedDatasetId]);

  // Auto-detect target column & columns
  useEffect(() => {
    if (datasetDetail?.schema_metadata?.columns) {
      const cols = datasetDetail.schema_metadata.columns;
      if (cols.length > 0 && !targetColumn) {
        // default to last column
        const lastCol = cols[cols.length - 1];
        setTargetColumn(lastCol.name);
        if (lastCol.inferred_type === 'numeric') {
          setTaskType(lastCol.unique_count && lastCol.unique_count <= 10 ? 'classification' : 'regression');
        } else {
          setTaskType('classification');
        }
      }
    }
  }, [datasetDetail, targetColumn]);

  // Update default hyperparameters when algorithm changes
  const handleAlgorithmChange = (algoKey: string) => {
    setSelectedAlgorithm(algoKey);
    const algoObj = algorithms?.find((a) => a.algorithm === algoKey);
    if (algoObj) {
      setHyperparameters({ ...algoObj.default_hyperparameters });
      setTaskType(algoObj.task_type);
    }
  };

  // Training Mutation
  const trainMutation = useMutation({
    mutationFn: (payload: TrainingJobCreate) => trainingApi.trainModel(payload),
    onSuccess: (data) => {
      setTrainingResult(data);
      setErrorMessage(null);
      refetchJobs();
      queryClient.invalidateQueries({ queryKey: ['trainingJobs'] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error?.message || err.message || 'Training failed';
      setErrorMessage(msg);
    },
  });

  // Elapsed training timer
  useEffect(() => {
    let interval: any;
    if (trainMutation.isPending) {
      setTrainingElapsed(0);
      interval = setInterval(() => {
        setTrainingElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      setTrainingElapsed(0);
    }
    return () => clearInterval(interval);
  }, [trainMutation.isPending]);

  const handleStartTraining = () => {
    if (!selectedProjectId || !selectedDatasetId || !targetColumn) {
      setErrorMessage('Please select a project, dataset, and target column.');
      return;
    }

    setErrorMessage(null);
    const payload: TrainingJobCreate = {
      project_id: selectedProjectId,
      dataset_id: selectedDatasetId,
      target_column: targetColumn,
      task_type: taskType,
      algorithm: selectedAlgorithm,
      hyperparameters,
      cv_config: {
        n_splits: cvSplits,
        stratify,
        shuffle: true,
        random_state: 42,
      },
      model_name: modelName || undefined,
    };

    trainMutation.mutate(payload);
  };

  const currentAlgoObj: AlgorithmInfo | undefined = algorithms?.find(
    (a) => a.algorithm === selectedAlgorithm
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary">
              <BrainCircuit className="h-6 w-6 text-primary" />
            </span>
            <h1 className="text-2xl font-bold text-slate-900">ML Training Studio</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Train, evaluate, and benchmark high-performance models with K-Fold Cross Validation and zero data leakage.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleStartTraining}
            disabled={trainMutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white font-medium hover:bg-primary/90 transition-all disabled:opacity-50 shadow-sm"
          >
            {trainMutation.isPending ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Training Model ({trainingElapsed}s)...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                <span>Train Model</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* In-Progress Training Alert */}
      {trainMutation.isPending && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin flex-shrink-0" />
            <div>
              <p className="font-semibold text-sm">Model Training & Cross-Validation in Progress...</p>
              <p className="text-xs text-blue-700">Fitting estimator folds, computing statistical metrics, and generating diagnostics ({trainingElapsed}s elapsed).</p>
            </div>
          </div>
          <span className="px-2.5 py-1 text-xs font-mono font-medium rounded-full bg-blue-100 text-blue-800 border border-blue-300">
            {trainingElapsed}s
          </span>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Training Error</p>
            <p>{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Configuration & Hyperparameter Setup */}
        <div className="lg:col-span-1 space-y-6">
          {/* Workspace & Dataset Selection */}
          <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
              <Layers className="h-4 w-4 text-primary" />
              <span>1. Dataset & Target</span>
            </h2>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Project Workspace
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                disabled={projectsLoading}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                {projectsData?.items?.map((p: Project) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Dataset File
              </label>
              <select
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                disabled={datasetsLoading}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                {datasetsData?.items?.map((d: Dataset) => (
                  <option key={d.id} value={d.id}>
                    {d.filename} ({d.row_count} rows)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Target Column (y)
              </label>
              <select
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                {datasetDetail?.schema_metadata?.columns?.map((c: ColumnMeta) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.inferred_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Problem Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setTaskType('classification');
                    if (currentAlgoObj?.task_type === 'regression') {
                      setSelectedAlgorithm('random_forest_classifier');
                    }
                  }}
                  className={`py-2 px-3 text-xs font-semibold rounded-lg border text-center transition-all ${
                    taskType === 'classification'
                      ? 'bg-primary/10 border-primary text-primary'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  Classification
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTaskType('regression');
                    if (currentAlgoObj?.task_type === 'classification') {
                      setSelectedAlgorithm('random_forest_regressor');
                    }
                  }}
                  className={`py-2 px-3 text-xs font-semibold rounded-lg border text-center transition-all ${
                    taskType === 'regression'
                      ? 'bg-primary/10 border-primary text-primary'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  Regression
                </button>
              </div>
            </div>
          </div>

          {/* Algorithm & Hyperparameter Tuning */}
          <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
              <Sparkles className="h-4 w-4 text-primary" />
              <span>2. Model Algorithm & Params</span>
            </h2>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                ML Algorithm
              </label>
              <select
                value={selectedAlgorithm}
                onChange={(e) => handleAlgorithmChange(e.target.value)}
                disabled={algorithmsLoading}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                <optgroup label="Classification Algorithms">
                  {algorithms
                    ?.filter((a) => a.task_type === 'classification')
                    .map((a) => (
                      <option key={a.algorithm} value={a.algorithm}>
                        {a.name}
                      </option>
                    ))}
                </optgroup>
                <optgroup label="Regression Algorithms">
                  {algorithms
                    ?.filter((a) => a.task_type === 'regression')
                    .map((a) => (
                      <option key={a.algorithm} value={a.algorithm}>
                        {a.name}
                      </option>
                    ))}
                </optgroup>
              </select>
              {currentAlgoObj && (
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  {currentAlgoObj.description}
                </p>
              )}
            </div>

            {/* Dynamic Hyperparameter Sliders */}
            <div className="space-y-3 pt-2">
              <span className="text-xs font-bold text-slate-900 uppercase tracking-wider block">
                Hyperparameter Tuning
              </span>
              {currentAlgoObj?.hyperparameter_schema &&
                Object.entries(currentAlgoObj.hyperparameter_schema).map(([key, schema]) => (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-mono text-slate-700">{key}</span>
                      <span className="font-bold text-primary">
                        {hyperparameters[key] ?? schema.default}
                      </span>
                    </div>
                    {schema.min !== undefined && schema.max !== undefined ? (
                      <input
                        type="range"
                        min={schema.min}
                        max={schema.max}
                        step={schema.type === 'float' ? 0.01 : 1}
                        value={Number(hyperparameters[key] ?? schema.default)}
                        onChange={(e) =>
                          setHyperparameters({
                            ...hyperparameters,
                            [key]:
                              schema.type === 'float'
                                ? parseFloat(e.target.value)
                                : parseInt(e.target.value, 10),
                          })
                        }
                        className="w-full accent-primary h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                      />
                    ) : (
                      <input
                        type="text"
                        value={String(hyperparameters[key] ?? schema.default)}
                        onChange={(e) =>
                          setHyperparameters({ ...hyperparameters, [key]: e.target.value })
                        }
                        className="w-full px-2.5 py-1.5 text-xs rounded border border-slate-300"
                      />
                    )}
                  </div>
                ))}
            </div>
          </div>

          {/* Validation & Naming Settings */}
          <div className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
              <GitBranch className="h-4 w-4 text-primary" />
              <span>3. Cross Validation & Identity</span>
            </h2>

            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-slate-700 uppercase tracking-wider">
                  K-Fold Splits (k)
                </span>
                <span className="font-bold text-primary">{cvSplits} Folds</span>
              </div>
              <input
                type="range"
                min={2}
                max={10}
                value={cvSplits}
                onChange={(e) => setCvSplits(parseInt(e.target.value, 10))}
                className="w-full accent-primary h-1.5 bg-slate-200 rounded-lg cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-xs font-medium text-slate-700">Stratified Fold Partitioning</span>
              <input
                type="checkbox"
                checked={stratify}
                onChange={(e) => setStratify(e.target.checked)}
                className="rounded accent-primary h-4 w-4"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Model Name Tag
              </label>
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g. churn-rf-v1.0"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Training Dashboard & Diagnostic Evaluation */}
        <div className="lg:col-span-2 space-y-6">
          {trainingResult ? (
            <div className="space-y-6">
              {/* Top Banner with Performance Summary */}
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
                  <div className="flex items-center gap-3">
                    <span className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200">
                      <CheckCircle2 className="h-6 w-6" />
                    </span>
                    <div>
                      <h3 className="text-lg font-bold text-slate-900">
                        {trainingResult.algorithm.replace(/_/g, ' ').toUpperCase()} Trained
                      </h3>
                      <p className="text-xs text-slate-500">
                        Evaluated with {trainingResult.cv_summary?.folds.length || cvSplits}-Fold CV in{' '}
                        <span className="font-semibold text-slate-700">
                          {trainingResult.training_duration_ms} ms
                        </span>
                      </p>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 self-start sm:self-center">
                    STATUS: {trainingResult.status}
                  </span>
                </div>

                {/* Metric Badges Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
                  {trainingResult.task_type === 'classification' ? (
                    <>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">Test Accuracy</span>
                        <div className="text-xl font-bold text-primary mt-1">
                          {trainingResult.test_metrics.accuracy !== undefined
                            ? `${(trainingResult.test_metrics.accuracy * 100).toFixed(1)}%`
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">Test F1-Score</span>
                        <div className="text-xl font-bold text-slate-900 mt-1">
                          {trainingResult.test_metrics.f1_score !== undefined
                            ? (trainingResult.test_metrics.f1_score * 100).toFixed(1) + '%'
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">ROC-AUC</span>
                        <div className="text-xl font-bold text-emerald-600 mt-1">
                          {trainingResult.test_metrics.roc_auc !== undefined && trainingResult.test_metrics.roc_auc !== null
                            ? `${(trainingResult.test_metrics.roc_auc * 100).toFixed(1)}%`
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">CV Mean Score</span>
                        <div className="text-xl font-bold text-violet-600 mt-1">
                          {trainingResult.cv_summary
                            ? `${(trainingResult.cv_summary.mean_val_score * 100).toFixed(1)}%`
                            : 'N/A'}
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">Test R² Score</span>
                        <div className="text-xl font-bold text-primary mt-1">
                          {trainingResult.test_metrics.r2_score !== undefined
                            ? trainingResult.test_metrics.r2_score.toFixed(4)
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">RMSE</span>
                        <div className="text-xl font-bold text-slate-900 mt-1">
                          {trainingResult.test_metrics.rmse !== undefined
                            ? trainingResult.test_metrics.rmse.toFixed(4)
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">MAE</span>
                        <div className="text-xl font-bold text-emerald-600 mt-1">
                          {trainingResult.test_metrics.mae !== undefined
                            ? trainingResult.test_metrics.mae.toFixed(4)
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <span className="text-xs text-slate-500 font-medium">CV R² Mean</span>
                        <div className="text-xl font-bold text-violet-600 mt-1">
                          {trainingResult.cv_summary
                            ? trainingResult.cv_summary.mean_val_score.toFixed(4)
                            : 'N/A'}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Diagnostic Visualizations Tabs */}
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm space-y-4">
                <div className="flex border-b border-border gap-2 overflow-x-auto pb-2">
                  <button
                    onClick={() => setActiveTab('metrics')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                      activeTab === 'metrics'
                        ? 'bg-primary text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <BarChart3 className="h-3.5 w-3.5" />
                    <span>Train vs Test Split</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('cv')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                      activeTab === 'cv'
                        ? 'bg-primary text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Activity className="h-3.5 w-3.5" />
                    <span>K-Fold Folds</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('importance')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                      activeTab === 'importance'
                        ? 'bg-primary text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Award className="h-3.5 w-3.5" />
                    <span>Feature Importance</span>
                  </button>

                  {trainingResult.task_type === 'classification' ? (
                    <>
                      <button
                        onClick={() => setActiveTab('matrix')}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                          activeTab === 'matrix'
                            ? 'bg-primary text-white'
                            : 'text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        <Table className="h-3.5 w-3.5" />
                        <span>Confusion Matrix</span>
                      </button>

                      <button
                        onClick={() => setActiveTab('roc')}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                          activeTab === 'roc'
                            ? 'bg-primary text-white'
                            : 'text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        <LineChartIcon className="h-3.5 w-3.5" />
                        <span>ROC Curve</span>
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setActiveTab('matrix')}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                        activeTab === 'matrix'
                          ? 'bg-primary text-white'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <LineChartIcon className="h-3.5 w-3.5" />
                      <span>Residuals Scatter</span>
                    </button>
                  )}

                  <button
                    onClick={() => setActiveTab('artifact')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                      activeTab === 'artifact'
                        ? 'bg-primary text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Artifact</span>
                  </button>
                </div>

                {/* Tab 1: Train vs Test Comparison */}
                {activeTab === 'metrics' && (
                  <div className="space-y-4 pt-2">
                    <h4 className="text-sm font-bold text-slate-800">Train vs Test Generalization Performance</h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={
                            trainingResult.task_type === 'classification'
                              ? [
                                  {
                                    name: 'Accuracy',
                                    Train: Number((trainingResult.train_metrics.accuracy || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.accuracy || 0).toFixed(4)),
                                  },
                                  {
                                    name: 'Precision',
                                    Train: Number((trainingResult.train_metrics.precision || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.precision || 0).toFixed(4)),
                                  },
                                  {
                                    name: 'Recall',
                                    Train: Number((trainingResult.train_metrics.recall || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.recall || 0).toFixed(4)),
                                  },
                                  {
                                    name: 'F1 Score',
                                    Train: Number((trainingResult.train_metrics.f1_score || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.f1_score || 0).toFixed(4)),
                                  },
                                ]
                              : [
                                  {
                                    name: 'R2 Score',
                                    Train: Number((trainingResult.train_metrics.r2_score || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.r2_score || 0).toFixed(4)),
                                  },
                                  {
                                    name: 'RMSE',
                                    Train: Number((trainingResult.train_metrics.rmse || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.rmse || 0).toFixed(4)),
                                  },
                                  {
                                    name: 'MAE',
                                    Train: Number((trainingResult.train_metrics.mae || 0).toFixed(4)),
                                    Test: Number((trainingResult.test_metrics.mae || 0).toFixed(4)),
                                  },
                                ]
                          }
                          margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                          <XAxis dataKey="name" stroke="#64748B" fontSize={12} />
                          <YAxis stroke="#64748B" fontSize={12} />
                          <Tooltip />
                          <Bar dataKey="Train" fill="#93C5FD" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="Test" fill="#2563EB" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Tab 2: K-Fold CV Results */}
                {activeTab === 'cv' && (
                  <div className="space-y-4 pt-2">
                    <div className="flex justify-between items-center">
                      <h4 className="text-sm font-bold text-slate-800">
                        Out-of-Fold Cross Validation ({trainingResult.cv_summary?.folds.length} Folds)
                      </h4>
                      {trainingResult.cv_summary && (
                        <span className="text-xs font-mono text-slate-600 bg-slate-100 px-2.5 py-1 rounded">
                          μ = {trainingResult.cv_summary.mean_val_score.toFixed(4)} ±{' '}
                          {trainingResult.cv_summary.std_val_score.toFixed(4)}
                        </span>
                      )}
                    </div>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={trainingResult.cv_summary?.folds.map((f) => ({
                            name: `Fold ${f.fold}`,
                            ValidationScore: f.val_score,
                          }))}
                          margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                          <XAxis dataKey="name" stroke="#64748B" fontSize={12} />
                          <YAxis stroke="#64748B" fontSize={12} />
                          <Tooltip />
                          <Bar dataKey="ValidationScore" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Tab 3: Feature Importances */}
                {activeTab === 'importance' && (
                  <div className="space-y-4 pt-2">
                    <h4 className="text-sm font-bold text-slate-800">Top Predictive Features</h4>
                    {trainingResult.feature_importances.length > 0 ? (
                      <div className="space-y-2">
                        {trainingResult.feature_importances.map((item) => (
                          <div key={item.feature} className="space-y-1">
                            <div className="flex justify-between text-xs font-medium">
                              <span className="text-slate-700 font-mono">
                                #{item.rank} {item.feature}
                              </span>
                              <span className="text-primary font-bold">
                                {(item.importance * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                              <div
                                className="bg-primary h-full rounded-full transition-all duration-500"
                                style={{ width: `${Math.max(item.importance * 100, 2)}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500">
                        Feature importances are not directly emitted by this linear/instance-based model.
                      </p>
                    )}
                  </div>
                )}

                {/* Tab 4: Confusion Matrix / Residuals */}
                {activeTab === 'matrix' && (
                  <div className="space-y-4 pt-2">
                    {trainingResult.task_type === 'classification' && trainingResult.confusion_matrix ? (
                      <div>
                        <h4 className="text-sm font-bold text-slate-800 mb-3">Confusion Matrix (Normalized)</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full border border-slate-200 text-xs">
                            <thead className="bg-slate-50 text-slate-600">
                              <tr>
                                <th className="p-2.5 border border-slate-200">Actual \ Predicted</th>
                                {trainingResult.confusion_matrix.labels.map((lbl) => (
                                  <th key={lbl} className="p-2.5 border border-slate-200 text-center font-bold">
                                    Pred {lbl}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {trainingResult.confusion_matrix.matrix.map((row, rIdx) => (
                                <tr key={rIdx}>
                                  <td className="p-2.5 border border-slate-200 font-bold bg-slate-50 text-slate-700">
                                    True {trainingResult.confusion_matrix?.labels[rIdx]}
                                  </td>
                                  {row.map((val, cIdx) => {
                                    const norm = trainingResult.confusion_matrix?.normalized_matrix[rIdx][cIdx] || 0;
                                    const isDiagonal = rIdx === cIdx;
                                    return (
                                      <td
                                        key={cIdx}
                                        className={`p-2.5 border border-slate-200 text-center font-mono ${
                                          isDiagonal ? 'bg-primary/10 text-primary font-bold' : 'text-slate-700'
                                        }`}
                                      >
                                        <div>{val}</div>
                                        <div className="text-[10px] text-slate-400">({(norm * 100).toFixed(0)}%)</div>
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <h4 className="text-sm font-bold text-slate-800 mb-3">
                          Residuals Distribution (Predicted vs Actual)
                        </h4>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                              <XAxis dataKey="predicted" name="Predicted" stroke="#64748B" fontSize={12} />
                              <YAxis dataKey="actual" name="Actual" stroke="#64748B" fontSize={12} />
                              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                              <Scatter
                                name="Predictions"
                                data={trainingResult.residuals_sample}
                                fill="#2563EB"
                              />
                            </ScatterChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 5: ROC Curve */}
                {activeTab === 'roc' && trainingResult.roc_curve.length > 0 && (
                  <div className="space-y-4 pt-2">
                    <h4 className="text-sm font-bold text-slate-800">Receiver Operating Characteristic (ROC)</h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trainingResult.roc_curve} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                          <XAxis dataKey="x" name="False Positive Rate" stroke="#64748B" fontSize={12} domain={[0, 1]} />
                          <YAxis dataKey="y" name="True Positive Rate" stroke="#64748B" fontSize={12} domain={[0, 1]} />
                          <Tooltip />
                          <Line type="monotone" dataKey="y" stroke="#2563EB" strokeWidth={2} dot={{ r: 3 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Tab 6: Artifact Details */}
                {activeTab === 'artifact' && (
                  <div className="space-y-3 pt-2 text-xs">
                    <h4 className="text-sm font-bold text-slate-800">Model Deployment & Artifact</h4>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 font-mono space-y-1.5 text-slate-700">
                      <div><span className="text-slate-400">Model UUID:</span> {trainingResult.model_id}</div>
                      <div><span className="text-slate-400">Job UUID:</span> {trainingResult.id}</div>
                      <div><span className="text-slate-400">Artifact Path:</span> {trainingResult.artifact_path}</div>
                      <div><span className="text-slate-400">Created At:</span> {trainingResult.created_at}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Empty Placeholder State */
            <div className="bg-white rounded-xl border border-border p-12 text-center shadow-sm flex flex-col items-center justify-center min-h-[400px]">
              <div className="p-4 rounded-2xl bg-primary/10 text-primary mb-4">
                <BrainCircuit className="h-10 w-10 text-primary" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">No Model Trained Yet</h3>
              <p className="text-sm text-slate-500 max-w-md mt-2">
                Configure your dataset, select a target variable and machine learning algorithm on the left, and click
                &quot;Train Model&quot; to execute cross validation and generate visual diagnostics.
              </p>
            </div>
          )}

          {/* Historical Training Jobs Table */}
          <div className="bg-white rounded-xl border border-border p-6 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-border pb-3">
              <Clock className="h-4 w-4 text-primary" />
              <span>Historical Training Jobs</span>
            </h3>

            {trainingJobs && trainingJobs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Job ID</th>
                      <th className="py-2.5 px-3">Dataset</th>
                      <th className="py-2.5 px-3">Target</th>
                      <th className="py-2.5 px-3">Type</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Started</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {trainingJobs.map((j) => (
                      <tr key={j.id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-mono text-slate-700">{j.id.slice(0, 8)}...</td>
                        <td className="py-2.5 px-3 text-slate-800">{j.dataset_name || 'Dataset'}</td>
                        <td className="py-2.5 px-3 font-mono text-primary font-medium">{j.target_column}</td>
                        <td className="py-2.5 px-3 capitalize text-slate-600">{j.task_type}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              j.status === 'SUCCESS'
                                ? 'bg-emerald-100 text-emerald-800'
                                : j.status === 'RUNNING'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {j.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-500">
                          {new Date(j.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-slate-500">No training jobs recorded in this workspace.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
