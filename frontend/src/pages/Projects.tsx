import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'react-router-dom';
import {
  FolderKanban,
  Plus,
  Search,
  Database,
  Boxes,
  FlaskConical,
  Trash2,
  ExternalLink,
  Calendar,
  X,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { getProjects, createProject, deleteProject } from '../api/projects';
import { ProjectCreateFormData, projectCreateSchema } from '../schemas/project';
import { Project } from '../types/project';

export const Projects: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['projects', searchTerm],
    queryFn: () => getProjects({ search: searchTerm || undefined }),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectCreateFormData>({
    resolver: zodResolver(projectCreateSchema),
    defaultValues: { name: '', description: '' },
  });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      reset();
      setIsModalOpen(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setDeleteConfirmId(null);
    },
  });

  const onSubmit = (formData: ProjectCreateFormData) => {
    createMutation.mutate(formData);
  };

  const projectsList = data?.data?.items || [];
  const totalProjects = data?.data?.total || 0;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-border shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Project Workspaces</h1>
            <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-primary text-xs font-semibold border border-blue-100">
              {totalProjects} Active
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Organize machine learning workflows, datasets, and registered model pipelines.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Project
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-border shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search projects by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-border rounded-lg text-xs bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading && (
        <div className="p-16 flex flex-col items-center justify-center bg-white rounded-xl border border-border">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="text-xs font-medium text-slate-500 mt-2">Loading workspaces...</span>
        </div>
      )}

      {isError && (
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-status-error text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>Failed to load projects: {(error as { message?: string })?.message || 'Unknown error'}</span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && projectsList.length === 0 && (
        <div className="p-12 text-center bg-white rounded-xl border border-dashed border-slate-300">
          <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
            <FolderKanban className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">No project workspaces found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Get started by creating your first machine learning project workspace.
          </p>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" /> Create Project
          </button>
        </div>
      )}

      {/* Projects Grid */}
      {!isLoading && !isError && projectsList.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projectsList.map((project: Project) => (
            <div
              key={project.id}
              className="bg-white rounded-xl border border-border shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between overflow-hidden group"
            >
              <div className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-blue-50 text-primary">
                      <FolderKanban className="w-4 h-4" />
                    </div>
                    <Link
                      to={`/projects/${project.id}`}
                      className="text-sm font-semibold text-slate-900 group-hover:text-primary transition-colors line-clamp-1"
                    >
                      {project.name}
                    </Link>
                  </div>

                  <button
                    type="button"
                    onClick={() => setDeleteConfirmId(project.id)}
                    title="Delete Project"
                    className="text-slate-400 hover:text-status-error p-1 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-xs text-slate-500 mt-3 line-clamp-2 min-h-[32px]">
                  {project.description || 'No description provided.'}
                </p>

                {/* Metric Counters */}
                <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-100 text-center">
                  <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center justify-center gap-1 text-slate-500 text-[10px]">
                      <Database className="w-3 h-3 text-slate-400" /> Datasets
                    </div>
                    <span className="text-xs font-bold text-slate-800 font-mono">
                      {project.dataset_count}
                    </span>
                  </div>

                  <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center justify-center gap-1 text-slate-500 text-[10px]">
                      <FlaskConical className="w-3 h-3 text-slate-400" /> Runs
                    </div>
                    <span className="text-xs font-bold text-slate-800 font-mono">
                      {project.experiment_count}
                    </span>
                  </div>

                  <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center justify-center gap-1 text-slate-500 text-[10px]">
                      <Boxes className="w-3 h-3 text-slate-400" /> Models
                    </div>
                    <span className="text-xs font-bold text-slate-800 font-mono">
                      {project.model_count}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
                <Link
                  to={`/projects/${project.id}`}
                  className="flex items-center gap-1 font-semibold text-primary hover:underline"
                >
                  Explore <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-md rounded-xl border border-border shadow-xl overflow-hidden animate-scaleIn">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">Create New Project</h3>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
              {createMutation.isError && (
                <div className="p-3 rounded-lg bg-red-50 text-status-error text-xs">
                  {(createMutation.error as { message?: string })?.message || 'Failed to create project'}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Project Workspace Name
                </label>
                <input
                  type="text"
                  {...register('name')}
                  placeholder="e.g., Credit Risk Assessment"
                  className="w-full px-3 py-2 border border-border rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                {errors.name && (
                  <p className="mt-1 text-[11px] text-status-error">{errors.name.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  {...register('description')}
                  rows={3}
                  placeholder="Describe the ML objective, target domain, and business metrics..."
                  className="w-full px-3 py-2 border border-border rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-border text-slate-700 text-xs font-medium hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || createMutation.isPending}
                  className="px-4 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Creating...
                    </>
                  ) : (
                    'Create Workspace'
                  )}
                </button>
              </div>
            </form>
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
              <h3 className="text-sm font-semibold text-slate-900">Delete Project Workspace?</h3>
              <p className="text-xs text-slate-500 mt-1">
                This action is permanent and will cascade deletion to all associated datasets,
                experiments, and model artifacts.
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
