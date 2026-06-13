/**
 * Session Status Component - Provides visual feedback about session health
 * Ensures users are aware of their login status and prevents unexpected logouts
 */

'use client';

import { useState, useMemo } from 'react';
import { WifiOff, Shield, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { useAuth, useSessionHealth, useSessionWarnings } from '@/providers/AuthProvider';

interface SessionStatusProps {
  className?: string;
  showDetails?: boolean;
}

export function SessionStatus({ className = '', showDetails = false }: SessionStatusProps) {
  const { isAuthenticated, user } = useAuth();
  const health = useSessionHealth();
  const { shouldShowWarning } = useSessionWarnings();
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isAuthenticated) return null;

  const getStatusColor = () => {
    if (health.isHealthy) return 'text-green-600 dark:text-green-400';
    if (health.hasRefreshToken) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getStatusIcon = () => {
    if (health.isHealthy) return <CheckCircle className="h-4 w-4" />;
    if (health.hasRefreshToken) return <Clock className="h-4 w-4" />;
    return <AlertTriangle className="h-4 w-4" />;
  };

  const getStatusText = () => {
    if (health.isHealthy) return 'Session Active';
    if (health.hasRefreshToken) return 'Session Refreshing';
    return 'Session Expired';
  };

  return (
    <div className={`${className}`}>
      {/* Compact Status Indicator */}
      <div 
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className={`flex items-center gap-1 ${getStatusColor()}`}>
          {getStatusIcon()}
          <span className="text-sm font-medium">
            {getStatusText()}
          </span>
        </div>
      </div>

      {/* Expanded Details */}
      {(isExpanded || showDetails) && (
        <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="space-y-3">
            {/* User Info */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Logged in as:
              </span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {user?.email || 'Unknown'}
              </span>
            </div>

            {/* Session Health Details */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Access Token:</span>
                <div className="flex items-center gap-1">
                  {health.hasAccessToken ? (
                    <>
                      <Shield className="h-3 w-3 text-green-600" />
                      <span className="text-green-600">Valid</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-3 w-3 text-red-600" />
                      <span className="text-red-600">Missing</span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Refresh Token:</span>
                <div className="flex items-center gap-1">
                  {health.hasRefreshToken ? (
                    <>
                      <Shield className="h-3 w-3 text-green-600" />
                      <span className="text-green-600">Valid</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-3 w-3 text-red-600" />
                      <span className="text-red-600">Missing</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Last Refresh Time */}
            {health.lastRefresh && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Last Refresh:</span>
                <span className="text-gray-900 dark:text-white">
                  {new Date(health.lastRefresh).toLocaleTimeString()}
                </span>
              </div>
            )}

            {/* Session Status Message */}
            <div className="pt-2 border-t border-gray-200 dark:border-gray-600">
              <SessionMessage health={health} />
            </div>
          </div>
        </div>
      )}

      {/* Warning Banner */}
      {shouldShowWarning && (
        <SessionWarningBanner />
      )}
    </div>
  );
}

function SessionMessage({ health }: { health: ReturnType<typeof useSessionHealth> }) {
  if (health.isHealthy) {
    return (
      <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
        <CheckCircle className="h-4 w-4" />
        <span>Your session is secure and active. You&apos;ll stay logged in.</span>
      </div>
    );
  }

  if (health.hasRefreshToken) {
    return (
      <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
        <Clock className="h-4 w-4" />
        <span>Session refreshing automatically. You won&apos;t be logged out.</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
      <AlertTriangle className="h-4 w-4" />
      <span>Session expired. Please log in again to continue.</span>
    </div>
  );
}

function SessionWarningBanner() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2">
          <Clock className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Session Refresh in Progress
            </h4>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
              We&apos;re automatically refreshing your session to keep you logged in. 
              No action needed on your part.
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setIsVisible(false)}
          className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// Hook for session persistence monitoring
export function useSessionPersistence() {
  const { isAuthenticated } = useAuth();
  const health = useSessionHealth();
  const persistenceScore = useMemo(() => {
    if (!isAuthenticated) return 0;

    let score = 40;
    if (health.hasAccessToken) score += 30;
    if (health.hasRefreshToken) score += 30;
    if (health.shouldRefresh) score -= 10;
    return Math.max(0, Math.min(100, score));
  }, [health, isAuthenticated]);

  const getPersistenceLevel = () => {
    if (persistenceScore >= 80) return 'excellent';
    if (persistenceScore >= 60) return 'good';
    if (persistenceScore >= 40) return 'moderate';
    if (persistenceScore >= 20) return 'poor';
    return 'critical';
  };

  return {
    score: persistenceScore,
    level: getPersistenceLevel(),
    isHealthy: persistenceScore >= 60,
    needsAttention: persistenceScore < 40,
  };
}

export default SessionStatus;
