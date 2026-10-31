import { useUIStore } from "../../store/useUIStore";
import { AlertCircle, CheckCircle, Info, X } from "lucide-react";
import { cn } from "../../lib/utils";

export function ToastContainer() {
  const { toasts, dismissToast } = useUIStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => {
        const icon =
          toast.type === "success" ? (
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : toast.type === "error" ? (
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          ) : (
            <Info className="w-4 h-4 text-amber-700 flex-shrink-0" />
          );

        return (
          <div
            key={toast.id}
            className={cn(
              "pointer-events-auto flex items-center justify-between gap-3 p-3.5 bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant dark:border-darkpaper-outline shadow-md text-sm",
              toast.type === "error" && "border-rose-400 bg-rose-50/50 dark:bg-rose-950/20"
            )}
          >
            <div className="flex items-center gap-2.5">
              {icon}
              <span className="font-serif text-parchment-on-surface dark:text-darkpaper-on-surface">
                {toast.message}
              </span>
            </div>
            <button
              onClick={() => dismissToast(toast.id)}
              className="text-parchment-on-surface-variant hover:text-parchment-primary p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

