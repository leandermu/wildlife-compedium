import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";
import { Layout } from "./components/Layout";
import { Dashboard } from "./routes/Dashboard";
import { SpeciesList } from "./routes/SpeciesList";
import { SpeciesDetailPage } from "./routes/SpeciesDetail";
import { AchievementsPage } from "./routes/Achievements";
import { AdminPage } from "./routes/Admin";
import { ActivityPage } from "./routes/Activity";
import { NotFound } from "./routes/NotFound";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "arten", element: <SpeciesList /> },
      { path: "arten/:slug", element: <SpeciesDetailPage /> },
      { path: "auszeichnungen", element: <AchievementsPage /> },
      {
        path: "karte",
        lazy: async () => {
          const { PhotoMapPage } = await import("./routes/PhotoMap");
          return { Component: PhotoMapPage };
        },
      },
      { path: "aktivitaeten", element: <ActivityPage /> },
      { path: "verwaltung", element: <AdminPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
