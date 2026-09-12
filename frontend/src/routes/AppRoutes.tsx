import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Dashboard } from '../pages/Dashboard';
import { Datasets } from '../pages/Datasets';
import { DatasetDetails } from '../pages/DatasetDetails';
import { EDA } from '../pages/EDA';
import { Preprocessing } from '../pages/Preprocessing';
import { Projects } from '../pages/Projects';
import { ProjectDetails } from '../pages/ProjectDetails';
import { Training } from '../pages/Training';
import { Experiments } from '../pages/Experiments';
import { Models } from '../pages/Models';
import { ModelDetails } from '../pages/ModelDetails';
import { Predictions } from '../pages/Predictions';
import { Monitoring } from '../pages/Monitoring';
import { Settings } from '../pages/Settings';
import { Login } from '../pages/auth/Login';
import { Register } from '../pages/auth/Register';
import { ForgotPassword } from '../pages/auth/ForgotPassword';
import { ProtectedRoute } from './ProtectedRoute';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Authentication Pages */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Authenticated Application Pages */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route path="/dashboard" element={<Navigate to="/" replace />} />

      {/* Project Management Routes */}
      <Route
        path="/projects"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Projects />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/projects/:projectId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ProjectDetails />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      {/* Dataset Management Routes */}
      <Route
        path="/datasets"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Datasets />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/datasets/:datasetId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <DatasetDetails />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/datasets/:datasetId/eda"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <EDA />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/datasets/:datasetId/preprocess"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Preprocessing />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/training"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Training />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/experiments"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Experiments />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      {/* Model Registry & Governance Routes */}
      <Route
        path="/models"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Models />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/models/:modelId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ModelDetails />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      {/* Real-time & Batch Inference Routes */}
      <Route
        path="/predictions"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Predictions />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      {/* Observability & Statistical Drift Engine Routes */}
      <Route
        path="/monitoring"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Monitoring />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Settings />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />


      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
