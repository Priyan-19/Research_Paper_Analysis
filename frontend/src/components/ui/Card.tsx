import React from "react";
import { cn } from "../../lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  plateNumber?: string | number;
}

export function Card({ className, plateNumber, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "relative bg-parchment-container-lowest dark:bg-darkpaper-container-low border border-parchment-outline-variant dark:border-darkpaper-outline-variant p-5 transition-all",
        className
      )}
      {...props}
    >
      {plateNumber !== undefined && (
        <span className="absolute top-2.5 right-3 text-[10px] font-mono tracking-label-wide text-parchment-outline select-none">
          {typeof plateNumber === "number" ? String(plateNumber).padStart(2, "0") : plateNumber}
        </span>
      )}
      {children}
    </div>
  );
}

