import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { focusRing, transitions } from "@/lib/design-system";

// Enhanced Card variants with consistent styling
const cardVariants = cva(
  // Base styles - consistent border-radius, shadow, and padding
  "rounded-xl border bg-card text-card-foreground shadow-sm",
  {
    variants: {
      variant: {
        default: "",
        interactive: cn(
          "cursor-pointer hover:shadow-lg hover:border-primary/20",
          transitions.all,
          focusRing.default
        ),
        elevated: "shadow-md hover:shadow-lg",
        outline: "border-2 shadow-none",
        ghost: "border-0 shadow-none bg-transparent",
      },
      size: {
        sm: "p-4",
        default: "p-6", 
        lg: "p-8",
      },
      state: {
        default: "",
        loading: "animate-pulse",
        disabled: "opacity-50 cursor-not-allowed",
        error: "border-destructive/50 bg-destructive/5",
        success: "border-green-500/50 bg-green-50/50 dark:bg-green-950/50",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      state: "default",
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, size, state, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(cardVariants({ variant, size, state, className }))}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

// Enhanced Card Header with consistent spacing
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { size?: "sm" | "default" | "lg" }
>(({ className, size = "default", ...props }, ref) => {
  const sizeStyles = {
    sm: "space-y-1 pb-2",
    default: "space-y-1.5 pb-3",
    lg: "space-y-2 pb-4"
  };

  return (
    <div
      ref={ref}
      className={cn("flex flex-col", sizeStyles[size], className)}
      {...props}
    />
  );
});
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { size?: "sm" | "default" | "lg" }
>(({ className, size = "default", ...props }, ref) => {
  const sizeStyles = {
    sm: "text-sm font-medium",
    default: "text-lg font-semibold",
    lg: "text-xl font-semibold"
  };

  return (
    <div
      ref={ref}
      className={cn(
        "leading-none tracking-tight",
        sizeStyles[size],
        className
      )}
      {...props}
    />
  );
});
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { size?: "sm" | "default" | "lg" }
>(({ className, size = "default", ...props }, ref) => {
  const sizeStyles = {
    sm: "pt-0",
    default: "pt-0", 
    lg: "pt-0"
  };

  return (
    <div 
      ref={ref} 
      className={cn(sizeStyles[size], className)} 
      {...props} 
    />
  );
});
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { 
    justify?: "start" | "center" | "end" | "between";
  }
>(({ className, justify = "start", ...props }, ref) => {
  const justifyStyles = {
    start: "justify-start",
    center: "justify-center", 
    end: "justify-end",
    between: "justify-between"
  };

  return (
    <div
      ref={ref}
      className={cn(
        "flex items-center pt-4",
        justifyStyles[justify],
        className
      )}
      {...props}
    />
  );
});
CardFooter.displayName = "CardFooter";

export { 
  Card, 
  CardHeader, 
  CardFooter, 
  CardTitle, 
  CardDescription, 
  CardContent,
  cardVariants 
};