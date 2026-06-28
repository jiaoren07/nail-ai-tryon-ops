// Minimal type shim for react-compare-image (no upstream @types package).
// Props subset is what U5 actually uses; extend if other call sites need more.
declare module "react-compare-image" {
  import { ComponentType } from "react";

  interface Props {
    leftImage: string;
    rightImage: string;
    leftImageAlt?: string;
    rightImageAlt?: string;
    sliderLineColor?: string;
    sliderLineWidth?: number;
    handleSize?: number;
    handle?: React.ReactElement;
    skeleton?: React.ReactElement;
    aspectRatio?: "taller" | "wider";
    vertical?: boolean;
  }

  const ReactCompareImage: ComponentType<Props>;
  export default ReactCompareImage;
}
