import { useCallback, useMemo, useState, type ReactNode } from "react";
import { UserContext, type Gender, type UserContextValue } from "./context";

// Only the Provider component lives here so Vite fast refresh works
// (react-refresh/only-export-components). Types + context instance are in
// ./context, the consumer hook is in ./useUser. Type re-exports below keep
// existing `import type {...} from "./UserContext"` sites compiling.
export type { Gender, HandFeatures, UserContextValue, UserState } from "./context";

const SS_USER_ID = "userId";
const SS_GENDER = "userGender";

function ensureUserId(): string {
  const existing = sessionStorage.getItem(SS_USER_ID);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  sessionStorage.setItem(SS_USER_ID, fresh);
  return fresh;
}

function readGender(): Gender | null {
  const raw = sessionStorage.getItem(SS_GENDER);
  return raw === "female" || raw === "male" ? raw : null;
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [userId] = useState<string>(() => ensureUserId());
  const [userGender, setUserGenderState] = useState<Gender | null>(() => readGender());
  const [handFeatures, setHandFeatures] = useState<UserContextValue["handFeatures"]>(null);
  const [compareSelection, setCompareSelection] = useState<string[]>([]);
  const [photoId, setPhotoId] = useState<string | null>(null);

  const setUserGender = useCallback((g: Gender) => {
    sessionStorage.setItem(SS_GENDER, g);
    setUserGenderState(g);
  }, []);

  const resetEverything = useCallback(() => {
    sessionStorage.removeItem(SS_USER_ID);
    sessionStorage.removeItem(SS_GENDER);
    window.location.reload();
  }, []);

  const value = useMemo<UserContextValue>(
    () => ({
      userId,
      userGender,
      handFeatures,
      compareSelection,
      photoId,
      setUserGender,
      setHandFeatures,
      setCompareSelection,
      setPhotoId,
      resetEverything,
    }),
    [userId, userGender, handFeatures, compareSelection, photoId, setUserGender, resetEverything],
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}
