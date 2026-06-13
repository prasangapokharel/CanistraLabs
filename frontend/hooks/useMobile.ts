'use client';

import { useState, useEffect } from 'react';

/**
 * Hook to detect if the device is mobile based on window width
 */
export function useMobile(breakpoint: number = 768) {
  const [isMobile, setIsMobile] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch - this is a necessary pattern for client-only hooks
   
  useEffect(() => {
    setMounted(true);
  }, []);

   
  useEffect(() => {
    if (!mounted) return;

    // Set initial value
    setIsMobile(window.innerWidth < breakpoint);

    // Handle resize
    const handleResize = () => {
      setIsMobile(window.innerWidth < breakpoint);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [breakpoint, mounted]);

  // Return false during SSR to prevent hydration mismatch
  return mounted ? isMobile : false;
}

/**
 * Alias for useMobile for backward compatibility
 */
export function useIsMobile(breakpoint: number = 768) {
  return useMobile(breakpoint);
}
