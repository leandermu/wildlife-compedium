import { lazy, Suspense } from "react";
import type { LocationPickerProps } from "./LocationPicker";

const LocationPicker = lazy(() => import("./LocationPicker").then((module) => ({
  default: module.LocationPicker,
})));

export function LazyLocationPicker(props: LocationPickerProps) {
  return (
    <Suspense fallback={(
      <div className="rounded-sm border border-rule bg-paper-2/40 p-3 text-[12px] text-ink-3">
        Karte wird geladen …
      </div>
    )}>
      <LocationPicker {...props} />
    </Suspense>
  );
}
