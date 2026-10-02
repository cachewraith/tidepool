#!/usr/bin/env bash
# Tidepool installer for Arch Linux. Safe to run again.
#
#   ./install.sh                 interactive
#   ./install.sh --theme frost   start with a different theme
#   ./install.sh --no-packages   only link configs
#   ./install.sh --yes           install base packages without asking
#
# Nothing is deleted. Existing files are moved to ~/.config-backup-tidepool-<time>.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
BIN="$HOME/.local/bin"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME/.config-backup-tidepool-$STAMP"
THEME=""
DO_PACKAGES=1
ASSUME_YES=0

BASE_PKGS=(
  hyprland hypridle hyprlock hyprpolkitagent xdg-desktop-portal-hyprland
  waybar rofi kitty swaync swaybg
  wl-clipboard cliphist grim slurp jq libnotify brightnessctl playerctl
  pipewire pipewire-pulse wireplumber pavucontrol
  ttf-jetbrains-mono-nerd starship eza bat fzf zoxide fastfetch btop cava
  thunar gvfs bash-completion
)
GAME_PKGS=(prismlauncher jdk21-openjdk gamemode mangohud)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --theme)       THEME="${2:-}"; shift 2 ;;
    --no-packages) DO_PACKAGES=0; shift ;;
    --yes|-y)      ASSUME_YES=1; shift ;;
    -h|--help)     sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)             echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
ask()  { [[ "$ASSUME_YES" == 1 ]] && return 0; local a; read -rp "$1 [y/N] " a; [[ "$a" =~ ^[Yy]$ ]]; }

# --- Packages ---------------------------------------------------------------
if [[ "$DO_PACKAGES" == 1 ]]; then
  if command -v pacman >/dev/null 2>&1; then
    say "Packages"
    echo "Base: ${BASE_PKGS[*]}"
    if ask "Install base packages with pacman?"; then
      sudo pacman -S --needed "${BASE_PKGS[@]}"
    fi
    echo
    echo "Gaming and Minecraft: ${GAME_PKGS[*]}"
    if [[ "$ASSUME_YES" == 0 ]] && ask "Install gaming and Minecraft packages too?"; then
      sudo pacman -S --needed "${GAME_PKGS[@]}"
    fi
  else
    echo "pacman not found, skipping packages."
  fi
fi

# --- Hyprland version -------------------------------------------------------
say "Checking Hyprland"
if command -v Hyprland >/dev/null 2>&1; then
  ver="$(Hyprland --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  echo "Found Hyprland ${ver:-unknown}"
  if [[ -n "$ver" && "$(printf '%s\n0.55.0\n' "$ver" | sort -V | head -1)" != "0.55.0" ]]; then
    echo "This config uses Hyprland's Lua format, which needs 0.55 or newer."
    echo "Update first: sudo pacman -Syu"
    ask "Continue anyway?" || exit 1
  fi
else
  echo "Hyprland is not installed yet. Linking configs anyway."
fi

# --- Linking ----------------------------------------------------------------
link() {
  local src="$1" dst="$2" rel
  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" && "$(readlink -f "$dst")" == "$(readlink -f "$src")" ]]; then return 0; fi
  if [[ -e "$dst" || -L "$dst" ]]; then
    rel="${dst#"$HOME"/}"
    mkdir -p "$BACKUP/$(dirname "$rel")"
    mv "$dst" "$BACKUP/$rel"
    echo "  backed up $dst"
  fi
  ln -s "$src" "$dst"
  echo "  linked $dst"
}

say "Linking configs"
link "$REPO/config/hypr/hyprland.lua"    "$CFG/hypr/hyprland.lua"
link "$REPO/config/hypr/hypridle.conf"   "$CFG/hypr/hypridle.conf"
link "$REPO/config/waybar/config.jsonc"  "$CFG/waybar/config.jsonc"
link "$REPO/config/rofi/config.rasi"     "$CFG/rofi/config.rasi"
link "$REPO/config/kitty/kitty.conf"     "$CFG/kitty/kitty.conf"
link "$REPO/config/fastfetch/config.jsonc" "$CFG/fastfetch/config.jsonc"
link "$REPO/config/shell/bashrc.sh"      "$CFG/tidepool/bashrc.sh"

say "Linking commands into $BIN"
mkdir -p "$BIN"
for f in "$REPO"/bin/*; do
  chmod +x "$f"
  link "$f" "$BIN/$(basename "$f")"
done

# Hyprland prefers hyprland.lua when both exist, so an old hyprland.conf is just unused clutter
if [[ -f "$CFG/hypr/hyprland.conf" ]]; then
  echo
  echo "Found $CFG/hypr/hyprland.conf. Hyprland now loads hyprland.lua, so it is no longer used."
  if ask "Move it to the backup folder?"; then
    mkdir -p "$BACKUP/.config/hypr"
    mv "$CFG/hypr/hyprland.conf" "$BACKUP/.config/hypr/hyprland.conf"
    echo "  backed up hyprland.conf"
  fi
fi

# --- Bash hook --------------------------------------------------------------
say "Shell"
if ! grep -q '# >>> tidepool >>>' "$HOME/.bashrc" 2>/dev/null; then
  if [[ -f "$HOME/.bashrc" ]]; then
    mkdir -p "$BACKUP"
    cp "$HOME/.bashrc" "$BACKUP/.bashrc"
  fi
  cat >> "$HOME/.bashrc" <<'EOF'

# >>> tidepool >>>
[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/tidepool/bashrc.sh" ] && . "${XDG_CONFIG_HOME:-$HOME/.config}/tidepool/bashrc.sh"
# <<< tidepool <<<
EOF
  echo "  added the Tidepool block to ~/.bashrc"
else
  echo "  ~/.bashrc already has the Tidepool block"
fi

# --- Theme ------------------------------------------------------------------
say "Rendering theme"
if [[ -z "$THEME" ]]; then
  if [[ -s "$CFG/tidepool/theme" ]]; then THEME="$(cat "$CFG/tidepool/theme")"; else THEME="tidepool"; fi
fi
TP_NO_RELOAD=1 "$REPO/bin/tp-theme" set "$THEME"
mkdir -p "$HOME/Pictures/Screenshots"

# --- Check the Lua config ---------------------------------------------------
if command -v Hyprland >/dev/null 2>&1; then
  say "Verifying config"
  Hyprland --verify-config 2>&1 | tail -25 || true
fi

say "Done"
cat <<EOF
Next:
  1. Log out and start Hyprland (pick it in your login screen, or run: start-hyprland).
  2. Switch themes any time:  tp-theme next   or   SUPER+T
  3. Open a new terminal to see the new prompt.

Themes: $(ls "$REPO/themes" | tr '\n' ' ')
Backups, if any, are in: $BACKUP
Keybinds and tips: $REPO/README.md
EOF
