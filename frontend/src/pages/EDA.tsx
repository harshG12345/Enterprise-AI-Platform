import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  ArrowLeft,
  BarChart2,
  ChevronRight,
  Database,
  Download,
  Flame,
  HelpCircle,
  Loader2,
  RefreshCw,
  Sparkles,
  Tag,
} from 'lucide-react';

import { edaApi } from '../api/eda';
import { OverviewTab } from '../components/eda/OverviewTab';
import { NumericalFeaturesTab } from '../components/eda/NumericalFeaturesTab';
import { CategoricalFeaturesTab } from '../components/eda/CategoricalFeaturesTab';
import { MissingValuesTab } from '../components/eda/MissingValuesTab';
import { CorrelationMatrixTab } from '../components/eda/CorrelationMatrixTab';

type EDATab = 'overview' | 'numerical' | 'categorical' | 'missing' | 'correlation';

export const EDA: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [activeTab, setActiveTab] = useState<EDATab>('overview');

  const {
    data: eda,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['eda', datasetId],
    queryFn: () => edaApi.getDatasetEDA(datasetId!),
    enabled: !!datasetId,
  });

  const handleExportJSON = () => {
    if (!eda) return;
    const blob = new Blob([JSON.stringify(eda, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eda-report-${eda.dataset_name}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <div className="text-center">
          <p className="text-base font-semibold text-foreground">Computing Statistical Distributions...</p>
          <p className="text-xs text-muted-foreground mt-1">
            Calculating moments, quantiles, histograms, outlier boundaries, and correlation matrices
          </p>
        </div>
      </div>
    );
  }

  if (isError || !eda) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 max-w-lg mx-auto text-center space-y-4 my-12">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <div>
          <h2 className="text-lg font-bold text-foreground">Exploratory Analysis Failed</h2>
          <p className="text-xs text-muted-foreground mt-1">
            {(error as any)?.response?.data?.error?.message || 'Could not load EDA profile for this dataset.'}
          </p>
        </div>
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Try Again
          </button>
          <Link
            to={`/datasets/${datasetId}`}
            className="px-4 py-2 bg-muted text-foreground text-xs font-semibold rounded-lg hover:bg-accent"
          >
            Back to Dataset
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Link to="/datasets" className="hover:text-foreground">
              Datasets
            </Link>
            <ChevronRight className="w-3 h-3" />
            <Link to={`/datasets/${datasetId}`} className="hover:text-foreground truncate max-w-[200px]">
              {eda.dataset_name}
            </Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-foreground font-semibold">EDA Studio</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-primary" /> Exploratory Data Analysis (EDA)
            </h1>
            <span className="text-xs px-2.5 py-0.5 bg-primary/10 text-primary font-semibold rounded-full">
              Automated Profiling
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="px-3 py-2 bg-background border border-input rounded-lg text-xs font-semibold text-foreground hover:bg-accent flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} /> Refresh
          </button>

          <button
            onClick={handleExportJSON}
            className="px-3 py-2 bg-background border border-input rounded-lg text-xs font-semibold text-foreground hover:bg-accent flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> Export Report JSON
          </button>

          <Link
            to={`/datasets/${datasetId}`}
            className="px-3 py-2 bg-muted text-foreground rounded-lg text-xs font-semibold hover:bg-accent flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dataset
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-border space-x-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Database className="w-4 h-4" /> Overview & Health
          {eda.health_warnings.length > 0 && (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-amber-500/10 text-amber-700 font-bold">
              {eda.health_warnings.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('numerical')}
          className={`pb-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'numerical'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart2 className="w-4 h-4" /> Numerical Features ({eda.numerical_features.length})
        </button>

        <button
          onClick={() => setActiveTab('categorical')}
          className={`pb-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'categorical'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Tag className="w-4 h-4" /> Categorical Features ({eda.categorical_features.length})
        </button>

        <button
          onClick={() => setActiveTab('missing')}
          className={`pb-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'missing'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <HelpCircle className="w-4 h-4" /> Missingness Profile
        </button>

        <button
          onClick={() => setActiveTab('correlation')}
          className={`pb-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'correlation'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Flame className="w-4 h-4 text-red-500" /> Correlation Heatmap
        </button>
      </div>

      {/* Tab Content Display */}
      {activeTab === 'overview' && <OverviewTab eda={eda} />}
      {activeTab === 'numerical' && (
        <NumericalFeaturesTab numericalFeatures={eda.numerical_features} />
      )}
      {activeTab === 'categorical' && (
        <CategoricalFeaturesTab categoricalFeatures={eda.categorical_features} />
      )}
      {activeTab === 'missing' && <MissingValuesTab missingSummary={eda.missing_summary} />}
      {activeTab === 'correlation' && (
        <CorrelationMatrixTab
          pearsonCorr={eda.pearson_correlation}
          spearmanCorr={eda.spearman_correlation}
        />
      )}
    </div>
  );
};
