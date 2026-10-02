#!/usr/bin/env bash
# Tidepool uninstaller. Removes the links and generated files, puts backups back.
# Does not remove packages.
set -euo pipefail

CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
BIN="$HOME/.local/bin"
STATE="$CFG/tidepool"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Removing links that point into $REPO"
for dir in "$CFG" "$BIN"; do
  while IFS= read -r l; do
    if [[ "$(readlink -f "$l")" == "$REPO"/* ]]; then rm -f "$l"; echo "  removed $l"; fi
  done < <(find "$dir" -maxdepth 3 -type l 2>/dev/null)
done

if [[ -f "$STATE/managed" ]]; then
  echo "Removing generated files"
  while IFS= read -r f; do
    [[ -n "$f" && -e "$f" ]] && rm -f "$f" && echo "  removed $f"
  done < "$STATE/managed"
fi

if [[ -d "$STATE/backup" ]]; then
  echo "Restoring files Tidepool had replaced"
  for b in "$STATE/backup"/*; do
    [[ -e "$b" || -L "$b" ]] || continue
    rel="$(basename "$b")"; rel="${rel//__//}"
    if [[ ! -e "$CFG/$rel" ]]; then
      mkdir -p "$(dirname "$CFG/$rel")"
      cp -P "$b" "$CFG/$rel"
      echo "  restored $CFG/$rel"
    fi
  done
fi

if grep -q '# >>> tidepool >>>' "$HOME/.bashrc" 2>/dev/null; then
  sed -i '/# >>> tidepool >>>/,/# <<< tidepool <<</d' "$HOME/.bashrc"
  echo "Removed the Tidepool block from ~/.bashrc"
fi

# Files install.sh moved aside. Oldest backup first, so your originals win.
shopt -s nullglob
for bdir in "$HOME"/.config-backup-tidepool-*; do
  [[ -d "$bdir" ]] || continue
  while IFS= read -r -d '' f; do
    rel="${f#"$bdir"/}"
    if [[ ! -e "$HOME/$rel" && ! -L "$HOME/$rel" ]]; then
      mkdir -p "$(dirname "$HOME/$rel")"
      cp -P "$f" "$HOME/$rel"
      echo "  restored ~/$rel"
    fi
  done < <(find "$bdir" \( -type f -o -type l \) -print0)
done

rm -rf "$STATE/current"
echo "Done. Backup folders are kept: ~/.config-backup-tidepool-*"
