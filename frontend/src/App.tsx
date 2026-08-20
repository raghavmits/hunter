import { BrowserRouter, Route, Routes } from "react-router";
import { Layout } from "./components/Layout";
import { CompanyPage } from "./pages/CompanyPage";
import { CorpusPage } from "./pages/CorpusPage";
import { DigestPage } from "./pages/DigestPage";
import { FunnelPage } from "./pages/FunnelPage";
import { ThreadDetailPage } from "./pages/ThreadDetailPage";
import { ThreadsPage } from "./pages/ThreadsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DigestPage />} />
          <Route path="threads" element={<ThreadsPage />} />
          <Route path="threads/:id" element={<ThreadDetailPage />} />
          <Route path="companies/:id" element={<CompanyPage />} />
          <Route path="funnel" element={<FunnelPage />} />
          <Route path="corpus" element={<CorpusPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
