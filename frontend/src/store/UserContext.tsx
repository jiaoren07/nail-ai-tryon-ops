import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Gender = "female" | "male";

export interface HandFeatures {
  skin_tone?: string;
  hand_shape?: string;
}

export interface UserState {
  userId: string;
  userGender: Gender | null;
  handFeatures: HandFeatures | null;
  compareSelection: string[];
  photoId: string | null;
}

export interface UserContextValue extends UserState {
  setUserGender: (g: Gender) => void;
  setHandFeatures: (h: HandFeatures | null) => void;
  setCompareSelection: (ids: string[]) => void;
  setPhotoId: (id: string | null) => void;
  resetEverything: () => void;
}

const UserContext = createContext<UserContextValue | null>(null);

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
  const [handFeatures, setHandFeatures] = useState<HandFeatures | null>(null);
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

export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be called inside <UserProvider>");
  return ctx;
}
