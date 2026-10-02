{
  "$schema": "/etc/xdg/swaync/configSchema.json",
  "positionX": "right",
  "positionY": "top",
  "layer": "overlay",
  "control-center-layer": "top",
  "layer-shell": true,
  "cssPriority": "user",
  "control-center-margin-top": 8,
  "control-center-margin-bottom": 8,
  "control-center-margin-right": 8,
  "control-center-margin-left": 0,
  "control-center-width": 420,
  "notification-window-width": 400,
  "notification-icon-size": 48,
  "notification-body-image-height": 100,
  "notification-body-image-width": 200,
  "timeout": 6,
  "timeout-low": 4,
  "timeout-critical": 0,
  "fit-to-screen": true,
  "keyboard-shortcuts": true,
  "image-visibility": "when-available",
  "transition-time": 180,
  "hide-on-clear": false,
  "hide-on-action": true,
  "script-fail-notify": false,
  "scripts": {
    "ping": {
      "exec": "sh -c '@HOME@/.local/bin/tp-sound notify'",
      "urgency": "Normal"
    },
    "ping-low": {
      "exec": "sh -c '@HOME@/.local/bin/tp-sound notify'",
      "urgency": "Low"
    },
    "ping-critical": {
      "exec": "sh -c '@HOME@/.local/bin/tp-sound bell'",
      "urgency": "Critical"
    }
  },
  "widgets": ["title", "dnd", "mpris", "volume", "notifications"],
  "widget-config": {
    "title": { "text": "Notifications", "clear-all-button": true, "button-text": "Clear" },
    "dnd": { "text": "Do not disturb" },
    "mpris": { "show-album-art": "when-available", "autohide": true },
    "volume": { "label": "Vol" }
  }
}
