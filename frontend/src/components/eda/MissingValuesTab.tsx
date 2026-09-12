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
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Search,
  ShieldAlert,
} from 'lucide-react';
import { ColumnMissingSummary } from '../../types/eda';

interface MissingValuesTabProps {
  missingSummary: ColumnMissingSummary[];
}

export const MissingValuesTab: React.FC<MissingValuesTabProps> = ({ missingSummary }) => {
  const [search, setSearch] = useState<string>('');

  const cleanCols = missingSummary.filter((c) => c.missing_count === 0);
  const mildCols = missingSummary.filter(
    (c) => c.missing_count > 0 && c.missing_percentage < 20
  );
  const severeCols = missingSummary.filter((c) => c.missing_percentage >= 20);

  const filtered = missingSummary.filter((c) =>
    c.column_name.toLowerCase().includes(search.toLowerCase())
  );

  // Sort descending by missing percentage for chart
  const chartData = [...missingSummary]
    .sort((a, b) => b.missing_percentage - a.missing_percentage)
    .slice(0, 15);

  const getMissingColor = (pct: number) => {
    if (pct === 0) return '#10b981'; // green
    if (pct < 20) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="space-y-6">
      {/* Top Missing Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border p-4 rounded-xl shadow-xs flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase">100% Complete Columns</span>
            <div className="text-xl font-bold text-foreground">{cleanCols.length}</div>
            <div className="text-[11px] text-muted-foreground">Zero missing cells</div>
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase">Mild Missing (&lt;20%)</span>
            <div className="text-xl font-bold text-foreground">{mildCols.length}</div>
            <div className="text-[11px] text-muted-foreground">Imputable features</div>
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-xl shadow-xs flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
            <ShieldAlert className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase">Severe Missing (&ge;20%)</span>
            <div className="text-xl font-bold text-foreground">{severeCols.length}</div>
            <div className="text-[11px] text-muted-foreground">Requires attention/drop</div>
          </div>
        </div>
      </div>

      {/* Missingness Rate Chart */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-amber-500" /> Top Missingness Rates by Feature
          </h3>
          <span className="text-xs text-muted-foreground">Top {chartData.length} columns</span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 80, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
              <XAxis
                type="number"
                unit="%"
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                type="category"
                dataKey="column_name"
                tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                width={100}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as ColumnMissingSummary;
                    return (
                      <div className="bg-popover text-popover-foreground border border-border p-2.5 rounded-lg shadow-md text-xs">
                        <p className="font-semibold text-foreground">{data.column_name}</p>
                        <p className="text-red-500 font-bold mt-1">
                          Missing: {data.missing_percentage.toFixed(1)}% ({data.missing_count.toLocaleString()} rows)
                        </p>
                        <p className="text-emerald-600 font-medium">
                          Valid: {data.valid_count.toLocaleString()} rows
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="missing_percentage" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getMissingColor(entry.missing_percentage)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Comprehensive Missingness Table */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-foreground">Column Completeness Matrix</h3>
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search column..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-muted text-muted-foreground uppercase font-semibold border-b border-border">
              <tr>
                <th className="px-3 py-2">Column Name</th>
                <th className="px-3 py-2">Data Type</th>
                <th className="px-3 py-2 text-right">Missing Count</th>
                <th className="px-3 py-2 text-right">Missing (%)</th>
                <th className="px-3 py-2 text-right">Valid Records</th>
                <th className="px-3 py-2">Data Health Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((col) => (
                <tr key={col.column_name} className="hover:bg-accent/30">
                  <td className="px-3 py-2 font-medium text-foreground">{col.column_name}</td>
                  <td className="px-3 py-2 font-mono text-muted-foreground">{col.data_type}</td>
                  <td className="px-3 py-2 text-right font-mono font-semibold text-foreground">
                    {col.missing_count.toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right font-mono font-semibold">
                    <span
                      className={
                        col.missing_percentage === 0
                          ? 'text-emerald-600'
                          : col.missing_percentage < 20
                          ? 'text-amber-600'
                          : 'text-red-600'
                      }
                    >
                      {col.missing_percentage.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-muted-foreground">
                    {col.valid_count.toLocaleString()} ({col.valid_percentage.toFixed(1)}%)
                  </td>
                  <td className="px-3 py-2">
                    {col.missing_percentage === 0 ? (
                      <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 font-medium">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Complete
                      </span>
                    ) : col.missing_percentage < 20 ? (
                      <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 font-medium">
                        <AlertTriangle className="w-3 h-3 text-amber-600" /> Moderate Missing
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-700 font-medium">
                        <ShieldAlert className="w-3 h-3 text-red-600" /> Critical Missing
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
