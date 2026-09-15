import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  Check,
  Trash2,
  ExternalLink,
  Cpu,
  Database,
  Activity,
  Box,
  Shield,
  Layers,
} from 'lucide-react';
import { Notification, NotificationCategory, NotificationType } from '../../types/notification';

interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
  onCloseDropdown?: () => void;
}

const formatRelativeTime = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return 'Recently';
  }
};

const getTypeIcon = (type: NotificationType) => {
  switch (type) {
    case 'SUCCESS':
      return <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />;
    case 'WARNING':
      return <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />;
    case 'ERROR':
      return <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />;
    case 'INFO':
    default:
      return <Info className="w-4 h-4 text-blue-500 flex-shrink-0" />;
  }
};

const getCategoryIcon = (category: NotificationCategory) => {
  switch (category) {
    case 'TRAINING':
      return <Cpu className="w-3 h-3 text-purple-500" />;
    case 'DATASET':
      return <Database className="w-3 h-3 text-cyan-500" />;
    case 'DRIFT':
      return <Activity className="w-3 h-3 text-amber-500" />;
    case 'MODEL':
      return <Box className="w-3 h-3 text-indigo-500" />;
    case 'SECURITY':
      return <Shield className="w-3 h-3 text-rose-500" />;
    case 'SYSTEM':
    default:
      return <Layers className="w-3 h-3 text-slate-500" />;
  }
};

const getCategoryBadgeClass = (category: NotificationCategory): string => {
  switch (category) {
    case 'TRAINING':
      return 'bg-purple-50 text-purple-700 border-purple-200';
    case 'DATASET':
      return 'bg-cyan-50 text-cyan-700 border-cyan-200';
    case 'DRIFT':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'MODEL':
      return 'bg-indigo-50 text-indigo-700 border-indigo-200';
    case 'SECURITY':
      return 'bg-rose-50 text-rose-700 border-rose-200';
    case 'SYSTEM':
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200';
  }
};

export const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkRead,
  onDelete,
  onCloseDropdown,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (!notification.is_read) {
      onMarkRead(notification.id);
    }
    if (notification.link) {
      navigate(notification.link);
      if (onCloseDropdown) {
        onCloseDropdown();
      }
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`group relative p-3.5 rounded-xl border transition-all duration-200 cursor-pointer ${
        notification.is_read
          ? 'bg-white border-slate-100 hover:bg-slate-50/80 hover:border-slate-200'
          : 'bg-blue-50/40 border-blue-100/80 hover:bg-blue-50/70 hover:border-blue-200 shadow-sm'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Type Icon */}
        <div className="mt-0.5">{getTypeIcon(notification.type)}</div>

        {/* Content */}
        <div className="flex-1 min-w-0 pr-6">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span
              className={`text-xs font-semibold leading-tight ${
                notification.is_read ? 'text-slate-800' : 'text-slate-900'
              }`}
            >
              {notification.title}
            </span>

            {/* Category Chip */}
            <span
              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${getCategoryBadgeClass(
                notification.category
              )}`}
            >
              {getCategoryIcon(notification.category)}
              {notification.category}
            </span>

            {/* Unread indicator */}
            {!notification.is_read && (
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 inline-block animate-pulse" />
            )}
          </div>

          <p className="text-xs text-slate-600 leading-relaxed line-clamp-2 mb-2">
            {notification.message}
          </p>

          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>{formatRelativeTime(notification.created_at)}</span>

            {notification.link && (
              <span className="inline-flex items-center gap-1 text-primary hover:underline font-medium">
                View details
                <ExternalLink className="w-3 h-3" />
              </span>
            )}
          </div>
        </div>

        {/* Quick Actions (Floating Right) */}
        <div
          className="absolute top-2.5 right-2.5 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => e.stopPropagation()}
        >
          {!notification.is_read && (
            <button
              type="button"
              onClick={() => onMarkRead(notification.id)}
              title="Mark as read"
              className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-100/60 transition-colors"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => onDelete(notification.id)}
            title="Delete notification"
            className="p-1 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-100/60 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
