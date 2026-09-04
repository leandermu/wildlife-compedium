export function internalMapUrl(
  latitude: number | null | undefined,
  longitude: number | null | undefined,
  photoId?: number,
): string {
  const params = new URLSearchParams();
  if (typeof latitude === "number" && typeof longitude === "number") {
    params.set("lat", String(latitude));
    params.set("lon", String(longitude));
  }
  if (photoId !== undefined) params.set("photo", String(photoId));
  const query = params.toString();
  return query ? `/karte?${query}` : "/karte";
}
