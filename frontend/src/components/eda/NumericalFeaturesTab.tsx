import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import {
  AlertCircle,
  BarChart2,
  Hash,
  Sliders,
} from 'lucide-react';
import { NumericalColumnStats } from '../../types/eda';

interface NumericalFeaturesTabProps {
  numericalFeatures: NumericalColumnStats[];
}

export const NumericalFeaturesTab: React.FC<NumericalFeaturesTabProps> = ({ numericalFeatures }) => {
  const [selectedColumn, setSelectedColumn] = useState<string>(
    numericalFeatures[0]?.column_name || ''
  );
  const [search, setSearch] = useState<string>('');

  if (numericalFeatures.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground">
        <AlertCircle className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm font-medium text-foreground">No Numerical Features Found</p>
        <p className="text-xs mt-1">This dataset does not contain numerical columns to compute moments or histograms.</p>
      </div>
    );
  }

  const filteredFeatures = numericalFeatures.filter((f) =>
    f.column_name.toLowerCase().includes(search.toLowerCase())
  );

  const activeFeature =
    numericalFeatures.find((f) => f.column_name === selectedColumn) || numericalFeatures[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left Column: Feature Selector Sidebar */}
      <div className="lg:col-span-1 bg-card border border-border rounded-xl p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            <Hash className="w-3.5 h-3.5 text-primary" /> Numerical Features ({numericalFeatures.length})
          </h3>
        </div>

        <input
          type="text"
          placeholder="Filter features..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full text-xs px-3 py-1.5 bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
        />

        <div className="space-y-1 max-h-[500px] overflow-y-auto pr-1">
          {filteredFeatures.map((feat) => {
            const isSelected = feat.column_name === activeFeature.column_name;
            return (
              <button
                key={feat.column_name}
                onClick={() => setSelectedColumn(feat.column_name)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                  isSelected
                    ? 'bg-primary text-primary-foreground font-semibold shadow-xs'
                    : 'text-foreground hover:bg-accent/50'
                }`}
              >
                <span className="truncate">{feat.column_name}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded ${
                    isSelected
                      ? 'bg-primary-foreground/20 text-primary-foreground'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {feat.outliers_iqr_count > 0 ? `${feat.outliers_iqr_count} out` : 'clean'}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Column: Detailed Statistics & Charts */}
      <div className="lg:col-span-3 space-y-6">
        {/* Metric Header Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-foreground">{activeFeature.column_name}</h2>
                <span className="text-xs font-medium px-2 py-0.5 bg-primary/10 text-primary rounded-full">
                  Continuous (Float/Int)
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Total Sampled: <span className="font-semibold text-foreground">{activeFeature.count.toLocaleString()}</span> values
              </p>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <div className="bg-muted px-3 py-1.5 rounded-lg border border-border">
                <span className="text-muted-foreground mr-1.5">Skewness:</span>
                <span
                  className={`font-semibold ${
                    Math.abs(activeFeature.skewness) > 1.5
                      ? 'text-amber-600'
                      : 'text-foreground'
                  }`}
                >
                  {activeFeature.skewness.toFixed(3)}
                </span>
              </div>
              <div className="bg-muted px-3 py-1.5 rounded-lg border border-border">
                <span className="text-muted-foreground mr-1.5">Kurtosis:</span>
                <span className="font-semibold text-foreground">{activeFeature.kurtosis.toFixed(3)}</span>
              </div>
              <div className="bg-muted px-3 py-1.5 rounded-lg border border-border">
                <span className="text-muted-foreground mr-1.5">IQR Outliers:</span>
                <span
                  className={`font-semibold ${
                    activeFeature.outliers_iqr_count > 0 ? 'text-red-600' : 'text-emerald-600'
                  }`}
                >
                  {activeFeature.outliers_iqr_count}
                </span>
              </div>
            </div>
          </div>

          {/* Statistical Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <div className="bg-background border border-border p-2.5 rounded-lg">
              <span className="text-[11px] text-muted-foreground font-medium block">Mean</span>
              <span className="text-sm font-bold text-foreground">{activeFeature.mean.toLocaleString()}</span>
            </div>
            <div className="bg-background border border-border p-2.5 rounded-lg">
              <span className="text-[11px] text-muted-foreground font-medium block">Std Dev (σ)</span>
              <span className="text-sm font-bold text-foreground">{activeFeature.std.toLocaleString()}</span>
            </div>
            <div className="bg-background border border-border p-2.5 rounded-lg">
              <span className="text-[11px] text-muted-foreground font-medium block">Median (Q2)</span>
              <span className="text-sm font-bold text-foreground">{activeFeature.median.toLocaleString()}</span>
            </div>
            <div className="bg-background border border-border p-2.5 rounded-lg">
              <span className="text-[11px] text-muted-foreground font-medium block">Min</span>
              <span className="text-sm font-bold text-foreground">{activeFeature.min.toLocaleString()}</span>
            </div>
            <div className="bg-background border border-border p-2.5 rounded-lg">
              <span className="text-[11px] text-muted-foreground font-medium block">Max</span>
              <span className="text-sm font-bold text-foreground">{activeFeature.max.toLocaleString()}</span>
            </div>
            <div className="bg-background border border-border p-2.5 rounded-lg">
              <span className="text-[11px] text-muted-foreground font-medium block">IQR (Q3 - Q1)</span>
              <span className="text-sm font-bold text-foreground">{activeFeature.iqr.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Histogram Chart */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-primary" /> Empirical Frequency Distribution (Histogram)
            </h3>
            <span className="text-xs text-muted-foreground">
              {activeFeature.histogram.length} bins
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activeFeature.histogram} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-popover text-popover-foreground border border-border p-2.5 rounded-lg shadow-md text-xs">
                          <p className="font-semibold text-foreground">Bin: {data.label}</p>
                          <p className="text-primary font-bold mt-1">
                            Frequency: {data.count.toLocaleString()} instances
                          </p>
                          <p className="text-muted-foreground text-[10px]">
                            Range: [{data.bin_start.toFixed(2)} — {data.bin_end.toFixed(2)}]
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Boxplot & Quantile Summary Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-500" /> Five-Number Summary & Outlier Distribution
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
            <div className="bg-muted/50 p-3 rounded-lg border border-border">
              <span className="text-[11px] text-muted-foreground uppercase font-semibold">Min (Lower Whisker)</span>
              <p className="text-sm font-bold text-foreground mt-1">{activeFeature.boxplot.lower_whisker.toLocaleString()}</p>
            </div>
            <div className="bg-muted/50 p-3 rounded-lg border border-border">
              <span className="text-[11px] text-muted-foreground uppercase font-semibold">Q1 (25th Percentile)</span>
              <p className="text-sm font-bold text-foreground mt-1">{activeFeature.boxplot.q1.toLocaleString()}</p>
            </div>
            <div className="bg-primary/10 p-3 rounded-lg border border-primary/20">
              <span className="text-[11px] text-primary uppercase font-bold">Median (50th)</span>
              <p className="text-sm font-bold text-primary mt-1">{activeFeature.boxplot.median.toLocaleString()}</p>
            </div>
            <div className="bg-muted/50 p-3 rounded-lg border border-border">
              <span className="text-[11px] text-muted-foreground uppercase font-semibold">Q3 (75th Percentile)</span>
              <p className="text-sm font-bold text-foreground mt-1">{activeFeature.boxplot.q3.toLocaleString()}</p>
            </div>
            <div className="bg-muted/50 p-3 rounded-lg border border-border">
              <span className="text-[11px] text-muted-foreground uppercase font-semibold">Max (Upper Whisker)</span>
              <p className="text-sm font-bold text-foreground mt-1">{activeFeature.boxplot.upper_whisker.toLocaleString()}</p>
            </div>
          </div>

          {activeFeature.boxplot.outliers_sample.length > 0 && (
            <div className="pt-2">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-2">
                <AlertCircle className="w-3.5 h-3.5 text-red-500" />
                Detected Outlier Values Sample ({activeFeature.boxplot.outliers_count} total detected)
              </span>
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                {activeFeature.boxplot.outliers_sample.map((val, i) => (
                  <span
                    key={i}
                    className="text-[11px] font-mono px-2 py-0.5 bg-red-500/10 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900/30 rounded"
                  >
                    {val.toFixed(2)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
