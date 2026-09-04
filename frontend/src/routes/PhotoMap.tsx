import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "../api";
import type { MapPhoto } from "../types";
import { Empty, Spinner } from "../components/ui";
import { formatDate } from "../lib/format";

interface PhotoPlace {
  key: string;
  latitude: number;
  longitude: number;
  photos: MapPhoto[];
}

function FitPhotoBounds({ places }: { places: PhotoPlace[] }) {
  const map = useMap();

  useEffect(() => {
    if (places.length === 0) return;
    if (places.length === 1) {
      map.setView([places[0].latitude, places[0].longitude], 11);
      return;
    }
    const bounds: LatLngBoundsExpression = places.map((place) => [
      place.latitude,
      place.longitude,
    ]);
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
  }, [map, places]);

  return null;
}

export function PhotoMapPage() {
  const [photos, setPhotos] = useState<MapPhoto[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.mapPhotos()
      .then(setPhotos)
      .catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  const places = useMemo<PhotoPlace[]>(() => {
    if (!photos) return [];
    const grouped = new Map<string, PhotoPlace>();
    for (const photo of photos) {
      if (photo.latitude === null || photo.longitude === null) continue;
      const key = `${photo.latitude.toFixed(5)}:${photo.longitude.toFixed(5)}`;
      const place = grouped.get(key) ?? {
        key,
        latitude: photo.latitude,
        longitude: photo.longitude,
        photos: [],
      };
      place.photos.push(photo);
      grouped.set(key, place);
    }
    return [...grouped.values()];
  }, [photos]);

  const withoutCoordinates = useMemo(
    () => (photos ?? []).filter(
      (photo) => photo.latitude === null || photo.longitude === null,
    ),
    [photos],
  );

  if (error) {
    return <Empty title="Karte konnte nicht geladen werden" hint={error} />;
  }
  if (!photos) return <Spinner label="Fundorte werden eingezeichnet …" />;

  return (
    <div className="animate-fade-up space-y-8">
      <header className="border-b border-rule pb-6">
        <p className="label-caps">Fotografische Fundorte</p>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-serif text-4xl text-ink">Karte</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-3">
              Alle Fotos der aktuellen Sammlung mit gespeichertem Standort. Mehrere
              Aufnahmen am selben Ort sind in einem Kartenpunkt zusammengefasst.
            </p>
          </div>
          <dl className="flex gap-6 text-right">
            <div>
              <dd className="font-serif text-2xl text-ink">{places.length}</dd>
              <dt className="label-caps">Fundorte</dt>
            </div>
            <div>
              <dd className="font-serif text-2xl text-ink">{photos.length}</dd>
              <dt className="label-caps">Fotos</dt>
            </div>
          </dl>
        </div>
      </header>

      {places.length > 0 ? (
        <section className="wc-map overflow-hidden rounded-sm border border-rule-2 bg-paper-2 shadow-[var(--shadow-card)]">
          <MapContainer
            center={[51.1, 10.4]}
            zoom={6}
            scrollWheelZoom
            className="h-[62vh] min-h-[30rem] w-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <FitPhotoBounds places={places} />
            {places.map((place) => (
              <CircleMarker
                key={place.key}
                center={[place.latitude, place.longitude]}
                radius={Math.min(16, 7 + Math.sqrt(place.photos.length) * 2)}
                pathOptions={{
                  color: "#f8f4ea",
                  weight: 3,
                  fillColor: "#4a6340",
                  fillOpacity: 0.92,
                }}
              >
                <Popup maxWidth={340} minWidth={260}>
                  <div className="max-h-96 overflow-y-auto pr-1">
                    <p className="mb-2 font-serif text-lg text-ink">
                      {place.photos[0].location_name || "Gespeicherter Fundort"}
                    </p>
                    <div className="space-y-2">
                      {place.photos.map((photo) => (
                        <MapPhotoCard key={photo.id} photo={photo} />
                      ))}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </section>
      ) : (
        <Empty
          title="Noch keine GPS-Fundorte"
          hint="Fotos mit GPS-Daten oder Begegnungen mit Koordinaten erscheinen hier automatisch."
        />
      )}

      {withoutCoordinates.length > 0 && (
        <section>
          <div className="mb-4 flex items-baseline justify-between gap-4 border-b border-rule pb-3">
            <div>
              <h2 className="font-serif text-2xl text-ink">Orte ohne Kartenkoordinaten</h2>
              <p className="mt-1 text-[13px] text-ink-3">
                Diese Fotos haben einen Ortsnamen, aber keine GPS-Daten.
              </p>
            </div>
            <span className="label-caps">{withoutCoordinates.length} Fotos</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {withoutCoordinates.map((photo) => (
              <MapPhotoCard key={photo.id} photo={photo} standalone />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function MapPhotoCard({
  photo,
  standalone = false,
}: {
  photo: MapPhoto;
  standalone?: boolean;
}) {
  const mapUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    photo.latitude !== null && photo.longitude !== null
      ? `${photo.latitude},${photo.longitude}`
      : photo.location_name,
  )}`;

  return (
    <article className={standalone ? "overflow-hidden rounded-sm border border-rule bg-paper shadow-[var(--shadow-card)]" : "overflow-hidden rounded-sm border border-rule bg-paper-2"}>
      {photo.thumb_url || photo.url ? (
        <Link to={`/arten/${photo.species_slug}`} className="block aspect-[4/3] overflow-hidden bg-paper-3">
          <img
            src={photo.thumb_url ?? photo.url ?? ""}
            alt={photo.species_name}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-300 hover:scale-[1.03]"
          />
        </Link>
      ) : null}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <Link to={`/arten/${photo.species_slug}`} className="font-serif text-lg text-ink hover:text-moss-2">
              {photo.species_name}
            </Link>
            <p className="truncate text-[12px] text-ink-3">
              {formatDate(photo.date) || "ohne Datum"}
              {photo.location_name && ` · ${photo.location_name}`}
            </p>
          </div>
          <span className="shrink-0 text-lg" title={photo.profile_name}>
            {photo.profile_avatar}
          </span>
        </div>
        <a
          href={mapUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-[12px] text-moss-2 underline decoration-rule-2 underline-offset-2"
        >
          In Google Maps öffnen ↗
        </a>
      </div>
    </article>
  );
}
