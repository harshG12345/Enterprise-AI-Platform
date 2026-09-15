import React from 'react';
import { Activity, User as UserIcon, ShieldCheck, LogOut } from 'lucide-react';
import { useAuth } from '../../store/authStore';
import { NotificationDropdown } from '../notifications/NotificationDropdown';

interface HeaderProps {
  systemStatus?: 'healthy' | 'warning' | 'error';
}

export const Header: React.FC<HeaderProps> = ({ systemStatus = 'healthy' }) => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-border px-6 flex items-center justify-between sticky top-0 z-20 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs font-medium text-slate-700">
          <Activity
            className={`w-3.5 h-3.5 ${
              systemStatus === 'healthy'
                ? 'text-status-success animate-pulse'
                : 'text-status-warning'
            }`}
          />
          <span className="capitalize">{systemStatus} System Cluster</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <NotificationDropdown />

        <div className="h-5 w-px bg-border" />

        <div className="flex items-center gap-3 pl-2">
          <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-semibold text-xs">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-semibold text-slate-900 flex items-center gap-1">
              {user?.full_name || 'Enterprise User'}
              <ShieldCheck className="w-3.5 h-3.5 text-primary" />
            </span>
            <span className="text-[10px] text-slate-500 font-mono">{user?.email || 'user@enterprise-ai.io'}</span>
          </div>

          <button
            type="button"
            onClick={logout}
            title="Log Out"
            className="ml-2 p-1.5 text-slate-400 hover:text-status-error hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
