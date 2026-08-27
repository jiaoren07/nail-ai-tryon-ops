import { useContext } from "react";
import { UserContext, type UserContextValue } from "./context";

export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be called inside <UserProvider>");
  return ctx;
}
