import { useEffect } from "react";

export default function Toast({ message, variant = "info", onDismiss, duration = 4000 }) {
  useEffect(() => {
    if (!onDismiss) return;
    const timer = setTimeout(onDismiss, duration);
    return () => clearTimeout(timer);
  }, [onDismiss, duration]);

  if (!message) return null;

  return (
    <div className={`toast toast-${variant}`} role="status">
      {message}
    </div>
  );
}
