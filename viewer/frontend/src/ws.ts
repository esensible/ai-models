import { useCallback, useEffect, useRef, useState } from "react";
import type { Entry, ServerMsg } from "./types";

const WS_URL = import.meta.env.VITE_WS_URL;
const TOKEN = import.meta.env.VITE_API_TOKEN;

/** Directory-service client: keeps the current folder listing live over the WebSocket. */
export function useDirectory() {
  const [path, setPath] = useState("/");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const pathRef = useRef(path);
  pathRef.current = path;
  const presigns = useRef(new Map<string, (url: string) => void>());

  const send = useCallback((obj: unknown) => {
    const s = ws.current;
    if (s && s.readyState === WebSocket.OPEN) s.send(JSON.stringify(obj));
  }, []);

  const list = useCallback((p: string) => send({ action: "list", path: p }), [send]);

  useEffect(() => {
    let closed = false;
    let retry: number | undefined;
    const connect = () => {
      const url = TOKEN ? `${WS_URL}?token=${encodeURIComponent(TOKEN)}` : WS_URL;
      const s = new WebSocket(url);
      ws.current = s;
      s.onopen = () => { setConnected(true); setError(null); list(pathRef.current); };
      s.onclose = () => { setConnected(false); if (!closed) retry = window.setTimeout(connect, 1500); };
      s.onerror = () => setError("connection error");
      s.onmessage = (ev) => {
        const msg = JSON.parse(ev.data) as ServerMsg;
        if (msg.type === "list") {
          if (msg.path === pathRef.current) setEntries(msg.entries);
        } else if (msg.type === "changed") {
          if (msg.path === pathRef.current) list(pathRef.current);
        } else if (msg.type === "presign") {
          presigns.current.get(msg.path)?.(msg.url);
          presigns.current.delete(msg.path);
        } else if (msg.type === "error") {
          setError(msg.message);
        }
      };
    };
    connect();
    return () => { closed = true; if (retry) window.clearTimeout(retry); ws.current?.close(); };
  }, [list]);

  const navigate = useCallback((p: string) => { setPath(p); list(p); }, [list]);
  const rename = useCallback((from: string, to: string) => send({ action: "rename", from, to }), [send]);
  const remove = useCallback((p: string) => send({ action: "delete", path: p }), [send]);
  const presign = useCallback(
    (p: string) => new Promise<string>((resolve) => {
      presigns.current.set(p, resolve);
      send({ action: "presign", path: p });
    }),
    [send],
  );

  return { path, entries, connected, error, navigate, rename, remove, presign };
}
