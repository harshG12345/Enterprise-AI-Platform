import React from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  HardDrive,
  HelpCircle,
  Info,
  Layers,
  Sparkles,
  Zap,
} from 'lucide-react';
import { EDAResponse } from '../../types/eda';

interface OverviewTabProps {
  eda: EDAResponse;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ eda }) => {
  const { overview, health_warnings } = eda;

  const getWarningBadge = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-500/10 text-red-700 border-red-200 dark:border-red-800/40 dark:text-red-400';
      case 'warning':
        return 'bg-amber-500/10 text-amber-700 border-amber-200 dark:border-amber-800/40 dark:text-amber-400';
      default:
        return 'bg-blue-500/10 text-blue-700 border-blue-200 dark:border-blue-800/40 dark:text-blue-400';
    }
  };

  const getWarningIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />;
      default:
        return <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Statistical Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-1">
            <span className="text-xs font-medium uppercase tracking-wider">Total Rows</span>
            <FileSpreadsheet className="w-4 h-4 text-primary" />
          </div>
          <div className="text-xl font-bold text-foreground">{overview.total_rows.toLocaleString()}</div>
          <div className="text-[11px] text-muted-foreground mt-1">Instances sampled</div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-1">
            <span className="text-xs font-medium uppercase tracking-wider">Features</span>
            <Layers className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-xl font-bold text-foreground">{overview.total_columns}</div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {overview.numerical_columns_count} num, {overview.categorical_columns_count} cat
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-1">
            <span className="text-xs font-medium uppercase tracking-wider">Missing Cells</span>
            <HelpCircle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-xl font-bold text-foreground">
            {overview.missing_cells_percentage.toFixed(1)}%
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {overview.total_missing_cells.toLocaleString()} cells missing
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-1">
            <span className="text-xs font-medium uppercase tracking-wider">Duplicates</span>
            <Database className="w-4 h-4 text-violet-500" />
          </div>
          <div className="text-xl font-bold text-foreground">
            {overview.duplicate_rows_count.toLocaleString()}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {overview.duplicate_rows_percentage.toFixed(1)}% duplicate rows
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-1">
            <span className="text-xs font-medium uppercase tracking-wider">Memory Size</span>
            <HardDrive className="w-4 h-4 text-cyan-500" />
          </div>
          <div className="text-xl font-bold text-foreground">{overview.memory_usage_human}</div>
          <div className="text-[11px] text-muted-foreground mt-1">Deep in-memory footprint</div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground mb-1">
            <span className="text-xs font-medium uppercase tracking-wider">Quality Score</span>
            <Sparkles className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-xl font-bold text-emerald-600">
            {Math.max(0, 100 - Math.round(overview.missing_cells_percentage * 2 + health_warnings.length * 5))}/100
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">
            {health_warnings.length === 0 ? 'Optimal state' : `${health_warnings.length} advisory alerts`}
          </div>
        </div>
      </div>

      {/* Feature Breakdown by Type */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
            <Zap className="w-4 h-4 text-primary" /> Feature Type Distribution
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs font-medium text-muted-foreground mb-1">
                <span>Numerical Features (Continuous / Discrete)</span>
                <span className="font-semibold text-foreground">
                  {overview.numerical_columns_count} (
                  {((overview.numerical_columns_count / overview.total_columns) * 100).toFixed(0)}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{
                    width: `${(overview.numerical_columns_count / overview.total_columns) * 100}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium text-muted-foreground mb-1">
                <span>Categorical & Text Features</span>
                <span className="font-semibold text-foreground">
                  {overview.categorical_columns_count} (
                  {((overview.categorical_columns_count / overview.total_columns) * 100).toFixed(0)}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                <div
                  className="bg-indigo-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${(overview.categorical_columns_count / overview.total_columns) * 100}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium text-muted-foreground mb-1">
                <span>Boolean Flags</span>
                <span className="font-semibold text-foreground">
                  {overview.boolean_columns_count} (
                  {((overview.boolean_columns_count / overview.total_columns) * 100).toFixed(0)}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                <div
                  className="bg-emerald-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${(overview.boolean_columns_count / overview.total_columns) * 100}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium text-muted-foreground mb-1">
                <span>Datetime Timestamps</span>
                <span className="font-semibold text-foreground">
                  {overview.datetime_columns_count} (
                  {((overview.datetime_columns_count / overview.total_columns) * 100).toFixed(0)}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                <div
                  className="bg-cyan-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${(overview.datetime_columns_count / overview.total_columns) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Health Advisory & Quality Insights */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-emerald-500" /> Automated Quality Diagnosis
          </h3>
          {health_warnings.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-center text-muted-foreground">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mb-2" />
              <p className="text-sm font-medium text-foreground">Clean Dataset Hygiene</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                No high missingness, zero variance, collinearity, or extreme skew issues were detected.
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
              {health_warnings.map((warn, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border flex items-start gap-3 ${getWarningBadge(warn.level)}`}
                >
                  {getWarningIcon(warn.level)}
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider">{warn.code}</span>
                      <span className="text-[10px] uppercase font-semibold px-1.5 py-0.2 rounded bg-background/50">
                        {warn.level}
                      </span>
                    </div>
                    <p className="text-xs text-foreground font-medium">{warn.message}</p>
                    <p className="text-[11px] text-muted-foreground italic">💡 {warn.suggestion}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
