import { useState } from "react";
import { useDirectory } from "./ws";
import Viewer from "./Viewer";
import type { Entry } from "./types";

const filePath = (folder: string, name: string) => folder + name;
const dirPath = (folder: string, name: string) => folder + name + "/";
const parentOf = (folder: string) => {
  if (folder === "/") return "/";
  const parts = folder.replace(/\/+$/, "").split("/").filter(Boolean);
  parts.pop();
  return parts.length ? "/" + parts.join("/") + "/" : "/";
};
const fmtSize = (n?: number) =>
  n == null ? "" : n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1048576).toFixed(1)} MB`;

function Breadcrumb({ path, go }: { path: string; go: (p: string) => void }) {
  const parts = path.split("/").filter(Boolean);
  let acc = "/";
  const crumbs = [{ label: "home", path: "/" }, ...parts.map((p) => ({ label: p, path: (acc += p + "/") }))];
  return (
    <div className="flex flex-wrap items-center gap-1 text-sm text-gray-400">
      {crumbs.map((c, i) => (
        <span key={c.path} className="flex items-center gap-1">
          {i > 0 && <span className="text-gray-600">/</span>}
          <button className="hover:text-gray-100" onClick={() => go(c.path)}>{c.label}</button>
        </span>
      ))}
    </div>
  );
}

export default function App() {
  const dir = useDirectory();
  const [view, setView] = useState<{ url: string; name: string } | null>(null);

  const open = async (e: Entry) => {
    const url = await dir.presign(filePath(dir.path, e.name));
    setView({ url, name: e.name });
  };
  const rename = (e: Entry) => {
    const to = window.prompt("Rename to:", e.name);
    if (to && to !== e.name) dir.rename(filePath(dir.path, e.name), filePath(dir.path, to));
  };
  const remove = (e: Entry) => {
    if (window.confirm(`Delete ${e.name}?`)) dir.remove(filePath(dir.path, e.name));
  };

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <h1 className="text-base font-semibold">3MF Viewer</h1>
        <span
          className={`h-2.5 w-2.5 rounded-full ${dir.connected ? "bg-emerald-500" : "bg-amber-500"}`}
          title={dir.connected ? "connected" : "connecting…"}
        />
      </header>

      <div className="px-4 py-2 border-b border-gray-800">
        <Breadcrumb path={dir.path} go={dir.navigate} />
      </div>

      {dir.error && <div className="px-4 py-2 text-sm text-red-400">{dir.error}</div>}

      <ul className="flex-1 overflow-y-auto divide-y divide-gray-800">
        {dir.path !== "/" && (
          <li>
            <button className="w-full text-left px-4 py-3 hover:bg-gray-900" onClick={() => dir.navigate(parentOf(dir.path))}>
              📁 ..
            </button>
          </li>
        )}
        {dir.entries.map((e) =>
          e.type === "dir" ? (
            <li key={e.name}>
              <button className="w-full text-left px-4 py-3 hover:bg-gray-900" onClick={() => dir.navigate(dirPath(dir.path, e.name))}>
                📁 {e.name}
              </button>
            </li>
          ) : (
            <li key={e.name} className="flex items-center px-4 py-3 hover:bg-gray-900">
              <button className="flex-1 text-left min-w-0" onClick={() => open(e)}>
                <div className="truncate">🧊 {e.name}</div>
                <div className="text-xs text-gray-500">{fmtSize(e.size)}</div>
              </button>
              <div className="flex gap-3 pl-2 text-sm">
                <button className="text-gray-400 hover:text-gray-100" onClick={() => rename(e)}>Rename</button>
                <button className="text-red-400 hover:text-red-300" onClick={() => remove(e)}>Delete</button>
              </div>
            </li>
          ),
        )}
        {dir.entries.length === 0 && <li className="px-4 py-8 text-center text-gray-600">empty folder</li>}
      </ul>

      {view && (
        <div className="fixed inset-0 z-10 flex flex-col bg-black/90">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <span className="truncate">{view.name}</span>
            <button className="text-gray-300 hover:text-white text-lg" onClick={() => setView(null)}>✕</button>
          </div>
          <div className="flex-1 min-h-0">
            <Viewer url={view.url} />
          </div>
        </div>
      )}
    </div>
  );
}
