#!/usr/bin/env bash
# Re-download the free hand-drawn fonts used for engraved/embossed text on models.
# These live in the persistent workspace, so this is only needed after a full wipe.
#
# Chalkboard (Apple) is proprietary and NOT fetched here — drop Chalkboard.ttf in
# this dir manually if you want it exact; otherwise PatrickHand is the stand-in.
set -euo pipefail
cd "$(dirname "$0")"
fetch() { curl -fsSL -o "$1" "$2" && echo "  $1"; }

echo "fetching fonts ->"
# Patrick Hand — OFL, casual handwritten (default Chalkboard substitute)
fetch PatrickHand-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf"
# Coming Soon — Apache, alt handwritten
fetch ComingSoon-Regular.ttf \
  "https://github.com/google/fonts/raw/main/apache/comingsoon/ComingSoon-Regular.ttf"
echo "done. Use in build123d via Text(..., font_path='cad/fonts/<file>.ttf')."
