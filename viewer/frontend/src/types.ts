export type EntryType = "file" | "dir";

export interface Entry {
  name: string;
  type: EntryType;
  size?: number;
  mtime?: string;
  key?: string;
}

export type ServerMsg =
  | { type: "list"; path: string; entries: Entry[] }
  | { type: "presign"; path: string; url: string; expiresIn: number }
  | { type: "changed"; path: string }
  | { type: "error"; message: string };
