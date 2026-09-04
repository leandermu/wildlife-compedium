import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export interface LocationPickerProps {
  latitude: number | null;
  longitude: number | null;
  onChange: (latitude: number | null, longitude: number | null) => void;
}

function ClickSelector({ onPick }: { onPick: (latitude: number, longitude: number) => void }) {
  useMapEvents({
    click(event) {
      onPick(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

function Recenter({ latitude, longitude }: { latitude: number; longitude: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([latitude, longitude], Math.max(map.getZoom(), 12));
  }, [latitude, longitude, map]);
  return null;
}

export function LocationPicker({ latitude, longitude, onChange }: LocationPickerProps) {
  const selected = latitude !== null && longitude !== null;
  const [open, setOpen] = useState(selected);
  const center: [number, number] = selected ? [latitude, longitude] : [51.1, 10.4];

  return (
    <div className="rounded-sm border border-rule bg-paper-2/40 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[13px] font-medium text-ink-2">Standort auf der Karte setzen</p>
          <p className="text-[11px] text-ink-3">
            {selected
              ? `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`
              : "Optional – Karte öffnen und den Fundort anklicken."}
          </p>
        </div>
        <div className="flex gap-2">
          {selected && (
            <button
              type="button"
              onClick={() => onChange(null, null)}
              className="text-[12px] text-ink-3 underline decoration-rule-2 underline-offset-2 hover:text-rust"
            >
              Entfernen
            </button>
          )}
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="rounded-sm border border-rule-2 bg-paper px-3 py-1.5 text-[12px] text-ink-2 hover:bg-paper-2"
            aria-expanded={open}
          >
            {open ? "Karte schließen" : "Karte öffnen"}
          </button>
        </div>
      </div>

      {open && (
        <div className="wc-map mt-3 overflow-hidden rounded-sm border border-rule-2">
          <MapContainer center={center} zoom={selected ? 12 : 5} className="h-64 w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClickSelector
              onPick={(nextLatitude, nextLongitude) => onChange(
                Number(nextLatitude.toFixed(6)),
                Number(nextLongitude.toFixed(6)),
              )}
            />
            {selected && (
              <>
                <Recenter latitude={latitude} longitude={longitude} />
                <CircleMarker
                  center={[latitude, longitude]}
                  radius={8}
                  pathOptions={{
                    color: "#f8f4ea",
                    weight: 3,
                    fillColor: "#a87a2c",
                    fillOpacity: 0.95,
                  }}
                />
              </>
            )}
          </MapContainer>
          <p className="border-t border-rule bg-paper px-3 py-2 text-[11px] text-ink-3">
            Klicke auf den gewünschten Punkt. Die Koordinaten werden automatisch übernommen.
          </p>
        </div>
      )}
    </div>
  );
}
