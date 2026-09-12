import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { useAuth } from '../store/authStore';
import { UserRole } from '../types/auth';

interface RoleRouteProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
}

export const RoleRoute: React.FC<RoleRouteProps> = ({ children, allowedRoles }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!user || !allowedRoles.includes(user.role)) {
    return (
      <div className="p-8 max-w-xl mx-auto mt-12 bg-white border border-red-200 rounded-xl shadow-sm text-center">
        <div className="w-12 h-12 bg-red-50 text-status-error rounded-full flex items-center justify-center mx-auto mb-3">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-base font-bold text-slate-900">Access Restricted</h2>
        <p className="text-xs text-slate-500 mt-1">
          Your current enterprise role ({user?.role || 'Guest'}) does not have permission to access
          this area.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
