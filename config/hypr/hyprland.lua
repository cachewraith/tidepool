-- ~/.config/hypr/hyprland.lua  (Tidepool)
-- Needs Hyprland 0.55 or newer. Check: hyprctl version
--
-- Colors and style come from theme.lua, which `tp-theme set <id>` writes.
-- Put personal overrides in ~/.config/hypr/user.lua, for example:
--   return { terminal = "alacritty", browser = "zen-browser", files = "nautilus" }
--
-- Every section runs inside try(), so one Lua error does not stop the rest of
-- the config from loading. Failures show up as a Hyprland notification.

local home   = os.getenv("HOME")
local xdg    = os.getenv("XDG_CONFIG_HOME") or (home .. "/.config")
local cfg    = xdg .. "/hypr/"

local function exists(path)
  local f = io.open(path, "r")
  if f then f:close() return true end
  return false
end

local function try(name, fn)
  local ok, err = pcall(fn)
  if not ok then
    local msg = "tidepool: " .. name .. " failed: " .. tostring(err)
    print(msg)
    pcall(hl.notification.create, { text = msg, timeout = 10000, icon = "error" })
  end
end

----------------------------------------------------------------------
-- Theme, game mode, user overrides
----------------------------------------------------------------------
local t = dofile(cfg .. "theme.lua")
local game = exists(xdg .. "/tidepool/gamemode")

local user = {
  terminal = "kitty",
  browser  = "firefox",
  files    = "thunar",
  launcher = "rofi -show drun",
}
if exists(cfg .. "user.lua") then
  for k, v in pairs(dofile(cfg .. "user.lua")) do user[k] = v end
end

local mod = "SUPER"

----------------------------------------------------------------------
-- Environment and display
----------------------------------------------------------------------
try("env", function()
  hl.env("PATH", home .. "/.local/bin:" .. (os.getenv("PATH") or "/usr/local/bin:/usr/bin"))
  hl.env("XCURSOR_SIZE", "24")
  hl.env("HYPRCURSOR_SIZE", "24")
  hl.env("QT_QPA_PLATFORM", "wayland;xcb")
  hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
end)

-- Catch-all monitor. To pin a screen, copy this line with its name from `hyprctl monitors`,
-- e.g. output = "DP-1", mode = "2560x1440@144", position = "0x0", scale = 1.0
try("monitor", function()
  hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1.0 })
end)

----------------------------------------------------------------------
-- Look and feel
----------------------------------------------------------------------
try("config", function()
  hl.config({
    general = {
      gaps_in = game and 0 or t.gaps_in,
      gaps_out = game and 0 or t.gaps_out,
      border_size = t.border,
      resize_on_border = true,
      layout = "dwindle",
      allow_tearing = game,
      col = {
        active_border = t.active_border,
        inactive_border = t.inactive_border,
      },
    },

    decoration = {
      rounding = game and 0 or t.rounding,
      active_opacity = game and 1.0 or t.opacity_active,
      inactive_opacity = game and 1.0 or t.opacity_inactive,
      shadow = {
        enabled = (not game) and t.shadow_range > 0,
        range = t.shadow_range,
        render_power = 3,
        color = t.shadow_color,
      },
      blur = {
        enabled = not game,
        size = t.blur_size,
        passes = t.blur_passes,
        vibrancy = t.blur_vibrancy,
        noise = 0.02,
        contrast = 0.95,
        brightness = 1.0,
        popups = true,
        new_optimizations = true,
        ignore_opacity = true,
      },
    },

    -- dwindle.pseudotile no longer exists; SUPER + P toggles pseudotiling per window.
    dwindle = {
      preserve_split = true,
    },

    input = {
      kb_layout = "us",
      follow_mouse = 1,
      sensitivity = 0,
      repeat_rate = 40,
      repeat_delay = 250,
      touchpad = {
        natural_scroll = true,
      },
    },

    misc = {
      disable_hyprland_logo = true,
      disable_splash_rendering = true,
      force_default_wallpaper = 0,
      mouse_move_enables_dpms = true,
      key_press_enables_dpms = true,
    },
  })
end)

----------------------------------------------------------------------
-- Motion: soft ease-out curves, slide for workspaces, pop for windows
----------------------------------------------------------------------
try("animations", function()
  hl.config({ animations = { enabled = not game } })
  if game then return end

  hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1} } })
  hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1} } })
  hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1} } })
  hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1} } })
  hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1} } })

  hl.animation({ leaf = "global",          enabled = true, speed = 10,   bezier = "default" })
  hl.animation({ leaf = "border",          enabled = true, speed = 5.4,  bezier = "easeOutQuint" })
  hl.animation({ leaf = "windows",         enabled = true, speed = 4.8,  bezier = "easeOutQuint" })
  hl.animation({ leaf = "windowsIn",       enabled = true, speed = 4.1,  bezier = "easeOutQuint", style = "popin 87%" })
  hl.animation({ leaf = "windowsOut",      enabled = true, speed = 1.5,  bezier = "linear",       style = "popin 87%" })
  hl.animation({ leaf = "fadeIn",          enabled = true, speed = 1.7,  bezier = "almostLinear" })
  hl.animation({ leaf = "fadeOut",         enabled = true, speed = 1.5,  bezier = "almostLinear" })
  hl.animation({ leaf = "fade",            enabled = true, speed = 3,    bezier = "quick" })
  hl.animation({ leaf = "layers",          enabled = true, speed = 3.8,  bezier = "easeOutQuint" })
  hl.animation({ leaf = "layersIn",        enabled = true, speed = 4,    bezier = "easeOutQuint", style = "fade" })
  hl.animation({ leaf = "layersOut",       enabled = true, speed = 1.5,  bezier = "linear",       style = "fade" })
  hl.animation({ leaf = "workspaces",      enabled = true, speed = 2.4,  bezier = "easeInOutCubic", style = "slide" })
  hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3,   bezier = "easeOutQuint", style = "slidefade" })
end)

try("gestures", function()
  hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
end)

----------------------------------------------------------------------
-- Keybinds
----------------------------------------------------------------------
try("binds: apps", function()
  hl.bind(mod .. " + Return",       hl.dsp.exec_cmd(user.terminal))
  hl.bind(mod .. " + B",            hl.dsp.exec_cmd(user.browser))
  hl.bind(mod .. " + E",            hl.dsp.exec_cmd(user.files))
  hl.bind(mod .. " + Space",        hl.dsp.exec_cmd(user.launcher))
  hl.bind(mod .. " + Tab",          hl.dsp.exec_cmd("rofi -show window"))
  hl.bind(mod .. " + M",            hl.dsp.exec_cmd("tp-menu"))
  hl.bind(mod .. " + V",            hl.dsp.exec_cmd("sh -c 'cliphist list | rofi -dmenu -p clip | cliphist decode | wl-copy'"))
  hl.bind(mod .. " + N",            hl.dsp.exec_cmd("swaync-client -t -sw"))
  hl.bind(mod .. " + Escape",       hl.dsp.exec_cmd("hyprlock"))
end)

try("binds: tidepool", function()
  hl.bind(mod .. " + T",            hl.dsp.exec_cmd("tp-theme pick"))
  hl.bind(mod .. " + SHIFT + T",    hl.dsp.exec_cmd("tp-theme next"))
  hl.bind(mod .. " + CTRL + T",     hl.dsp.exec_cmd("tp-theme random"))
  hl.bind(mod .. " + F10",          hl.dsp.exec_cmd("tp-gamemode toggle"))
  hl.bind(mod .. " + F9",           hl.dsp.exec_cmd("tp-sound toggle"))
  hl.bind("Print",                  hl.dsp.exec_cmd("tp-screenshot area"))
  hl.bind("SHIFT + Print",          hl.dsp.exec_cmd("tp-screenshot full"))
  hl.bind("ALT + Print",            hl.dsp.exec_cmd("tp-screenshot window"))
end)

try("binds: windows", function()
  hl.bind(mod .. " + Q",            hl.dsp.window.close())
  hl.bind(mod .. " + SHIFT + Q",    hl.dsp.window.kill())
  hl.bind(mod .. " + F",            hl.dsp.window.fullscreen())
  hl.bind(mod .. " + SHIFT + F",    hl.dsp.window.float())
  hl.bind(mod .. " + P",            hl.dsp.window.pseudo())
  hl.bind(mod .. " + Y",            hl.dsp.layout("togglesplit"))
  hl.bind(mod .. " + G",            hl.dsp.group.toggle())
  hl.bind(mod .. " + bracketright", hl.dsp.group.next())
  hl.bind(mod .. " + bracketleft",  hl.dsp.group.prev())
  hl.bind(mod .. " + SHIFT + E",    hl.dsp.exit())
end)

-- Focus and move with arrows or vim keys
try("binds: focus and move", function()
  local dirs = {
    { "Left",  "H", "left"  },
    { "Down",  "J", "down"  },
    { "Up",    "K", "up"    },
    { "Right", "L", "right" },
  }
  for _, d in ipairs(dirs) do
    local arrow, vim, name = d[1], d[2], d[3]
    hl.bind(mod .. " + " .. arrow,         hl.dsp.focus({ direction = name }))
    hl.bind(mod .. " + " .. vim,           hl.dsp.focus({ direction = name }))
    hl.bind(mod .. " + SHIFT + " .. arrow, hl.dsp.window.move({ direction = name }))
    hl.bind(mod .. " + SHIFT + " .. vim,   hl.dsp.window.move({ direction = name }))
  end
end)

try("binds: resize", function()
  -- relative = true grows/shrinks by the step; without it resize() sets an absolute size
  local step = 40
  local function grow(x, y) return hl.dsp.window.resize({ x = x, y = y, relative = true }) end
  hl.bind(mod .. " + CTRL + Left",  grow(-step, 0), { repeating = true })
  hl.bind(mod .. " + CTRL + Right", grow(step, 0),  { repeating = true })
  hl.bind(mod .. " + CTRL + Up",    grow(0, -step), { repeating = true })
  hl.bind(mod .. " + CTRL + Down",  grow(0, step),  { repeating = true })
  hl.bind(mod .. " + CTRL + H",     grow(-step, 0), { repeating = true })
  hl.bind(mod .. " + CTRL + L",     grow(step, 0),  { repeating = true })
  hl.bind(mod .. " + CTRL + K",     grow(0, -step), { repeating = true })
  hl.bind(mod .. " + CTRL + J",     grow(0, step),  { repeating = true })
end)

try("binds: workspaces", function()
  for i = 1, 10 do
    local key = tostring(i % 10)
    hl.bind(mod .. " + " .. key,         hl.dsp.focus({ workspace = tostring(i) }))
    hl.bind(mod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = tostring(i) }))
  end
  -- Scratchpad: a drop-in workspace for a terminal or notes
  hl.bind(mod .. " + S",         hl.dsp.workspace.toggle_special("scratch"))
  hl.bind(mod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:scratch" }))
end)

try("binds: mouse", function()
  hl.bind(mod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
  hl.bind(mod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })
end)

try("binds: media", function()
  hl.bind("XF86AudioRaiseVolume",  hl.dsp.exec_cmd("tp-volume up"),    { locked = true, repeating = true })
  hl.bind("XF86AudioLowerVolume",  hl.dsp.exec_cmd("tp-volume down"),  { locked = true, repeating = true })
  hl.bind("XF86AudioMute",         hl.dsp.exec_cmd("tp-volume mute"),  { locked = true })
  hl.bind("XF86AudioMicMute",      hl.dsp.exec_cmd("tp-volume mic"),   { locked = true })
  hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("tp-brightness up"),   { locked = true, repeating = true })
  hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("tp-brightness down"), { locked = true, repeating = true })
  hl.bind("XF86AudioPlay",         hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
  hl.bind("XF86AudioNext",         hl.dsp.exec_cmd("playerctl next"),       { locked = true })
  hl.bind("XF86AudioPrev",         hl.dsp.exec_cmd("playerctl previous"),   { locked = true })
end)

----------------------------------------------------------------------
-- Window and layer rules
----------------------------------------------------------------------
try("window rules", function()
  hl.window_rule({
    name = "float-utilities",
    match = { class = "^(pavucontrol|nm-connection-editor|blueman-manager|org.gnome.Calculator|org.pulseaudio.pavucontrol)$" },
    float = true,
    center = true,
  })
  hl.window_rule({
    name = "float-dialogs",
    match = { title = "^(Open File|Save File|Open Folder|Choose.*|Select.*)$" },
    float = true,
    center = true,
  })
  hl.window_rule({
    name = "picture-in-picture",
    match = { title = "^(Picture-in-Picture)$" },
    float = true,
    pin = true,
  })
  -- Video ignores theme opacity and keeps the screen awake
  hl.window_rule({
    name = "video",
    match = { class = "^(mpv|vlc)$" },
    opaque = true,
    idle_inhibit = "focus",
  })
  -- Games and Minecraft: opaque, low latency, no screen lock while fullscreen
  hl.window_rule({
    name = "games",
    match = { class = "^(steam_app_.*|gamescope|[Mm]inecraft.*|.*minecraft.*|org.prismlauncher.*|Prism.*)$" },
    opaque = true,
    immediate = true,
    idle_inhibit = "fullscreen",
  })
end)

try("layer rules", function()
  -- Blur behind the bar, launcher and notifications. ignore_alpha keeps the clear gaps unblurred.
  hl.layer_rule({ name = "blur-waybar", match = { namespace = "waybar" },                     blur = true, ignore_alpha = 0.1 })
  hl.layer_rule({ name = "blur-rofi",   match = { namespace = "rofi" },                       blur = true, ignore_alpha = 0.1, blur_popups = true })
  hl.layer_rule({ name = "blur-swaync", match = { namespace = "swaync-control-center" },      blur = true, ignore_alpha = 0.1 })
  hl.layer_rule({ name = "blur-notifs", match = { namespace = "swaync-notification-window" }, blur = true, ignore_alpha = 0.1 })
end)

----------------------------------------------------------------------
-- Autostart (runs once per login)
----------------------------------------------------------------------
try("autostart", function()
  hl.on("hyprland.start", function()
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("swaybg -i " .. home .. "/.config/tidepool/current/wallpaper.png -m fill")
    hl.exec_cmd("waybar")
    hl.exec_cmd("swaync")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
    hl.exec_cmd("tp-sound startup")
  end)
end)
