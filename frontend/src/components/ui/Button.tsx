import React, { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "secondary", size = "md", children, disabled, ...props }, ref) => {
    const baseClasses =
      "inline-flex items-center justify-center font-serif text-sm transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-parchment-primary disabled:opacity-40 disabled:cursor-not-allowed select-none";

    const variantClasses = {
      primary:
        "bg-parchment-primary text-parchment-on-primary hover:bg-parchment-primary-container dark:bg-darkpaper-primary dark:text-darkpaper-on-primary border border-parchment-primary dark:border-darkpaper-primary",
      secondary:
        "bg-parchment-container text-parchment-on-surface hover:bg-parchment-container-high border border-parchment-outline-variant dark:bg-darkpaper-container dark:text-darkpaper-on-surface dark:border-darkpaper-outline-variant",
      outline:
        "bg-transparent text-parchment-on-surface hover:bg-parchment-container-low border border-parchment-outline dark:text-darkpaper-on-surface dark:border-darkpaper-outline",
      ghost:
        "bg-transparent text-parchment-on-surface hover:bg-parchment-container-low dark:text-darkpaper-on-surface dark:hover:bg-darkpaper-container",
      danger:
        "bg-transparent text-parchment-error hover:bg-parchment-error-container border border-parchment-error",
    };

    const sizeClasses = {
      sm: "h-8 px-2.5 text-xs tracking-wider uppercase",
      md: "h-9.5 px-4 text-sm",
      lg: "h-11 px-6 text-base",
      icon: "h-9 w-9 p-0",
    };

    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(baseClasses, variantClasses[variant], sizeClasses[size], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

