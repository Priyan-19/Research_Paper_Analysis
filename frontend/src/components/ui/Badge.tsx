import React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "vector" | "graph" | "hybrid" | "success" | "error";
}

export function Badge({
  className,
  variant = "default",
  children,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-parchment-container text-parchment-on-surface border-parchment-outline-variant",
    secondary: "bg-parchment-secondary-container text-parchment-on-secondary-container border-parchment-outline-variant",
    outline: "bg-transparent text-parchment-on-surface-variant border-parchment-outline-variant",
    vector: "bg-[#e2e8f0] text-[#1e293b] border-[#cbd5e1] dark:bg-[#1e293b] dark:text-[#94a3b8] dark:border-[#334155]",
    graph: "bg-[#fef3c7] text-[#92400e] border-[#fde68a] dark:bg-[#451a03] dark:text-[#fde68a] dark:border-[#78350f]",
    hybrid: "bg-[#dcfce7] text-[#166534] border-[#bbf7d0] dark:bg-[#052e16] dark:text-[#bbf7d0] dark:border-[#14532d]",
    success: "bg-[#e6f4ea] text-[#137333] border-[#ceead6]",
    error: "bg-parchment-error-container text-parchment-on-error-container border-parchment-error",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-[11px] font-serif font-medium tracking-label uppercase border",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

