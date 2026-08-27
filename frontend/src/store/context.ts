import { createContext } from "react";

/** Types + the raw context instance, split from UserContext.tsx so that
 * file only exports the Provider component (react-refresh requirement)
 * and useUser.ts only exports the hook. */

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

export const UserContext = createContext<UserContextValue | null>(null);
