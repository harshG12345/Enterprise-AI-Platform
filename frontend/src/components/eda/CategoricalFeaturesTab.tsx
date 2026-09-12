import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts';
import {
  AlertCircle,
  BarChartHorizontal,
  Layers,
  Tag,
} from 'lucide-react';
import { CategoricalColumnStats } from '../../types/eda';

interface CategoricalFeaturesTabProps {
  categoricalFeatures: CategoricalColumnStats[];
}

const PALETTE = [
  '#2563eb',
  '#4f46e5',
  '#7c3aed',
  '#9333ea',
  '#c026d3',
  '#db2777',
  '#e11d48',
  '#ea580c',
  '#d97706',
  '#65a30d',
  '#16a34a',
  '#0d9488',
];

export const CategoricalFeaturesTab: React.FC<CategoricalFeaturesTabProps> = ({
  categoricalFeatures,
}) => {
  const [selectedColumn, setSelectedColumn] = useState<string>(
    categoricalFeatures[0]?.column_name || ''
  );
  const [search, setSearch] = useState<string>('');

  if (categoricalFeatures.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground">
        <AlertCircle className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm font-medium text-foreground">No Categorical Features Found</p>
        <p className="text-xs mt-1">This dataset does not contain string or categorical columns.</p>
      </div>
    );
  }

  const filteredFeatures = categoricalFeatures.filter((f) =>
    f.column_name.toLowerCase().includes(search.toLowerCase())
  );

  const activeFeature =
    categoricalFeatures.find((f) => f.column_name === selectedColumn) || categoricalFeatures[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left Column: Feature Selector Sidebar */}
      <div className="lg:col-span-1 bg-card border border-border rounded-xl p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-indigo-500" /> Categorical ({categoricalFeatures.length})
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
                    ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                    : 'text-foreground hover:bg-accent/50'
                }`}
              >
                <span className="truncate">{feat.column_name}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded ${
                    isSelected
                      ? 'bg-white/20 text-white'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {feat.unique_count} distinct
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Column: Detailed Categorical Inspection */}
      <div className="lg:col-span-3 space-y-6">
        {/* Metric Header Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-foreground">{activeFeature.column_name}</h2>
                <span className="text-xs font-medium px-2 py-0.5 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-full">
                  Discrete Categorical
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Total Valid Records: <span className="font-semibold text-foreground">{activeFeature.count.toLocaleString()}</span>
              </p>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <div className="bg-muted px-3 py-1.5 rounded-lg border border-border">
                <span className="text-muted-foreground mr-1.5">Cardinality:</span>
                <span
                  className={`font-semibold ${
                    activeFeature.is_high_cardinality ? 'text-amber-600' : 'text-foreground'
                  }`}
                >
                  {activeFeature.unique_count.toLocaleString()} unique
                </span>
              </div>
              <div className="bg-muted px-3 py-1.5 rounded-lg border border-border">
                <span className="text-muted-foreground mr-1.5">Unique Ratio:</span>
                <span className="font-semibold text-foreground">
                  {(activeFeature.unique_ratio * 100).toFixed(1)}%
                </span>
              </div>
              <div className="bg-muted px-3 py-1.5 rounded-lg border border-border">
                <span className="text-muted-foreground mr-1.5">Top Category:</span>
                <span className="font-semibold text-primary">{activeFeature.top_value || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Quick Warning / Tip */}
          {activeFeature.is_high_cardinality && (
            <div className="bg-amber-500/10 border border-amber-200 dark:border-amber-900/30 p-3 rounded-lg flex items-start gap-2.5 text-xs text-amber-800 dark:text-amber-300">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">High Cardinality Feature: </span>
                This column contains {activeFeature.unique_count} distinct categories. One-hot encoding will generate {activeFeature.unique_count} sparse columns. Target encoding or frequency encoding is recommended during Phase 7 preprocessing.
              </div>
            </div>
          )}
        </div>

        {/* Frequency Distribution Chart */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
            <BarChartHorizontal className="w-4 h-4 text-indigo-500" /> Category Frequency Distribution
          </h3>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={activeFeature.frequencies}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 60, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                <XAxis type="number" tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                <YAxis
                  type="category"
                  dataKey="value"
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  width={90}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-popover text-popover-foreground border border-border p-2.5 rounded-lg shadow-md text-xs">
                          <p className="font-semibold text-foreground">{data.value}</p>
                          <p className="text-primary font-bold mt-1">
                            Count: {data.count.toLocaleString()} instances
                          </p>
                          <p className="text-muted-foreground text-[10px]">
                            Share: {data.percentage.toFixed(2)}% of total
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {activeFeature.frequencies.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tabular Breakdown */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-indigo-500" /> Category Frequency Table
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted text-muted-foreground uppercase font-semibold border-b border-border">
                <tr>
                  <th className="px-3 py-2">Category Value</th>
                  <th className="px-3 py-2 text-right">Frequency Count</th>
                  <th className="px-3 py-2 text-right">Percentage (%)</th>
                  <th className="px-3 py-2">Relative Proportion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {activeFeature.frequencies.map((item, idx) => (
                  <tr key={idx} className="hover:bg-accent/30">
                    <td className="px-3 py-2 font-medium text-foreground">{item.value}</td>
                    <td className="px-3 py-2 text-right font-mono font-semibold text-foreground">
                      {item.count.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-muted-foreground">
                      {item.percentage.toFixed(1)}%
                    </td>
                    <td className="px-3 py-2">
                      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full"
                          style={{
                            width: `${item.percentage}%`,
                            backgroundColor: PALETTE[idx % PALETTE.length],
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
