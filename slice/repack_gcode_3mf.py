#!/usr/bin/env python
"""Replace the G-code inside a Bambu .gcode.3mf and fix its md5 sidecar.

A .gcode.3mf is a zip; the printer validates Metadata/plate_1.gcode against
Metadata/plate_1.gcode.md5 (lowercase hex md5 of the gcode bytes). Swap the
gcode without updating the md5 and the P1S rejects the file. This copies every
other entry verbatim and rewrites those two.

  ./cad/run.sh slice/repack_gcode_3mf.py SOURCE.gcode.3mf NEW.gcode OUT.gcode.3mf
"""
import hashlib
import sys
import zipfile

GCODE = "Metadata/plate_1.gcode"
MD5 = "Metadata/plate_1.gcode.md5"


def main():
    src, new_gcode, out = sys.argv[1], sys.argv[2], sys.argv[3]
    data = open(new_gcode, "rb").read()
    digest = hashlib.md5(data).hexdigest()

    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    if GCODE not in names or MD5 not in names:
        sys.exit(f"source missing {GCODE} or {MD5}")

    # sanity: confirm the source's own md5 matches its gcode (validates the scheme)
    want = zin.read(MD5).decode().strip()
    got = hashlib.md5(zin.read(GCODE)).hexdigest()
    if want.lower() != got.lower():
        sys.exit(f"md5 scheme mismatch on source: sidecar={want} computed={got}")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            if n == GCODE:
                zout.writestr(n, data)
            elif n == MD5:
                zout.writestr(n, digest)
            else:
                zout.writestr(zin.getinfo(n), zin.read(n))
    print(f"wrote {out}")
    print(f"  gcode: {len(data):,} bytes  md5={digest}")
    print(f"  (source md5 scheme verified: whole-file lowercase hex)")


if __name__ == "__main__":
    main()
