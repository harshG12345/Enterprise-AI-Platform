import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Database,
  Download,
  Filter,
  Layers,
  Loader2,
  Play,
  RotateCcw,
  Sliders,
  Table,
  Target,
  Wand2,
} from 'lucide-react';

import { getDataset } from '../api/datasets';
import { preprocessorApi } from '../api/preprocessor';
import {
  CategoricalEncoder,
  CategoricalFeatureConfig,
  CategoricalImputer,
  DatetimeFeatureConfig,
  NumericalFeatureConfig,
  NumericalImputer,
  NumericalPowerTransform,
  NumericalScaler,
  PreprocessingConfig,
  PreprocessingResponse,
} from '../types/preprocessor';

type Step = 'target_split' | 'features' | 'selection' | 'preview';

export const Preprocessing: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();

  const [currentStep, setCurrentStep] = useState<Step>('target_split');
  const [config, setConfig] = useState<PreprocessingConfig>({
    target_column: null,
    problem_type: null,
    numerical_features: [],
    categorical_features: [],
    datetime_features: [],
    feature_selection: {
      variance_threshold: null,
      correlation_threshold: null,
      drop_features: [],
    },
    split_config: {
      test_size: 0.2,
      val_size: 0.0,
      stratify: true,
      random_state: 42,
      shuffle: true,
    },
  });

  const [result, setResult] = useState<PreprocessingResponse | null>(null);

  // Load dataset schema metadata
  const { data: datasetData, isLoading: isDatasetLoading } = useQuery({
    queryKey: ['dataset', datasetId],
    queryFn: () => getDataset(datasetId!),
    enabled: !!datasetId,
  });

  const dataset = datasetData?.data;

  // Populate default feature configs on load
  useEffect(() => {
    if (dataset && dataset.columns && config.numerical_features.length === 0 && config.categorical_features.length === 0) {
      const numFeats: NumericalFeatureConfig[] = [];
      const catFeats: CategoricalFeatureConfig[] = [];
      const dtFeats: DatetimeFeatureConfig[] = [];

      dataset.columns.forEach((col) => {
        if (col.inferred_type === 'numeric') {
          numFeats.push({
            column_name: col.name,
            imputer: 'median',
            imputer_fill_value: null,
            scaler: 'standard',
            power_transform: 'none',
            clip_outliers: false,
            lower_percentile: 0.01,
            upper_percentile: 0.99,
          });
        } else if (col.inferred_type === 'categorical') {
          catFeats.push({
            column_name: col.name,
            imputer: 'most_frequent',
            imputer_fill_value: 'missing',
            encoder: 'onehot',
            max_categories: 20,
            handle_unknown: 'ignore',
          });
        } else if (col.inferred_type === 'datetime') {
          dtFeats.push({
            column_name: col.name,
            extracted_parts: ['year', 'month', 'day', 'dayofweek', 'is_weekend'],
            cyclical_encoding: true,
            drop_original: true,
          });
        }
      });

      setConfig((prev) => ({
        ...prev,
        numerical_features: numFeats,
        categorical_features: catFeats,
        datetime_features: dtFeats,
      }));
    }
  }, [dataset]);

  // Execute mutation
  const executeMutation = useMutation({
    mutationFn: (cfg: PreprocessingConfig) =>
      preprocessorApi.executePreprocessing(datasetId!, cfg),
    onSuccess: (data) => {
      setResult(data);
      setCurrentStep('preview');
    },
  });

  const handleExecute = () => {
    executeMutation.mutate(config);
  };

  const handleDownloadConfig = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pipeline-config-${dataset?.filename}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isDatasetLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <p className="text-sm font-semibold text-foreground">Loading Feature Engineering Studio...</p>
      </div>
    );
  }

  const columns = dataset?.columns || [];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Link to="/datasets" className="hover:text-foreground">
              Datasets
            </Link>
            <ChevronRight className="w-3 h-3" />
            <Link to={`/datasets/${datasetId}`} className="hover:text-foreground truncate max-w-[200px]">
              {dataset?.filename}
            </Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-foreground font-semibold">Preprocessing Studio</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
              <Wand2 className="w-6 h-6 text-primary" /> Preprocessing & Feature Engineering
            </h1>
            <span className="text-xs px-2.5 py-0.5 bg-emerald-500/10 text-emerald-600 font-semibold rounded-full">
              Zero Data Leakage Guaranteed
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to={`/datasets/${datasetId}`}
            className="px-3 py-2 bg-muted text-foreground rounded-lg text-xs font-semibold hover:bg-accent flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dataset
          </Link>
        </div>
      </div>

      {/* Step Stepper Navigation */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { id: 'target_split', label: '1. Target & Data Split', icon: Target },
          { id: 'features', label: '2. Feature Transformations', icon: Sliders },
          { id: 'selection', label: '3. Feature Pruning & Filter', icon: Filter },
          { id: 'preview', label: '4. Pipeline Result & Matrix', icon: Table },
        ].map((step) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isDone =
            (step.id === 'target_split' && currentStep !== 'target_split') ||
            (step.id === 'features' && (currentStep === 'selection' || currentStep === 'preview')) ||
            (step.id === 'selection' && currentStep === 'preview');

          return (
            <button
              key={step.id}
              onClick={() => setCurrentStep(step.id as Step)}
              className={`p-3.5 rounded-xl border text-left transition-all flex items-center gap-3 ${
                isActive
                  ? 'bg-card border-primary ring-2 ring-primary/20 shadow-xs'
                  : isDone
                  ? 'bg-muted/40 border-border text-foreground hover:bg-muted'
                  : 'bg-card border-border text-muted-foreground opacity-60'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : isDone
                    ? 'bg-emerald-500/10 text-emerald-600'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {isDone ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
              </div>
              <div className="truncate">
                <span className="text-xs font-bold block">{step.label}</span>
                <span className="text-[10px] text-muted-foreground">
                  {step.id === 'target_split'
                    ? 'Label & split ratio'
                    : step.id === 'features'
                    ? 'Scalers & encoders'
                    : step.id === 'selection'
                    ? 'Variance & collinearity'
                    : 'Fitted matrix preview'}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* STEP 1: TARGET VARIABLE & SPLITTING */}
      {currentStep === 'target_split' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-xs space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" /> Target Variable & Task Objective
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Select the prediction label and problem type to apply appropriate target stratification and encoding.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="text-xs font-semibold text-foreground block mb-2">
                  Target Column (Label Variable)
                </label>
                <select
                  value={config.target_column || ''}
                  onChange={(e) => {
                    const val = e.target.value || null;
                    const colObj = columns.find((c) => c.name === val);
                    const probType =
                      colObj?.inferred_type === 'numeric'
                        ? 'regression'
                        : colObj?.inferred_type === 'categorical' || colObj?.inferred_type === 'boolean'
                        ? 'classification'
                        : null;

                    setConfig((prev) => ({
                      ...prev,
                      target_column: val,
                      problem_type: probType,
                      numerical_features: prev.numerical_features.filter((f) => f.column_name !== val),
                      categorical_features: prev.categorical_features.filter((f) => f.column_name !== val),
                    }));
                  }}
                  className="w-full text-xs px-3 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">-- Unsupervised / No Target Column --</option>
                  {columns.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name} ({c.inferred_type})
                    </option>
                  ))}
                </select>
                <span className="text-[11px] text-muted-foreground mt-1 block">
                  The target variable will be excluded from feature transformations to prevent leakage.
                </span>
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground block mb-2">
                  Problem Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setConfig((prev) => ({ ...prev, problem_type: 'classification' }))}
                    className={`p-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition-colors ${
                      config.problem_type === 'classification'
                        ? 'bg-primary/10 border-primary text-primary'
                        : 'bg-background border-border text-foreground hover:bg-muted'
                    }`}
                  >
                    Classification (Binary/Multi)
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfig((prev) => ({ ...prev, problem_type: 'regression' }))}
                    className={`p-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition-colors ${
                      config.problem_type === 'regression'
                        ? 'bg-primary/10 border-primary text-primary'
                        : 'bg-background border-border text-foreground hover:bg-muted'
                    }`}
                  >
                    Regression (Continuous)
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Splitting Configuration */}
          <div className="bg-card border border-border rounded-xl p-6 shadow-xs space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-500" /> Data Splitting & Leakage Isolation
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Transformers are fitted solely on the training partition and evaluated out-of-sample.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs font-semibold text-foreground block mb-1">
                  Test Split Size ({(config.split_config.test_size * 100).toFixed(0)}%)
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="0.4"
                  step="0.05"
                  value={config.split_config.test_size}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      split_config: {
                        ...prev.split_config,
                        test_size: parseFloat(e.target.value),
                      },
                    }))
                  }
                  className="w-full cursor-pointer accent-primary"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground block mb-1">
                  Random Seed
                </label>
                <input
                  type="number"
                  value={config.split_config.random_state}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      split_config: {
                        ...prev.split_config,
                        random_state: parseInt(e.target.value) || 42,
                      },
                    }))
                  }
                  className="w-full text-xs px-3 py-1.5 bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="flex items-center gap-2 pt-5">
                <input
                  type="checkbox"
                  id="stratify_chk"
                  checked={config.split_config.stratify}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      split_config: {
                        ...prev.split_config,
                        stratify: e.target.checked,
                      },
                    }))
                  }
                  className="w-4 h-4 rounded text-primary accent-primary"
                />
                <label htmlFor="stratify_chk" className="text-xs font-semibold text-foreground cursor-pointer">
                  Stratified Split (Preserve class balance)
                </label>
              </div>

              <div className="flex items-center gap-2 pt-5">
                <input
                  type="checkbox"
                  id="shuffle_chk"
                  checked={config.split_config.shuffle}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      split_config: {
                        ...prev.split_config,
                        shuffle: e.target.checked,
                      },
                    }))
                  }
                  className="w-4 h-4 rounded text-primary accent-primary"
                />
                <label htmlFor="shuffle_chk" className="text-xs font-semibold text-foreground cursor-pointer">
                  Shuffle Rows Before Splitting
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => setCurrentStep('features')}
              className="px-5 py-2.5 bg-primary text-primary-foreground text-xs font-bold rounded-lg hover:bg-primary/90 flex items-center gap-2 shadow-xs"
            >
              Continue to Feature Transformations <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: FEATURE TRANSFORMATIONS */}
      {currentStep === 'features' && (
        <div className="space-y-6">
          {/* Numerical Features Table */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-primary" /> Numerical Feature Pipelines ({config.numerical_features.length})
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Configure missing value imputation, outlier clipping, power transformations, and scaling.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted text-muted-foreground uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="px-3 py-2.5">Feature Name</th>
                    <th className="px-3 py-2.5">Missing Imputer</th>
                    <th className="px-3 py-2.5">Scaler Algorithm</th>
                    <th className="px-3 py-2.5">Power Transform</th>
                    <th className="px-3 py-2.5 text-center">Outlier Clipper</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {config.numerical_features.map((feat, idx) => (
                    <tr key={feat.column_name} className="hover:bg-accent/30">
                      <td className="px-3 py-2 font-semibold text-foreground">{feat.column_name}</td>
                      <td className="px-3 py-2">
                        <select
                          value={feat.imputer}
                          onChange={(e) => {
                            const val = e.target.value as NumericalImputer;
                            setConfig((prev) => {
                              const updated = [...prev.numerical_features];
                              updated[idx].imputer = val;
                              return { ...prev, numerical_features: updated };
                            });
                          }}
                          className="text-xs px-2 py-1 bg-background border border-input rounded focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="median">Median</option>
                          <option value="mean">Mean</option>
                          <option value="most_frequent">Most Frequent</option>
                          <option value="constant">Constant (0.0)</option>
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select
                          value={feat.scaler}
                          onChange={(e) => {
                            const val = e.target.value as NumericalScaler;
                            setConfig((prev) => {
                              const updated = [...prev.numerical_features];
                              updated[idx].scaler = val;
                              return { ...prev, numerical_features: updated };
                            });
                          }}
                          className="text-xs px-2 py-1 bg-background border border-input rounded focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="standard">StandardScaler (z-score)</option>
                          <option value="minmax">MinMaxScaler [0, 1]</option>
                          <option value="robust">RobustScaler (IQR)</option>
                          <option value="maxabs">MaxAbsScaler [-1, 1]</option>
                          <option value="none">No Scaling (Raw)</option>
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select
                          value={feat.power_transform}
                          onChange={(e) => {
                            const val = e.target.value as NumericalPowerTransform;
                            setConfig((prev) => {
                              const updated = [...prev.numerical_features];
                              updated[idx].power_transform = val;
                              return { ...prev, numerical_features: updated };
                            });
                          }}
                          className="text-xs px-2 py-1 bg-background border border-input rounded focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="none">None</option>
                          <option value="log1p">Log1p (log(1+x))</option>
                        </select>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={feat.clip_outliers}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setConfig((prev) => {
                              const updated = [...prev.numerical_features];
                              updated[idx].clip_outliers = checked;
                              return { ...prev, numerical_features: updated };
                            });
                          }}
                          className="w-4 h-4 rounded text-primary accent-primary"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Categorical Features Table */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-500" /> Categorical Feature Pipelines ({config.categorical_features.length})
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Configure string encoders, high-cardinality grouping, and unknown category handling.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted text-muted-foreground uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="px-3 py-2.5">Feature Name</th>
                    <th className="px-3 py-2.5">Missing Imputer</th>
                    <th className="px-3 py-2.5">Encoder Strategy</th>
                    <th className="px-3 py-2.5">Max Categories (Top K)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {config.categorical_features.map((feat, idx) => (
                    <tr key={feat.column_name} className="hover:bg-accent/30">
                      <td className="px-3 py-2 font-semibold text-foreground">{feat.column_name}</td>
                      <td className="px-3 py-2">
                        <select
                          value={feat.imputer}
                          onChange={(e) => {
                            const val = e.target.value as CategoricalImputer;
                            setConfig((prev) => {
                              const updated = [...prev.categorical_features];
                              updated[idx].imputer = val;
                              return { ...prev, categorical_features: updated };
                            });
                          }}
                          className="text-xs px-2 py-1 bg-background border border-input rounded focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="most_frequent">Most Frequent</option>
                          <option value="constant">Constant ('missing')</option>
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select
                          value={feat.encoder}
                          onChange={(e) => {
                            const val = e.target.value as CategoricalEncoder;
                            setConfig((prev) => {
                              const updated = [...prev.categorical_features];
                              updated[idx].encoder = val;
                              return { ...prev, categorical_features: updated };
                            });
                          }}
                          className="text-xs px-2 py-1 bg-background border border-input rounded focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="onehot">One-Hot Encoding</option>
                          <option value="ordinal">Ordinal Integer Encoding</option>
                          <option value="frequency">Frequency / Count Encoding</option>
                          <option value="target">Smoothed Target Mean Encoding</option>
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="number"
                          min="2"
                          max="100"
                          value={feat.max_categories || 20}
                          onChange={(e) => {
                            const val = parseInt(e.target.value) || 20;
                            setConfig((prev) => {
                              const updated = [...prev.categorical_features];
                              updated[idx].max_categories = val;
                              return { ...prev, categorical_features: updated };
                            });
                          }}
                          className="w-20 text-xs px-2 py-1 bg-background border border-input rounded focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button
              onClick={() => setCurrentStep('target_split')}
              className="px-4 py-2 bg-muted text-foreground text-xs font-semibold rounded-lg hover:bg-accent flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Previous Step
            </button>
            <button
              onClick={() => setCurrentStep('selection')}
              className="px-5 py-2.5 bg-primary text-primary-foreground text-xs font-bold rounded-lg hover:bg-primary/90 flex items-center gap-2 shadow-xs"
            >
              Continue to Feature Selection <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: FEATURE SELECTION & PRUNING */}
      {currentStep === 'selection' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-xs space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <Filter className="w-5 h-5 text-amber-500" /> Feature Pruning & Dimensionality Filters
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Automatically eliminate low-variance features and prune multicollinear pairs.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground block">
                  Variance Threshold Filter (Drop features with variance &le; &theta;)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="e.g. 0.0 for constant columns"
                    value={config.feature_selection.variance_threshold ?? ''}
                    onChange={(e) => {
                      const val = e.target.value === '' ? null : parseFloat(e.target.value);
                      setConfig((prev) => ({
                        ...prev,
                        feature_selection: {
                          ...prev.feature_selection,
                          variance_threshold: val,
                        },
                      }));
                    }}
                    className="w-full text-xs px-3 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    type="button"
                    onClick={() =>
                      setConfig((prev) => ({
                        ...prev,
                        feature_selection: {
                          ...prev.feature_selection,
                          variance_threshold: 0.0,
                        },
                      }))
                    }
                    className="px-3 py-2 bg-muted text-xs font-medium rounded-lg hover:bg-accent whitespace-nowrap"
                  >
                    Set 0.0 (Constants)
                  </button>
                </div>
                <span className="text-[11px] text-muted-foreground">
                  Removes constant or quasi-constant features that provide zero information.
                </span>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground block">
                  Multicollinearity Correlation Pruning (|r| &gt; &theta;)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    step="0.05"
                    min="0.5"
                    max="0.99"
                    placeholder="e.g. 0.85 to drop redundant features"
                    value={config.feature_selection.correlation_threshold ?? ''}
                    onChange={(e) => {
                      const val = e.target.value === '' ? null : parseFloat(e.target.value);
                      setConfig((prev) => ({
                        ...prev,
                        feature_selection: {
                          ...prev.feature_selection,
                          correlation_threshold: val,
                        },
                      }));
                    }}
                    className="w-full text-xs px-3 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    type="button"
                    onClick={() =>
                      setConfig((prev) => ({
                        ...prev,
                        feature_selection: {
                          ...prev.feature_selection,
                          correlation_threshold: 0.85,
                        },
                      }))
                    }
                    className="px-3 py-2 bg-muted text-xs font-medium rounded-lg hover:bg-accent whitespace-nowrap"
                  >
                    Set 0.85 (High)
                  </button>
                </div>
                <span className="text-[11px] text-muted-foreground">
                  Prunes redundant collinear features based on training split correlation matrix.
                </span>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button
              onClick={() => setCurrentStep('features')}
              className="px-4 py-2 bg-muted text-foreground text-xs font-semibold rounded-lg hover:bg-accent flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Previous Step
            </button>

            <button
              onClick={handleExecute}
              disabled={executeMutation.isPending}
              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg flex items-center gap-2 shadow-md transition-all"
            >
              {executeMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Fitting Pipeline on Train Split...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Execute Preprocessing Pipeline
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: PREVIEW & MATRIX DISPLAY */}
      {currentStep === 'preview' && result && (
        <div className="space-y-6">
          {/* Success Banner & Metrics */}
          <div className="bg-emerald-500/10 border border-emerald-200 dark:border-emerald-800/30 p-5 rounded-xl shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-emerald-900 dark:text-emerald-300">
                    Pipeline Fitted & Serialized Successfully
                  </h2>
                  <p className="text-xs text-emerald-800 dark:text-emerald-400 mt-0.5">
                    Pipeline Artifact ID: <span className="font-mono font-semibold">{result.pipeline_id}</span> • Executed in {result.execution_time_ms} ms
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadConfig}
                  className="px-3 py-2 bg-background border border-input rounded-lg text-xs font-semibold text-foreground hover:bg-accent flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" /> Export Pipeline JSON
                </button>
                <Link
                  to="/training"
                  className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-bold rounded-lg flex items-center gap-1.5 shadow-sm"
                >
                  <Cpu className="w-3.5 h-3.5" /> Launch Model Training (Phase 8)
                </Link>
              </div>
            </div>
          </div>

          {/* Matrix Shape Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Raw Input Shape</span>
              <div className="text-lg font-bold text-foreground mt-1">
                {result.original_shape[0].toLocaleString()} &times; {result.original_shape[1]}
              </div>
              <span className="text-[11px] text-muted-foreground">{result.original_feature_count} features</span>
            </div>

            <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Training Matrix (X_train)</span>
              <div className="text-lg font-bold text-primary mt-1">
                {result.train_shape[0].toLocaleString()} &times; {result.train_shape[1]}
              </div>
              <span className="text-[11px] text-muted-foreground">Fitted split</span>
            </div>

            <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Test Matrix (X_test)</span>
              <div className="text-lg font-bold text-indigo-600 mt-1">
                {result.test_shape[0].toLocaleString()} &times; {result.test_shape[1]}
              </div>
              <span className="text-[11px] text-muted-foreground">Holdout evaluation split</span>
            </div>

            <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
              <span className="text-xs text-muted-foreground uppercase font-semibold">Transformed Features</span>
              <div className="text-lg font-bold text-emerald-600 mt-1">
                {result.transformed_feature_count}
              </div>
              <span className="text-[11px] text-muted-foreground">
                {result.dropped_features.length > 0 ? `${result.dropped_features.length} dropped` : 'All retained'}
              </span>
            </div>
          </div>

          {/* Transformed Data Preview Table */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Table className="w-4 h-4 text-primary" /> Transformed Training Matrix Preview (First 10 Rows)
              </h3>
              <span className="text-xs text-muted-foreground">
                {result.transformed_feature_names.length} numerical columns
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted text-muted-foreground uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="px-3 py-2">Row #</th>
                    {result.transformed_feature_names.map((colName) => (
                      <th key={colName} className="px-3 py-2 whitespace-nowrap">
                        {colName}
                      </th>
                    ))}
                    {result.target_column && (
                      <th className="px-3 py-2 bg-primary/10 text-primary font-bold">
                        TARGET ({result.target_column})
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {result.train_preview.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-accent/30 font-mono">
                      <td className="px-3 py-2 text-muted-foreground font-sans font-medium">{rIdx + 1}</td>
                      {result.transformed_feature_names.map((colName) => (
                        <td key={colName} className="px-3 py-2 whitespace-nowrap text-foreground">
                          {row[colName] !== null ? row[colName] : '-'}
                        </td>
                      ))}
                      {result.target_column && (
                        <td className="px-3 py-2 font-bold text-primary bg-primary/5">
                          {row.__target__ !== undefined ? row.__target__ : '-'}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button
              onClick={() => setCurrentStep('selection')}
              className="px-4 py-2 bg-muted text-foreground text-xs font-semibold rounded-lg hover:bg-accent flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Adjust Selection & Transforms
            </button>
            <button
              onClick={() => {
                setConfig({
                  target_column: null,
                  problem_type: null,
                  numerical_features: [],
                  categorical_features: [],
                  datetime_features: [],
                  feature_selection: { variance_threshold: null, correlation_threshold: null, drop_features: [] },
                  split_config: { test_size: 0.2, val_size: 0.0, stratify: true, random_state: 42, shuffle: true },
                });
                setResult(null);
                setCurrentStep('target_split');
              }}
              className="px-4 py-2 bg-muted text-foreground text-xs font-semibold rounded-lg hover:bg-accent flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset Wizard
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
