import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Key,
  Database,
  Activity,
  CheckCircle2,
  Lock,
  Clock,
  HardDrive,
  Copy,
  Check,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export const Settings: React.FC = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'cluster' | 'audit'>('profile');
  const [copiedKey, setCopiedKey] = useState(false);

  const mockApiKey = 'agy_sec_99a8f4c21b34e899201a0f9b3e';

  const handleCopyKey = () => {
    navigator.clipboard.writeText(mockApiKey);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const auditEvents = [
    {
      id: '1',
      action: 'MODEL_PROMOTED_TO_PRODUCTION',
      details: 'RandomForest Classifier promoted by user',
      timestamp: new Date().toISOString(),
      user: user?.email || 'admin@enterprise.ai',
    },
    {
      id: '2',
      action: 'BATCH_PREDICTION_JOB_LAUNCHED',
      details: 'Evaluated 1,000 rows on XGBoost Regression',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      user: user?.email || 'admin@enterprise.ai',
    },
    {
      id: '3',
      action: 'DATASET_INGESTION_COMPLETED',
      details: 'Uploaded telemetry_sensors.csv (14,500 rows)',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      user: user?.email || 'admin@enterprise.ai',
    },
  ];

  return (
    <div className="space-y-6 pb-16 animate-fadeIn">
      {/* Top Header */}
      <div className="border-b border-border pb-5">
        <div className="flex items-center gap-2">
          <span className="p-2 rounded-lg bg-primary/10 text-primary">
            <SettingsIcon className="h-6 w-6 text-primary" />
          </span>
          <h1 className="text-2xl font-bold text-slate-900">System & User Settings</h1>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Manage user profiles, access controls, API authentication credentials, and platform audit logs.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'profile'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <User className="w-4 h-4" /> User Profile
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'security'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Key className="w-4 h-4" /> API Credentials
        </button>
        <button
          onClick={() => setActiveTab('cluster')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'cluster'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Database className="w-4 h-4" /> Cluster Environment
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === 'audit'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Activity className="w-4 h-4" /> Audit Log
        </button>
      </div>

      {/* Content */}
      {activeTab === 'profile' && (
        <div className="bg-white rounded-2xl border border-border p-6 shadow-sm max-w-2xl space-y-6">
          <div className="flex items-center gap-4 border-b border-slate-100 pb-5">
            <div className="w-14 h-14 rounded-2xl bg-primary text-white flex items-center justify-center font-bold text-xl uppercase shadow-md shadow-primary/20">
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">{user?.full_name || 'Enterprise User'}</h2>
              <p className="text-xs text-slate-500 font-mono">{user?.email || 'admin@enterprise.ai'}</p>
              <div className="mt-1 flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full bg-blue-50 text-primary border border-blue-200 text-[10px] font-bold uppercase">
                  {user?.role || 'ADMIN'}
                </span>
                <span className="text-[11px] text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Active Session
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Full Name
              </label>
              <input
                type="text"
                disabled
                value={user?.full_name || 'Administrator'}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 font-medium"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <input
                type="email"
                disabled
                value={user?.email || 'admin@enterprise.ai'}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 font-medium"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Assigned RBAC Role
              </label>
              <input
                type="text"
                disabled
                value={user?.role || 'ADMIN'}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 font-medium font-mono"
              />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="bg-white rounded-2xl border border-border p-6 shadow-sm max-w-2xl space-y-6">
          <div>
            <h2 className="text-sm font-bold text-slate-900">API Key & Service Credentials</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Use this secret key to authenticate programmatic REST inference requests.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700">Production REST API Key</span>
              <button
                onClick={handleCopyKey}
                className="flex items-center gap-1 text-xs text-primary font-semibold hover:underline"
              >
                {copiedKey ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedKey ? 'Copied' : 'Copy Key'}
              </button>
            </div>
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 font-mono text-xs text-slate-800 break-all select-all">
              {mockApiKey}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-2.5">
            <Lock className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <span className="font-bold">Security Best Practice:</span> Keep your API credentials confidential.
              Never commit secret keys into public version control repositories.
            </div>
          </div>
        </div>
      )}

      {activeTab === 'cluster' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
          <div className="bg-white p-5 rounded-xl border border-border space-y-2 shadow-2xs">
            <div className="flex items-center gap-2 text-slate-900 font-bold text-xs">
              <HardDrive className="w-4 h-4 text-primary" /> Database Storage
            </div>
            <p className="text-[11px] text-slate-500">PostgreSQL 16 Engine with SQLAlchemy 2 Connection Pool</p>
            <div className="text-xs font-mono text-slate-800 font-bold">Driver: asyncpg / psycopg2</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-border space-y-2 shadow-2xs">
            <div className="flex items-center gap-2 text-slate-900 font-bold text-xs">
              <Activity className="w-4 h-4 text-primary" /> Task Broker & Worker
            </div>
            <p className="text-[11px] text-slate-500">Celery Distributed Worker Queue with Redis Broker</p>
            <div className="text-xs font-mono text-slate-800 font-bold">Concurrency: 4 Parallel Workers</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-border space-y-2 shadow-2xs">
            <div className="flex items-center gap-2 text-slate-900 font-bold text-xs">
              <Shield className="w-4 h-4 text-primary" /> MLflow Tracking Server
            </div>
            <p className="text-[11px] text-slate-500">MLflow 2.x Experiment Tracking & Model Artifact Store</p>
            <div className="text-xs font-mono text-slate-800 font-bold">Storage: Local Artifact Volume</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-border space-y-2 shadow-2xs">
            <div className="flex items-center gap-2 text-slate-900 font-bold text-xs">
              <Clock className="w-4 h-4 text-primary" /> Security & Auth
            </div>
            <p className="text-[11px] text-slate-500">Argon2 Password Hashing & HS256 JWT Token Auth</p>
            <div className="text-xs font-mono text-slate-800 font-bold">Token Expiration: 120 Minutes</div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="bg-white rounded-2xl border border-border p-6 shadow-sm space-y-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Governance & Audit Trail</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Immutable event log tracking model promotions, dataset mutations, and batch predictions.
            </p>
          </div>

          <div className="divide-y divide-slate-100">
            {auditEvents.map((evt) => (
              <div key={evt.id} className="py-3 flex items-start justify-between">
                <div>
                  <div className="text-xs font-mono font-bold text-slate-900">{evt.action}</div>
                  <div className="text-xs text-slate-600 mt-0.5">{evt.details}</div>
                  <div className="text-[10px] text-slate-400 mt-1 font-mono">By: {evt.user}</div>
                </div>
                <span className="text-[10px] font-mono text-slate-400">
                  {new Date(evt.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
