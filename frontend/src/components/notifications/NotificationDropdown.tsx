import React, { useEffect, useRef, useState } from 'react';
import {
  Bell,
  CheckCheck,
  Trash2,
  Sparkles,
  Loader2,
  Inbox,
  X,
  Layers,
  Activity,
  Cpu,
  Database,
} from 'lucide-react';
import { NotificationFilterTab, useNotifications } from '../../store/notificationStore';
import { NotificationItem } from './NotificationItem';

export const NotificationDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const {
    notifications,
    unreadCount,
    isLoading,
    filter,
    setFilter,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
    seedDemo,
  } = useNotifications();

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const filterTabs: { id: NotificationFilterTab; label: string; icon?: React.ReactNode }[] = [
    { id: 'ALL', label: 'All' },
    { id: 'UNREAD', label: `Unread (${unreadCount})` },
    { id: 'TRAINING', label: 'Training', icon: <Cpu className="w-3 h-3" /> },
    { id: 'DRIFT', label: 'Drift', icon: <Activity className="w-3 h-3" /> },
    { id: 'DATASET', label: 'Datasets', icon: <Database className="w-3 h-3" /> },
    { id: 'SYSTEM', label: 'System', icon: <Layers className="w-3 h-3" /> },
  ];

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Open notifications"
        aria-expanded={isOpen}
        className={`p-2 rounded-lg transition-all relative ${
          isOpen
            ? 'bg-slate-100 text-slate-900 ring-2 ring-primary/20'
            : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
        }`}
      >
        <Bell className="w-4 h-4" />

        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-rose-500 text-white font-bold text-[10px] rounded-full flex items-center justify-center shadow-sm animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Floating Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-[420px] max-w-[calc(100vw-24px)] bg-white rounded-2xl shadow-2xl border border-slate-200/90 z-50 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="p-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900">Notifications</h3>
              {unreadCount > 0 ? (
                <span className="px-2 py-0.5 text-[11px] font-semibold bg-rose-100 text-rose-700 rounded-full">
                  {unreadCount} new
                </span>
              ) : (
                <span className="px-2 py-0.5 text-[11px] font-medium bg-slate-200/70 text-slate-600 rounded-full">
                  All caught up
                </span>
              )}
            </div>

            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={markAllAsRead}
                  title="Mark all as read"
                  className="p-1.5 text-xs font-medium text-slate-600 hover:text-primary hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all flex items-center gap-1"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  <span className="text-[11px]">Read all</span>
                </button>
              )}

              <button
                type="button"
                onClick={seedDemo}
                title="Seed sample notifications for live demo"
                className="p-1.5 text-xs font-medium text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg border border-transparent hover:border-purple-200 transition-all flex items-center gap-1"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span className="text-[11px]">Demo</span>
              </button>

              {notifications.length > 0 && (
                <button
                  type="button"
                  onClick={clearAll}
                  title="Clear all notifications"
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 rounded-lg transition-all ml-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Filter Tab Strip */}
          <div className="px-3 py-2 border-b border-slate-100 bg-white flex items-center gap-1 overflow-x-auto scrollbar-none">
            {filterTabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setFilter(tab.id)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  filter === tab.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Notification List Container */}
          <div className="max-h-[420px] min-h-[160px] overflow-y-auto p-3 space-y-2 bg-slate-50/40">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin mb-2 text-primary" />
                <span className="text-xs">Fetching notifications...</span>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center px-4">
                <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-3 shadow-inner">
                  <Inbox className="w-6 h-6" />
                </div>
                <h4 className="text-xs font-semibold text-slate-800 mb-1">No notifications found</h4>
                <p className="text-[11px] text-slate-500 max-w-[240px] mb-3">
                  {filter !== 'ALL'
                    ? `No notifications matching the "${filter}" filter.`
                    : 'You are all caught up! New alerts and training events will appear here.'}
                </p>
                <button
                  type="button"
                  onClick={seedDemo}
                  className="px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary font-medium text-xs transition-colors flex items-center gap-1.5 border border-primary/20"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Seed Demo Alerts
                </button>
              </div>
            ) : (
              notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkRead={markAsRead}
                  onDelete={deleteNotification}
                  onCloseDropdown={() => setIsOpen(false)}
                />
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Live Alert Listener Active
            </span>
            <span className="font-mono text-[10px] text-slate-400">
              {notifications.length} {notifications.length === 1 ? 'alert' : 'alerts'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
