import { useContext } from "react";

import { AuthContext } from "../auth/AuthProvider";

/**
 * Access the logged-in user, their manageable guild list, and
 * login/logout actions. Must be used inside <AuthProvider>.
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === null) {
    throw new Error("useAuth must be used within an <AuthProvider>.");
  }

  return context;
}
