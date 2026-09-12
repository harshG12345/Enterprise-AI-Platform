import React, { useState } from 'react';
import {
  AlertTriangle,
  Flame,
  Network,
} from 'lucide-react';
import { CorrelationMatrix } from '../../types/eda';

interface CorrelationMatrixTabProps {
  pearsonCorr?: CorrelationMatrix | null;
  spearmanCorr?: CorrelationMatrix | null;
}

export const CorrelationMatrixTab: React.FC<CorrelationMatrixTabProps> = ({
  pearsonCorr,
  spearmanCorr,
}) => {
  const [method, setMethod] = useState<'pearson' | 'spearman'>('pearson');
  const [hoveredCell, setHoveredCell] = useState<{
    f1: string;
    f2: string;
    val: number | null;
  } | null>(null);

  const activeCorr = method === 'pearson' ? pearsonCorr : spearmanCorr;

  if (!activeCorr || activeCorr.features.length < 2) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground">
        <Network className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm font-medium text-foreground">Insufficient Numerical Features</p>
        <p className="text-xs mt-1">Correlation requires at least 2 numerical columns in the dataset.</p>
      </div>
    );
  }

  const { features, matrix, pairwise_pairs } = activeCorr;

  // Helper for Heatmap Cell Color
  // -1.0 (Deep Blue) -> 0.0 (Slate/Neutral) -> +1.0 (Deep Crimson / Amber)
  const getCellColor = (val: number | null): string => {
    if (val === null || isNaN(val)) return 'bg-muted text-muted-foreground';
    if (val === 1.0) return 'bg-red-600 text-white font-bold';
    if (val >= 0.8) return 'bg-red-500 text-white font-semibold';
    if (val >= 0.5) return 'bg-orange-400 text-slate-900 font-medium';
    if (val >= 0.2) return 'bg-amber-200 text-slate-900';
    if (val > -0.2) return 'bg-slate-100 dark:bg-slate-800 text-muted-foreground';
    if (val > -0.5) return 'bg-sky-200 text-slate-900';
    if (val > -0.8) return 'bg-blue-400 text-white font-medium';
    return 'bg-blue-600 text-white font-semibold';
  };

  const highCollinearPairs = pairwise_pairs.filter((p) => Math.abs(p.correlation) >= 0.85);

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="bg-card border border-border rounded-xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Flame className="w-4 h-4 text-red-500" /> Bivariate Feature Correlation Matrix
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Evaluate pairwise linear dependency and multicollinearity across {features.length} numerical features.
          </p>
        </div>

        {/* Method Toggle */}
        <div className="flex items-center gap-2 bg-muted p-1 rounded-lg border border-border">
          <button
            onClick={() => setMethod('pearson')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              method === 'pearson'
                ? 'bg-primary text-primary-foreground shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Pearson (Linear)
          </button>
          <button
            onClick={() => setMethod('spearman')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              method === 'spearman'
                ? 'bg-primary text-primary-foreground shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Spearman (Rank)
          </button>
        </div>
      </div>

      {/* Multicollinearity Warning Banner if detected */}
      {highCollinearPairs.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-200 dark:border-amber-900/30 p-4 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider">
              Strong Collinear Pairs Detected ({highCollinearPairs.length})
            </h4>
            <p className="text-xs text-amber-800 dark:text-amber-200">
              Features with absolute correlation ≥ 0.85 may inflate regression coefficient variance. Consider removing one feature per pair or applying PCA dimensionality reduction.
            </p>
          </div>
        </div>
      )}

      {/* Interactive Heatmap Matrix Grid */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">
            Heatmap Grid ({method.toUpperCase()})
          </span>
          {hoveredCell && (
            <div className="text-xs bg-muted px-3 py-1 rounded-lg border border-border">
              <span className="font-semibold text-foreground">
                {hoveredCell.f1} &times; {hoveredCell.f2}:
              </span>{' '}
              <span className="font-mono font-bold text-primary">
                {hoveredCell.val !== null ? hoveredCell.val.toFixed(4) : 'N/A'}
              </span>
            </div>
          )}
        </div>

        <div className="overflow-x-auto pb-2">
          <div className="inline-block min-w-full">
            <div className="grid" style={{ gridTemplateColumns: `140px repeat(${features.length}, minmax(64px, 1fr))` }}>
              {/* Header Row */}
              <div className="p-2 font-semibold text-[11px] text-muted-foreground border-b border-border">
                Feature
              </div>
              {features.map((f) => (
                <div
                  key={`header-${f}`}
                  className="p-2 text-center text-[10px] font-semibold text-muted-foreground truncate border-b border-border"
                  title={f}
                >
                  {f}
                </div>
              ))}

              {/* Data Rows */}
              {features.map((rowFeat, i) => (
                <React.Fragment key={`row-${rowFeat}`}>
                  <div
                    className="p-2 text-[11px] font-medium text-foreground truncate border-b border-border/50 flex items-center"
                    title={rowFeat}
                  >
                    {rowFeat}
                  </div>
                  {features.map((colFeat, j) => {
                    const val = matrix[i]?.[j] ?? null;
                    return (
                      <div
                        key={`cell-${i}-${j}`}
                        onMouseEnter={() =>
                          setHoveredCell({ f1: rowFeat, f2: colFeat, val })
                        }
                        onMouseLeave={() => setHoveredCell(null)}
                        className={`p-2 text-center text-[11px] font-mono border border-background/20 transition-transform hover:scale-105 hover:z-10 cursor-pointer ${getCellColor(
                          val
                        )}`}
                        title={`${rowFeat} vs ${colFeat}: ${val !== null ? val.toFixed(4) : 'N/A'}`}
                      >
                        {val !== null ? val.toFixed(2) : '-'}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-2 pt-2 text-[11px] text-muted-foreground">
          <span>Negative (-1.0)</span>
          <div className="flex h-3 w-48 rounded overflow-hidden border border-border">
            <div className="flex-1 bg-blue-600" />
            <div className="flex-1 bg-sky-300" />
            <div className="flex-1 bg-slate-200 dark:bg-slate-700" />
            <div className="flex-1 bg-amber-200" />
            <div className="flex-1 bg-orange-400" />
            <div className="flex-1 bg-red-600" />
          </div>
          <span>Positive (+1.0)</span>
        </div>
      </div>

      {/* Ranked Pairwise Table */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-3">
        <h3 className="text-sm font-semibold text-foreground">
          Ranked Pairwise Correlations (Top Absolute Dependencies)
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-muted text-muted-foreground uppercase font-semibold border-b border-border">
              <tr>
                <th className="px-3 py-2">Feature X</th>
                <th className="px-3 py-2">Feature Y</th>
                <th className="px-3 py-2 text-right">Correlation (r)</th>
                <th className="px-3 py-2 text-center">Linear Dependency</th>
                <th className="px-3 py-2">Collinearity Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pairwise_pairs.slice(0, 15).map((pair, idx) => {
                const absR = Math.abs(pair.correlation);
                const isHigh = absR >= 0.85;
                const isModerate = absR >= 0.5;

                return (
                  <tr key={idx} className="hover:bg-accent/30">
                    <td className="px-3 py-2 font-medium text-foreground">{pair.feature_x}</td>
                    <td className="px-3 py-2 font-medium text-foreground">{pair.feature_y}</td>
                    <td className="px-3 py-2 text-right font-mono font-bold text-foreground">
                      {pair.correlation > 0 ? `+${pair.correlation.toFixed(4)}` : pair.correlation.toFixed(4)}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          isHigh
                            ? 'bg-red-500/10 text-red-600'
                            : isModerate
                            ? 'bg-amber-500/10 text-amber-600'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {isHigh ? 'Strong' : isModerate ? 'Moderate' : 'Weak'}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {isHigh ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-red-600 font-semibold">
                          <AlertTriangle className="w-3 h-3" /> Redundant / Collinear
                        </span>
                      ) : (
                        <span className="text-[11px] text-muted-foreground">Acceptable Variance</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
