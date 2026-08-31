import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="py-24 text-center">
      <p className="label-caps">Seite 404</p>
      <h1 className="mt-3 font-serif text-4xl">Diese Seite fehlt im Band</h1>
      <p className="mt-3 text-ink-3">
        Vielleicht wurde sie herausgetrennt – oder es gab sie nie.
      </p>
      <Link to="/" className="link-quiet mt-6 inline-block">
        Zurück zum Kompendium
      </Link>
    </div>
  );
}
