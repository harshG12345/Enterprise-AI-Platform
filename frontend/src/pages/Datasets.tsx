import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Database,
  UploadCloud,
  Search,
  Trash2,
  ExternalLink,
  Calendar,
  X,
  Loader2,
  AlertCircle,
  FileSpreadsheet,
  CheckCircle2,
} from 'lucide-react';
import { getDatasets, uploadDataset, deleteDataset } from '../api/datasets';
import { getProjects } from '../api/projects';
import { Dataset } from '../types/dataset';

export const Datasets: React.FC = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadProjectId, setUploadProjectId] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Projects list query for dropdowns
  const { data: projectsData } = useQuery({
    queryKey: ['projects_list_dropdown'],
    queryFn: () => getProjects({ page_size: 100 }),
  });

  // Datasets query
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['datasets', selectedProjectId, searchTerm],
    queryFn: () =>
      getDatasets({
        project_id: selectedProjectId || undefined,
        search: searchTerm || undefined,
      }),
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!uploadFile || !uploadProjectId) {
        throw new Error('Please select both a target project and a dataset file.');
      }
      return uploadDataset(uploadProjectId, uploadFile, (percent) => {
        setUploadProgress(percent);
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsUploadModalOpen(false);
      setUploadFile(null);
      setUploadProgress(0);
      setUploadError(null);
    },
    onError: (err: unknown) => {
      const e = err as { message?: string };
      setUploadError(e.message || 'Dataset upload failed. Please verify file format.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setDeleteConfirmId(null);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setUploadFile(e.dataTransfer.files[0]);
      setUploadError(null);
    }
  };

  const datasetsList = data?.data?.items || [];
  const totalDatasets = data?.data?.total || 0;
  const projects = projectsData?.data?.items || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-border shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Dataset Repository</h1>
            <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-primary text-xs font-semibold border border-blue-100">
              {totalDatasets} Managed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Ingest, profile, and inspect tabular data (CSV / XLSX) with zero data leakage.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            if (projects.length > 0 && !uploadProjectId) {
              setUploadProjectId(projects[0].id);
            }
            setIsUploadModalOpen(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Dataset
        </button>
      </div>

      {/* Filters & Workspace Switcher */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-white p-4 rounded-xl border border-border shadow-sm">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search datasets by filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-border rounded-lg text-xs bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
          />
        </div>

        <div>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg text-xs bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="">All Workspaces</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading && (
        <div className="p-16 flex flex-col items-center justify-center bg-white rounded-xl border border-border">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="text-xs font-medium text-slate-500 mt-2">Loading datasets...</span>
        </div>
      )}

      {isError && (
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-status-error text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>Failed to load datasets: {(error as { message?: string })?.message || 'Unknown error'}</span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && datasetsList.length === 0 && (
        <div className="p-12 text-center bg-white rounded-xl border border-dashed border-slate-300">
          <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
            <Database className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">No tabular datasets found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Upload a CSV or XLSX spreadsheet to start exploratory analysis and model training.
          </p>
          <button
            type="button"
            onClick={() => {
              if (projects.length > 0 && !uploadProjectId) {
                setUploadProjectId(projects[0].id);
              }
              setIsUploadModalOpen(true);
            }}
            className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5" /> Upload Dataset
          </button>
        </div>
      )}

      {/* Datasets Table */}
      {!isLoading && !isError && datasetsList.length > 0 && (
        <div className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-border text-slate-500">
                  <th className="py-3 px-5 font-semibold">Dataset Name</th>
                  <th className="py-3 px-4 font-semibold">Rows × Columns</th>
                  <th className="py-3 px-4 font-semibold">File Size</th>
                  <th className="py-3 px-4 font-semibold">Validation Status</th>
                  <th className="py-3 px-4 font-semibold">Uploaded</th>
                  <th className="py-3 px-5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datasetsList.map((dataset: Dataset) => (
                  <tr key={dataset.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-5">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-blue-50 text-primary">
                          <FileSpreadsheet className="w-4 h-4" />
                        </div>
                        <div>
                          <Link
                            to={`/datasets/${dataset.id}`}
                            className="font-semibold text-slate-900 hover:text-primary transition-colors line-clamp-1"
                          >
                            {dataset.filename}
                          </Link>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ID: {dataset.id.slice(0, 8)}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-slate-700">
                      {dataset.row_count != null && dataset.column_count != null ? (
                        <span>
                          {Number(dataset.row_count).toLocaleString()} × {dataset.column_count}
                        </span>
                      ) : (
                        <span className="text-slate-400">Processing...</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 font-mono text-slate-600">
                      {(dataset.file_size / (1024 * 1024)).toFixed(2)} MB
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-status-success font-semibold text-[10px] border border-green-200">
                        <CheckCircle2 className="w-3 h-3" />
                        {dataset.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-500 text-[11px]">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{new Date(dataset.created_at).toLocaleDateString()}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-5 text-right space-x-2">
                      <Link
                        to={`/datasets/${dataset.id}`}
                        title="View Preview & Schema"
                        className="inline-flex items-center gap-1 p-1.5 rounded-lg border border-border text-slate-700 hover:bg-slate-100 transition-colors shadow-2xs text-[11px] font-semibold"
                      >
                        Inspect <ExternalLink className="w-3 h-3 text-slate-400" />
                      </Link>

                      <button
                        type="button"
                        onClick={() => setDeleteConfirmId(dataset.id)}
                        title="Delete Dataset"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-status-error hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Dataset Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-lg rounded-xl border border-border shadow-xl overflow-hidden animate-scaleIn">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">Upload Tabular Dataset</h3>
              <button
                type="button"
                onClick={() => setIsUploadModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {uploadError && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-status-error text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Project Workspace
                </label>
                <select
                  value={uploadProjectId}
                  onChange={(e) => setUploadProjectId(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="">Select a workspace...</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                  uploadFile
                    ? 'border-primary bg-blue-50/30'
                    : 'border-slate-300 hover:border-primary hover:bg-slate-50'
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".csv,.xlsx,.xls"
                  className="hidden"
                />

                <div className="w-12 h-12 rounded-full bg-blue-50 text-primary flex items-center justify-center mx-auto mb-3">
                  <UploadCloud className="w-6 h-6" />
                </div>

                {uploadFile ? (
                  <div>
                    <span className="text-xs font-semibold text-slate-900">{uploadFile.name}</span>
                    <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                      {(uploadFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                    <span className="text-[10px] text-primary font-semibold mt-2 inline-block">
                      Click to choose a different file
                    </span>
                  </div>
                ) : (
                  <div>
                    <span className="text-xs font-semibold text-slate-900">
                      Click to upload or drag & drop
                    </span>
                    <p className="text-[11px] text-slate-500 mt-1">
                      Supported formats: CSV, XLSX (Max size: 250 MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Progress Bar */}
              {uploadMutation.isPending && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[11px] font-mono text-slate-600">
                    <span>Uploading & extracting schema...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsUploadModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-border text-slate-700 text-xs font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => uploadMutation.mutate()}
                  disabled={!uploadFile || !uploadProjectId || uploadMutation.isPending}
                  className="px-4 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing...
                    </>
                  ) : (
                    'Upload & Profile Dataset'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-sm rounded-xl border border-border shadow-xl p-6 space-y-4">
            <div className="w-10 h-10 rounded-full bg-red-50 text-status-error flex items-center justify-center">
              <Trash2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Delete Dataset?</h3>
              <p className="text-xs text-slate-500 mt-1">
                This will permanently remove the physical file from storage and delete all associated
                schema metadata.
              </p>
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmId(null)}
                className="px-3 py-1.5 rounded-lg border border-border text-slate-700 text-xs font-medium hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => deleteMutation.mutate(deleteConfirmId)}
                disabled={deleteMutation.isPending}
                className="px-4 py-1.5 rounded-lg bg-status-error hover:bg-red-700 text-white text-xs font-semibold shadow-sm flex items-center gap-1.5 disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
