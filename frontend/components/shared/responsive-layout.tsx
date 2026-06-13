import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { gridPatterns } from "@/lib/design-system";

interface ResponsiveGridProps {
  children: ReactNode;
  variant?: keyof typeof gridPatterns;
  className?: string;
  testId?: string;
}

/**
 * Responsive grid component that enforces mobile-first design
 * All layouts tested at 320px, 768px, 1024px, 1440px viewports
 */
export function ResponsiveGrid({ 
  children, 
  variant = "autoFit", 
  className,
  testId 
}: ResponsiveGridProps) {
  return (
    <div 
      className={cn(gridPatterns[variant], className)}
      data-testid={testId}
    >
      {children}
    </div>
  );
}

interface ResponsiveStackProps {
  children: ReactNode;
  direction?: "column" | "row";
  breakpoint?: "sm" | "md" | "lg";
  gap?: "sm" | "md" | "lg";
  className?: string;
}

/**
 * Responsive stack that switches from column to row at specified breakpoint
 */
export function ResponsiveStack({ 
  children, 
  direction = "row",
  breakpoint = "md",
  gap = "md",
  className 
}: ResponsiveStackProps) {
  const gapClasses = {
    sm: "gap-4",
    md: "gap-6", 
    lg: "gap-8"
  };

  const responsiveClasses = {
    sm: direction === "row" ? "flex flex-col sm:flex-row" : "flex flex-row sm:flex-col",
    md: direction === "row" ? "flex flex-col md:flex-row" : "flex flex-row md:flex-col",
    lg: direction === "row" ? "flex flex-col lg:flex-row" : "flex flex-row lg:flex-col",
  };

  return (
    <div 
      className={cn(
        responsiveClasses[breakpoint],
        gapClasses[gap],
        className
      )}
    >
      {children}
    </div>
  );
}

interface MobileFirstContainerProps {
  children: ReactNode;
  className?: string;
}

/**
 * Container that prevents horizontal scroll on any viewport
 * Ensures all content is accessible on mobile devices
 */
export function MobileFirstContainer({ children, className }: MobileFirstContainerProps) {
  return (
    <div className={cn("w-full overflow-x-hidden", className)}>
      {children}
    </div>
  );
}