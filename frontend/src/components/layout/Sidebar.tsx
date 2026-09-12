import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderKanban,
  Database,
  Cpu,
  FlaskConical,
  Boxes,
  Zap,
  ActivitySquare,
  Settings as SettingsIcon,
  Layers,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Training Wizard', href: '/training', icon: Cpu },
  { name: 'Experiments', href: '/experiments', icon: FlaskConical },
  { name: 'Model Registry', href: '/models', icon: Boxes },
  { name: 'Inference', href: '/predictions', icon: Zap },
  { name: 'Drift & Monitoring', href: '/monitoring', icon: ActivitySquare },
  { name: 'Settings', href: '/settings', icon: SettingsIcon },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col shrink-0 h-screen sticky top-0 select-none">
      {/* Brand Identity */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800">
        <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white shadow-md shadow-primary/20">
          <Layers className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-sm tracking-tight text-white">Enterprise AI</span>
          <span className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">
            Data Science & MLOps
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
          Core Platform
        </div>
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                }`}
              />
              <span className="flex-1">{item.name}</span>
              {item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-primary/30 text-blue-200">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Footer */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 flex flex-col gap-1">
        <div className="flex items-center justify-between font-mono text-[11px] text-slate-400">
          <span>Engine v0.1.0</span>
          <span className="text-status-success font-semibold">ONLINE</span>
        </div>
        <div className="text-[10px] text-slate-500">FastAPI • Celery • MLflow</div>
      </div>
    </aside>
  );
};
