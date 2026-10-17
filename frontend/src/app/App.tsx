
import { useState } from "react";
import Header from "../components/layout/Header";
import Parser from "../pages/Parser";
import Dashboard from "../pages/Dashboard";

type Page = "parser" | "dashboard";

export default function App() {
  const [page, setPage] = useState<Page>("parser");

  return (
    <div className="min-h-screen bg-slate-50">
      <Header currentPage={page} onNavigate={setPage} />

      <main className="mx-auto max-w-7xl px-6 py-8">
        {page === "parser" ? <Parser /> : <Dashboard />}
      </main>
    </div>
  );
}
