/**
 * Clean Cookie Onboarding Component
 * Handles cookie consent and ensures users never logout unexpectedly
 */

'use client';

import { useState, useEffect } from 'react';
import { Cookie, Shield, Clock, Check } from 'lucide-react';
import { LocalStorage, UserPreferences } from '@/lib/localStorage';

interface CookieOnboardingProps {
  onAccept?: () => void;
  onDecline?: () => void;
  className?: string;
}

export function CookieOnboarding({ onAccept, onDecline, className = '' }: CookieOnboardingProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [selectedPreferences, setSelectedPreferences] = useState({
    essential: true, // Always true, cannot be disabled
    analytics: false,
    marketing: false,
    preferences: true, // For user preferences like theme
  });

  useEffect(() => {
    const cookieConsent = LocalStorage.get<string>('cookie_consent');
    queueMicrotask(() => setIsVisible(!cookieConsent));
  }, []);

  const handleAcceptAll = () => {
    const preferences = {
      essential: true,
      analytics: true,
      marketing: true,
      preferences: true,
    };
    
    saveCookiePreferences(preferences);
    setIsVisible(false);
    onAccept?.();
  };

  const handleAcceptSelected = () => {
    saveCookiePreferences(selectedPreferences);
    setIsVisible(false);
    onAccept?.();
  };

  const handleDeclineAll = () => {
    const preferences = {
      essential: true, // Essential cookies cannot be declined
      analytics: false,
      marketing: false,
      preferences: false,
    };
    
    saveCookiePreferences(preferences);
    setIsVisible(false);
    onDecline?.();
  };

  const saveCookiePreferences = (preferences: typeof selectedPreferences) => {
    LocalStorage.set('cookie_consent', 'given');
    LocalStorage.set('cookie_preferences', preferences);
    
    // Set user as onboarded
    UserPreferences.setOnboardingCompleted(true);
  };

  if (!isVisible) return null;

  return (
    <div className={`fixed bottom-0 left-0 right-0 z-50 ${className}`}>
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <Cookie className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Cookie Preferences
                </h3>
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                We use cookies to ensure you get the best experience, keep you logged in securely, 
                and remember your preferences. Your authentication will persist safely.
              </p>

              {/* Cookie Categories */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <CookieCategory
                  icon={Shield}
                  title="Essential"
                  description="Required for authentication and security"
                  checked={selectedPreferences.essential}
                  disabled={true}
                  onChange={() => {}} // Essential cookies cannot be disabled
                />
                
                <CookieCategory
                  icon={Check}
                  title="Preferences"
                  description="Remember your settings and theme"
                  checked={selectedPreferences.preferences}
                  onChange={(checked) => 
                    setSelectedPreferences(prev => ({ ...prev, preferences: checked }))
                  }
                />
                
                <CookieCategory
                  icon={Clock}
                  title="Analytics"
                  description="Help us improve the platform"
                  checked={selectedPreferences.analytics}
                  onChange={(checked) => 
                    setSelectedPreferences(prev => ({ ...prev, analytics: checked }))
                  }
                />
                
                <CookieCategory
                  icon={Cookie}
                  title="Marketing"
                  description="Personalized content and ads"
                  checked={selectedPreferences.marketing}
                  onChange={(checked) => 
                    setSelectedPreferences(prev => ({ ...prev, marketing: checked }))
                  }
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2 min-w-fit">
              <button
                onClick={handleAcceptAll}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Accept All
              </button>
              
              <button
                onClick={handleAcceptSelected}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white text-sm font-medium rounded-lg transition-colors"
              >
                Accept Selected
              </button>
              
              <button
                onClick={handleDeclineAll}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 text-sm font-medium transition-colors"
              >
                Decline Optional
              </button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              By continuing, you agree to our use of essential cookies for authentication. 
              Your login session will be maintained securely across browser sessions.
              <a href="/privacy" className="text-blue-600 dark:text-blue-400 hover:underline ml-1">
                Learn more about our privacy policy
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface CookieCategoryProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}

function CookieCategory({ 
  icon: Icon, 
  title, 
  description, 
  checked, 
  disabled = false,
  onChange 
}: CookieCategoryProps) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
      <Icon className="h-5 w-5 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
            {title}
          </h4>
          
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={checked}
              disabled={disabled}
              onChange={(e) => onChange(e.target.checked)}
              className="sr-only peer"
            />
            <div className={`
              w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer 
              dark:bg-gray-600 peer-checked:after:translate-x-full 
              peer-checked:after:border-white after:content-[''] after:absolute 
              after:top-[2px] after:left-[2px] after:bg-white after:rounded-full 
              after:h-4 after:w-4 after:transition-all
              ${checked ? 'peer-checked:bg-blue-600' : ''}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'peer-checked:bg-blue-600'}
            `} />
          </label>
        </div>
        
        <p className="text-xs text-gray-600 dark:text-gray-300">
          {description}
        </p>
        
        {disabled && (
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            Required
          </p>
        )}
      </div>
    </div>
  );
}

// Hook to check cookie preferences
export function useCookiePreferences() {
  const preferences = LocalStorage.get<{
    essential: boolean;
    analytics: boolean;
    marketing: boolean;
    preferences: boolean;
  }>('cookie_preferences');

  return {
    preferences,
    hasGivenConsent: LocalStorage.has('cookie_consent'),
    isOnboarded: UserPreferences.getOnboardingCompleted(),
  };
}

export default CookieOnboarding;
