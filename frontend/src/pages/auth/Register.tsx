import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, User as UserIcon, ArrowRight, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { registerUser } from '../../api/auth';
import { AuthLayout } from '../../layouts/AuthLayout';
import { RegisterFormData, registerSchema } from '../../schemas/auth';
import { UserRole } from '../../types/auth';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      fullName: '',
      email: '',
      role: 'DATA_SCIENTIST' as UserRole,
      password: '',
      confirmPassword: '',
    },
  });

  const passwordValue = watch('password', '');

  const hasLength = passwordValue.length >= 8;
  const hasUpper = /[A-Z]/.test(passwordValue);
  const hasLower = /[a-z]/.test(passwordValue);
  const hasNumber = /\d/.test(passwordValue);

  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null);
    try {
      await registerUser({
        full_name: data.fullName,
        email: data.email,
        role: data.role,
        password: data.password,
      });
      navigate('/login', {
        state: { message: 'Registration successful. Please sign in with your credentials.' },
      });
    } catch (err: unknown) {
      const error = err as { message?: string };
      setServerError(error.message || 'Registration failed. Please try again.');
    }
  };

  return (
    <AuthLayout
      title="Create Enterprise Account"
      subtitle="Join the collaborative MLOps & model governance ecosystem"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {serverError && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-status-error text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{serverError}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <UserIcon className="w-4 h-4" />
            </div>
            <input
              type="text"
              {...register('fullName')}
              placeholder="Jane Doe"
              className="block w-full pl-9 pr-3 py-2 border border-border rounded-lg text-xs bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          {errors.fullName && (
            <p className="mt-1 text-[11px] text-status-error">{errors.fullName.message}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              {...register('email')}
              placeholder="jane.doe@enterprise-ai.io"
              className="block w-full pl-9 pr-3 py-2 border border-border rounded-lg text-xs bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          {errors.email && (
            <p className="mt-1 text-[11px] text-status-error">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Workspace Role</label>
          <select
            {...register('role')}
            className="block w-full px-3 py-2 border border-border rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="DATA_SCIENTIST">Data Scientist (EDA, Training, Experiments, Registry)</option>
            <option value="USER">User / Analyst (Read, Inference & Predictions)</option>
            <option value="ADMIN">Admin (Full System & User Governance)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type="password"
              {...register('password')}
              placeholder="••••••••"
              className="block w-full pl-9 pr-3 py-2 border border-border rounded-lg text-xs bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          {errors.password && (
            <p className="mt-1 text-[11px] text-status-error">{errors.password.message}</p>
          )}

          {/* Password Strength Indicator */}
          <div className="mt-2 grid grid-cols-2 gap-1.5 text-[11px] text-slate-500">
            <div className={`flex items-center gap-1 ${hasLength ? 'text-status-success font-medium' : ''}`}>
              <CheckCircle2 className="w-3 h-3" /> 8+ Characters
            </div>
            <div className={`flex items-center gap-1 ${hasUpper ? 'text-status-success font-medium' : ''}`}>
              <CheckCircle2 className="w-3 h-3" /> Uppercase (A-Z)
            </div>
            <div className={`flex items-center gap-1 ${hasLower ? 'text-status-success font-medium' : ''}`}>
              <CheckCircle2 className="w-3 h-3" /> Lowercase (a-z)
            </div>
            <div className={`flex items-center gap-1 ${hasNumber ? 'text-status-success font-medium' : ''}`}>
              <CheckCircle2 className="w-3 h-3" /> Digit (0-9)
            </div>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Confirm Password</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type="password"
              {...register('confirmPassword')}
              placeholder="••••••••"
              className="block w-full pl-9 pr-3 py-2 border border-border rounded-lg text-xs bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          {errors.confirmPassword && (
            <p className="mt-1 text-[11px] text-status-error">{errors.confirmPassword.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full mt-2 py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Creating Account...
            </>
          ) : (
            <>
              Complete Registration
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>

        <div className="text-center pt-2 border-t border-slate-100">
          <span className="text-xs text-slate-500">
            Already registered?{' '}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              Sign In
            </Link>
          </span>
        </div>
      </form>
    </AuthLayout>
  );
};
