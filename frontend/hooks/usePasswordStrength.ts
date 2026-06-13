'use client';

import { useState, useCallback } from 'react';

interface PasswordStrength {
  score: number; // 0-4
  label: string; // 'Very Weak', 'Weak', 'Fair', 'Good', 'Strong'
  color: string; // Tailwind color
  feedback: string[];
}

/**
 * Hook for checking password strength
 */
export function usePasswordStrength() {
  const [password, setPassword] = useState('');
  const [strength, setStrength] = useState<PasswordStrength>({
    score: 0,
    label: 'Very Weak',
    color: 'bg-red-500',
    feedback: [],
  });

  const checkStrength = useCallback((pwd: string): PasswordStrength => {
    const feedback: string[] = [];
    let score = 0;

    if (!pwd) {
      return {
        score: 0,
        label: 'Very Weak',
        color: 'bg-red-500',
        feedback: [],
      };
    }

    // Length checks
    if (pwd.length >= 8) {
      score += 1;
    } else {
      feedback.push('At least 8 characters');
    }

    if (pwd.length >= 12) {
      score += 1;
    }

    // Character variety checks
    if (/[a-z]/.test(pwd)) {
      score += 0.5;
    } else {
      feedback.push('Add lowercase letters');
    }

    if (/[A-Z]/.test(pwd)) {
      score += 0.5;
    } else {
      feedback.push('Add uppercase letters');
    }

    if (/[0-9]/.test(pwd)) {
      score += 0.5;
    } else {
      feedback.push('Add numbers');
    }

    if (/[^a-zA-Z0-9]/.test(pwd)) {
      score += 0.5;
    } else {
      feedback.push('Add special characters');
    }

    // Determine label and color
    let label: string;
    let color: string;

    if (score < 1) {
      label = 'Very Weak';
      color = 'bg-red-500';
    } else if (score < 2) {
      label = 'Weak';
      color = 'bg-orange-500';
    } else if (score < 3) {
      label = 'Fair';
      color = 'bg-yellow-500';
    } else if (score < 4) {
      label = 'Good';
      color = 'bg-lime-500';
    } else {
      label = 'Strong';
      color = 'bg-green-500';
    }

    return { score: Math.min(4, Math.round(score)), label, color, feedback };
  }, []);

  const handlePasswordChange = useCallback(
    (newPassword: string) => {
      setPassword(newPassword);
      setStrength(checkStrength(newPassword));
    },
    [checkStrength]
  );

  return {
    password,
    strength,
    handlePasswordChange,
    checkStrength,
  };
}
