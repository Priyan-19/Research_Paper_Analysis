import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught render error:", error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex items-center justify-center p-6 bg-parchment-surface dark:bg-darkpaper-surface text-parchment-on-surface dark:text-darkpaper-on-surface">
          <div className="max-w-md w-full p-6 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container shadow-md text-center">
            <AlertTriangle className="w-10 h-10 text-amber-600 dark:text-amber-400 mx-auto mb-3" />
            <h3 className="font-serif text-base font-semibold mb-1">
              {this.props.fallbackTitle || "Render Interface Notice"}
            </h3>
            <p className="text-xs font-serif text-parchment-on-surface-variant mb-4">
              A display formatting issue occurred while rendering content. The application is still active.
            </p>
            {this.state.error && (
              <pre className="text-[11px] font-mono p-2 bg-parchment-container/60 dark:bg-darkpaper-container-high text-left overflow-x-auto mb-4 border border-parchment-outline-variant">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-serif bg-parchment-primary text-parchment-on-primary hover:bg-parchment-primary/90 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry Render</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

