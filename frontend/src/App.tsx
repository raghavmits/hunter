import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { CompaniesView } from "./CompaniesView";
import { ContactsView } from "./ContactsView";
import type { Company, Contact } from "./types";
import "./index.css";

type View = "contacts" | "companies";

export default function App() {
  const [view, setView] = useState<View>("contacts");
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [highlightCompanyId, setHighlightCompanyId] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    const [c, co] = await Promise.all([api.contacts.list(), api.companies.list()]);
    setContacts(c);
    setCompanies(co);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const switchToCompany = (id: string) => {
    setView("companies");
    setHighlightCompanyId(id);
  };

  return (
    <>
      <header>
        <h1>Hunter</h1>
        <nav>
          <button
            className={`nav-btn${view === "contacts" ? " active" : ""}`}
            onClick={() => setView("contacts")}
          >
            Contacts
          </button>
          <button
            className={`nav-btn${view === "companies" ? " active" : ""}`}
            onClick={() => setView("companies")}
          >
            Companies
          </button>
        </nav>
      </header>

      <main>
        {view === "contacts" ? (
          <ContactsView
            contacts={contacts}
            companies={companies}
            onReload={loadAll}
            onNavigateToCompany={switchToCompany}
          />
        ) : (
          <CompaniesView
            companies={companies}
            onReload={loadAll}
            highlightId={highlightCompanyId}
            onHighlightDone={() => setHighlightCompanyId(null)}
          />
        )}
      </main>

      <footer>
        Stored in Postgres on your machine — nothing leaves your machine.
      </footer>
    </>
  );
}
