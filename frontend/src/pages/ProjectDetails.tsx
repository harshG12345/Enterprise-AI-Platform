import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FolderKanban,
  Database,
  ArrowLeft,
  Calendar,
  User as UserIcon,
  Plus,
  Loader2,
  AlertCircle,
  FileSpreadsheet,
  ExternalLink,
  Cpu,
} from 'lucide-react';
import { getProject } from '../api/projects';

export const ProjectDetails: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'datasets' | 'experiments' | 'models'>(
    'overview'
  );

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });

  if (isLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center bg-white rounded-xl border border-border">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="text-xs font-medium text-slate-500 mt-2">Loading workspace details...</span>
      </div>
    );
  }

  if (isError || !data?.data) {
    return (
      <div className="p-8 max-w-xl mx-auto bg-white border border-red-200 rounded-xl shadow-sm text-center">
        <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
        <h2 className="text-sm font-bold text-slate-900">Project Workspace Not Found</h2>
        <p className="text-xs text-slate-500 mt-1">
          {(error as { message?: string })?.message ||
            'The requested project workspace could not be located or you lack access.'}
        </p>
        <Link
          to="/projects"
          className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Projects
        </Link>
      </div>
    );
  }

  const project = data.data;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Link to="/projects" className="hover:text-primary transition-colors">
          Projects
        </Link>
        <span>/</span>
        <span className="font-semibold text-slate-900 truncate">{project.name}</span>
      </div>

      {/* Project Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-blue-50 text-primary">
            <FolderKanban className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-mono">
                ID: {project.id.slice(0, 8)}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              {project.description || 'No detailed description provided for this workspace.'}
            </p>
            <div className="flex items-center gap-4 mt-3 text-[11px] text-slate-400">
              <div className="flex items-center gap-1.5">
                <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                <span>Owner: {project.owner_name || project.owner_email || 'You'}</span>
              </div>
              <span>•</span>
              <div className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Launch Actions */}
        <div className="flex items-center gap-2">
          <Link
            to="/datasets"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors shadow-2xs"
          >
            <Database className="w-3.5 h-3.5 text-primary" />
            Upload Dataset
          </Link>
          <Link
            to="/training"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold transition-colors shadow-sm"
          >
            <Cpu className="w-3.5 h-3.5" />
            Launch Training
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-border flex gap-6 text-xs font-semibold">
        {[
          { id: 'overview', label: 'Overview', count: null },
          { id: 'datasets', label: 'Datasets', count: project.dataset_count },
          { id: 'experiments', label: 'Experiments', count: project.experiment_count },
          { id: 'models', label: 'Models', count: project.model_count },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`pb-3 relative transition-colors flex items-center gap-2 ${
              activeTab === tab.id
                ? 'text-primary border-b-2 border-primary font-bold'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <span>{tab.label}</span>
            {tab.count !== null && (
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-primary'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
                <span className="text-xs text-slate-500 font-medium">Ingested Datasets</span>
                <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                  {project.dataset_count}
                </div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
                <span className="text-xs text-slate-500 font-medium">MLflow Experiment Runs</span>
                <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                  {project.experiment_count}
                </div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-border shadow-sm">
                <span className="text-xs text-slate-500 font-medium">Registered Models</span>
                <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                  {project.model_count}
                </div>
              </div>
            </div>

            {/* Datasets Preview */}
            <div className="bg-white p-5 rounded-xl border border-border shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-900">Project Datasets</h3>
                <Link
                  to="/datasets"
                  className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                >
                  Manage All <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
              {project.datasets.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  No datasets uploaded yet to this project.
                </p>
              ) : (
                <div className="divide-y divide-slate-100">
                  {project.datasets.map((d) => (
                    <div key={d.id} className="py-2.5 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <FileSpreadsheet className="w-4 h-4 text-primary" />
                        <span className="font-semibold text-slate-800">{d.filename}</span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          ({d.row_count || 0} rows, {d.column_count || 0} cols)
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-green-50 text-status-success text-[10px] font-semibold border border-green-200">
                        {d.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Models & Artifacts */}
          <div className="bg-white p-5 rounded-xl border border-border shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Model Governance</h3>
              <p className="text-xs text-slate-500 mb-4">
                Models trained within this workspace can be versioned and promoted to Staging or
                Production.
              </p>
              <div className="space-y-2.5">
                {project.models.length === 0 ? (
                  <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-400">
                    No trained models in registry.
                  </div>
                ) : (
                  project.models.map((m) => (
                    <div
                      key={m.id}
                      className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg text-xs"
                    >
                      <div className="flex items-center justify-between font-semibold text-slate-900">
                        <span>{m.name}</span>
                        <span className="text-primary font-mono text-[11px]">{m.version}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 capitalize mt-0.5">
                        {m.task_type} • Status: {m.status}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={() => navigate('/training')}
              className="mt-6 w-full py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center justify-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" /> Start Training Pipeline
            </button>
          </div>
        </div>
      )}

      {/* Tab Content: Datasets */}
      {activeTab === 'datasets' && (
        <div className="bg-white p-6 rounded-xl border border-border shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Workspace Ingested Datasets</h3>
            <Link
              to="/datasets"
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary-hover"
            >
              <Plus className="w-3.5 h-3.5" /> Upload Dataset
            </Link>
          </div>

          {project.datasets.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No datasets found in this workspace. Click upload to attach CSV/XLSX tabular data.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="py-2.5 font-semibold">Filename</th>
                    <th className="py-2.5 font-semibold">Dimensions</th>
                    <th className="py-2.5 font-semibold">Size</th>
                    <th className="py-2.5 font-semibold">Status</th>
                    <th className="py-2.5 font-semibold">Uploaded</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {project.datasets.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 font-semibold text-slate-800">{d.filename}</td>
                      <td className="py-3 font-mono text-slate-600">
                        {d.row_count || 0} rows × {d.column_count || 0} cols
                      </td>
                      <td className="py-3 font-mono text-slate-600">
                        {(d.file_size / (1024 * 1024)).toFixed(2)} MB
                      </td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded-full bg-green-50 text-status-success font-semibold text-[10px] border border-green-200">
                          {d.status}
                        </span>
                      </td>
                      <td className="py-3 text-slate-400">
                        {new Date(d.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab Content: Experiments */}
      {activeTab === 'experiments' && (
        <div className="bg-white p-6 rounded-xl border border-border shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">MLflow Experiment Runs</h3>
          {project.experiments.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No experiment runs recorded for this project yet. Start a training job to log runs.
            </div>
          ) : (
            <div className="space-y-3">
              {project.experiments.map((e) => (
                <div
                  key={e.id}
                  className="p-3 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-semibold text-slate-800">{e.name}</span>
                    <div className="text-[11px] text-slate-400 font-mono">
                      MLflow ID: {e.mlflow_experiment_id || 'Auto-generated'}
                    </div>
                  </div>
                  <span className="text-slate-400 text-[11px]">
                    {new Date(e.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab Content: Models */}
      {activeTab === 'models' && (
        <div className="bg-white p-6 rounded-xl border border-border shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Registered Models</h3>
          {project.models.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No trained models registered in this workspace yet.
            </div>
          ) : (
            <div className="space-y-3">
              {project.models.map((m) => (
                <div
                  key={m.id}
                  className="p-4 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800 text-sm">{m.name}</span>
                      <span className="px-2 py-0.5 bg-blue-50 text-primary font-mono text-[10px] rounded font-semibold">
                        {m.version}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1 capitalize">
                      {m.task_type} • Status: <span className="font-semibold">{m.status}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-slate-400">
                      {new Date(m.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
