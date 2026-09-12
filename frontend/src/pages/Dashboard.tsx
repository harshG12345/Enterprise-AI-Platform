import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderKanban,
  Database,
  Cpu,
  Boxes,
  CheckCircle2,
  Server,
  HardDrive,
  RefreshCw,
  Clock,
  ArrowRight,
  Zap,
  ActivitySquare,
  ShieldCheck,
  Plus,
} from 'lucide-react';
import { getHealth, getReadiness } from '../api/health';
import { getProjects } from '../api/projects';
import { datasetsApi } from '../api/datasets';
import { modelsApi } from '../api/models';
import { monitoringApi } from '../api/monitoring';
import { HealthData, ReadinessData } from '../types';
import { Project } from '../types/project';
import { ModelResponse } from '../types/models';
import { ModelMonitoringOverview } from '../types/monitoring';

export const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastCheckTime, setLastCheckTime] = useState<string>('');

  const [projectCount, setProjectCount] = useState<number>(0);
  const [datasetCount, setDatasetCount] = useState<number>(0);
  const [modelCount, setModelCount] = useState<number>(0);
  const [productionModelCount, setProductionModelCount] = useState<number>(0);
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [recentModels, setRecentModels] = useState<ModelResponse[]>([]);
  const [monitoringOverview, setMonitoringOverview] = useState<ModelMonitoringOverview[]>([]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [hRes, rRes, projRes, dataRes, modelsData, monData] = await Promise.allSettled([
        getHealth(),
        getReadiness(),
        getProjects({ page: 1, page_size: 5 }),
        datasetsApi.getDatasets({ page: 1, page_size: 5 }),
        modelsApi.listModels(),
        monitoringApi.getMonitoringOverview(),
      ]);


      if (hRes.status === 'fulfilled') setHealth(hRes.value.data);
      if (rRes.status === 'fulfilled') setReadiness(rRes.value.data);

      if (projRes.status === 'fulfilled' && projRes.value.data) {
        setProjectCount(projRes.value.data.total);
        setRecentProjects(projRes.value.data.items || []);
      }

      if (dataRes.status === 'fulfilled' && dataRes.value.data) {
        setDatasetCount(dataRes.value.data.total);
      }

      if (modelsData.status === 'fulfilled' && modelsData.value) {
        const allModels = modelsData.value;
        setModelCount(allModels.length);
        const prod = allModels.filter((m) => m.status === 'PRODUCTION');
        setProductionModelCount(prod.length);
        setRecentModels(allModels.slice(0, 5));
      }

      if (monData.status === 'fulfilled' && monData.value) {
        setMonitoringOverview(monData.value);
      }

      setLastCheckTime(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch dashboard cluster status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    {
      name: 'Active Projects',
      value: projectCount.toString(),
      change: `${projectCount} managed workspaces`,
      icon: FolderKanban,
      href: '/projects',
    },
    {
      name: 'Managed Datasets',
      value: datasetCount.toString(),
      change: `${datasetCount} validated datasets`,
      icon: Database,
      href: '/datasets',
    },
    {
      name: 'Registered Models',
      value: modelCount.toString(),
      change: `${productionModelCount} in Production`,
      icon: Boxes,
      href: '/models',
    },
    {
      name: 'Monitored Endpoints',
      value: monitoringOverview.length.toString(),
      change: `${monitoringOverview.filter((m) => m.health_status === 'HEALTHY').length} healthy models`,
      icon: ActivitySquare,
      href: '/monitoring',
    },
  ];

  const quickActions = [
    {
      title: 'New Project',
      desc: 'Create an isolated workspace',
      icon: Plus,
      href: '/projects',
      bg: 'bg-indigo-50 text-indigo-600 border-indigo-200 hover:bg-indigo-100',
    },
    {
      title: 'Ingest Dataset',
      desc: 'Upload CSV or parquet files',
      icon: Database,
      href: '/datasets',
      bg: 'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100',
    },
    {
      title: 'ML Training Wizard',
      desc: 'Cross-validation & auto tuning',
      icon: Cpu,
      href: '/training',
      bg: 'bg-purple-50 text-purple-600 border-purple-200 hover:bg-purple-100',
    },
    {
      title: 'Real-time Inference',
      desc: 'Score low-latency models',
      icon: Zap,
      href: '/predictions',
      bg: 'bg-emerald-50 text-emerald-600 border-emerald-200 hover:bg-emerald-100',
    },
  ];

  const services = [
    { name: 'FastAPI Backend Core', status: health?.status || 'Online', icon: Server, code: '200 OK' },
    { name: 'PostgreSQL Database', status: readiness?.database || 'Active', icon: HardDrive, code: 'Pool Connected' },
    { name: 'Redis Broker & Celery', status: readiness?.redis || 'Active', icon: Cpu, code: 'Queue Ready' },
    { name: 'MLflow Tracking Engine', status: readiness?.mlflow || 'Active', icon: Boxes, code: 'Artifact Store' },
  ];

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-border shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Enterprise AI Overview & Cluster Health
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time status of distributed training pipelines, model registries, and production inference nodes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Updated: {lastCheckTime || 'Syncing...'}</span>
          </div>
          <button
            type="button"
            onClick={fetchDashboardData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.href}
              className="bg-white p-5 rounded-2xl border border-border shadow-sm hover:shadow-md transition-all group block"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">{item.name}</span>
                <div className="p-2 rounded-xl bg-blue-50 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2 text-2xl font-bold text-slate-900 font-mono">{item.value}</div>
              <div className="mt-1 text-[11px] text-slate-400 flex items-center justify-between">
                <span>{item.change}</span>
                <ArrowRight className="w-3 h-3 text-slate-300 group-hover:text-primary transition-colors" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Launch Actions */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-xs">
          Quick Launch Workflows
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const ActionIcon = action.icon;
            return (
              <Link
                key={action.title}
                to={action.href}
                className={`p-4 rounded-xl border flex items-center gap-3.5 transition-all ${action.bg} shadow-2xs`}
              >
                <div className="p-2 rounded-lg bg-white/80 shadow-2xs">
                  <ActionIcon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold">{action.title}</div>
                  <div className="text-[10px] opacity-80">{action.desc}</div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Recent Workspaces & Models */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <div className="bg-white p-6 rounded-2xl border border-border shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Active Workspaces</h2>
              <p className="text-[11px] text-slate-400">Recently managed project environments</p>
            </div>
            <Link
              to="/projects"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {recentProjects.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
              No projects created yet. Click "New Project" to start.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentProjects.map((p) => (
                <Link
                  key={p.id}
                  to={`/projects/${p.id}`}
                  className="py-3 px-2 flex items-center justify-between hover:bg-slate-50 rounded-lg transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-slate-100 text-slate-600 group-hover:bg-primary/10 group-hover:text-primary">
                      <FolderKanban className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">
                        {p.name}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {p.dataset_count || 0} datasets • {p.model_count || 0} models
                      </div>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    {new Date(p.created_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Registered Model Champions */}
        <div className="bg-white p-6 rounded-2xl border border-border shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Model Registry Champions</h2>
              <p className="text-[11px] text-slate-400">Production & Staging lifecycle catalog</p>
            </div>
            <Link
              to="/models"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              View Registry <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {recentModels.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
              No models registered yet. Train a model in Training Wizard.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentModels.map((m) => (
                <Link
                  key={m.id}
                  to={`/models/${m.id}`}
                  className="py-3 px-2 flex items-center justify-between hover:bg-slate-50 rounded-lg transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-slate-100 text-slate-600 group-hover:bg-primary/10 group-hover:text-primary">
                      <Boxes className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">
                        {m.name} ({m.version})
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {m.task_type} • {m.framework}
                      </div>

                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        m.status === 'PRODUCTION'
                          ? 'bg-emerald-100 text-emerald-800'
                          : m.status === 'STAGING'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {m.status}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Cluster Health & Architecture Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Services Status */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-border shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Distributed Services Status</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-green-50 text-status-success font-medium border border-green-200 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              Operational Cluster
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {services.map((svc) => {
              const SvcIcon = svc.icon;
              return (
                <div
                  key={svc.name}
                  className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-3.5"
                >
                  <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-slate-700 shadow-2xs">
                    <SvcIcon className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-slate-900 truncate">{svc.name}</div>
                    <div className="flex items-center gap-1.5 mt-1 text-[11px] text-slate-500 font-mono">
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
                      <span className="capitalize">{svc.status}</span>
                      <span>•</span>
                      <span className="text-slate-400">{svc.code}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* System Metadata Card */}
        <div className="bg-white p-6 rounded-2xl border border-border shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Platform Runtime Details</h2>
            <dl className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <dt className="text-slate-500">App Name</dt>
                <dd className="font-semibold text-slate-800">{health?.app_name || 'Enterprise AI Platform'}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <dt className="text-slate-500">Version</dt>
                <dd className="font-mono text-slate-800">{health?.version || '1.0.0'}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <dt className="text-slate-500">Environment</dt>
                <dd className="font-mono uppercase text-primary font-semibold">
                  {health?.environment || 'Development'}
                </dd>
              </div>
              <div className="flex justify-between py-1">
                <dt className="text-slate-500">FastAPI OpenAPI</dt>
                <dd className="text-primary hover:underline font-mono">
                  <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
                    /docs ↗
                  </a>
                </dd>
              </div>
            </dl>
          </div>

          <div className="mt-6 p-3 rounded-xl bg-blue-50/70 border border-blue-100 text-[11px] text-blue-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
            <span>Enterprise governance, JWT RBAC security, and Celery task execution active.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

