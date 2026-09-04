#!/usr/bin/env bash
# 把 WebApp Launcher 注册为桌面应用（用户级 .desktop + 图标）。
#
# 背景：GNOME Wayland 下 Dock/任务栏图标与名称不来自窗口自身，而是按应用 ID
# 匹配 .desktop 文件。deb 自带的 .desktop 文件名是 WebappLauncher.desktop，
# 与本应用的实际 GTK 应用 ID（com.leon.webapp-launcher）不一致，会导致
# Dock 显示成"webapp-launcher"+通用齿轮图标。此脚本注册一个与应用 ID 完全
# 匹配的用户级 .desktop（用户目录优先级最高），并隐藏 deb 自带的重复项。
#
# 图标采用绝对路径引用（应用在保存/启动时写入 ~/.local/share/webapp-launcher/
# desktop-icon.png），避免 GNOME 图标主题缓存的坑；并附带右键菜单 Actions
# "打开设置"（等价 webapp-launcher --config）。
#
# 用法: tools/install-desktop.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID="com.leon.webapp-launcher"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS_DIR="$DATA_HOME/applications"
ICON_FILE="$DATA_HOME/webapp-launcher/desktop-icon.png"

# Exec 优先指向系统安装版（/usr/bin），否则退回仓库 release 版
if command -v webapp-launcher >/dev/null 2>&1; then
  BIN="$(command -v webapp-launcher)"
elif [[ -x "$ROOT/src-tauri/target/release/webapp-launcher" ]]; then
  BIN="$ROOT/src-tauri/target/release/webapp-launcher"
else
  echo "未找到 webapp-launcher 可执行文件：请先安装 deb 或构建 release。"
  exit 1
fi

mkdir -p "$APPS_DIR" "$(dirname "$ICON_FILE")"

# 确保图标文件就位（默认图标；用户保存上传图标时应用会覆盖此文件）
cp -f "$ROOT/src-tauri/icons/icon.png" "$ICON_FILE"

cat > "$APPS_DIR/$APP_ID.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=WebApp Launcher
Name[zh_CN]=WebApp Launcher
GenericName=Web app shell
Comment=Launch any website as a desktop app
Exec=$BIN
Icon=$ICON_FILE
Terminal=false
Categories=Utility;Network;
Keywords=web;app;shell;launcher;
StartupWMClass=$APP_ID
StartupNotify=false
Actions=settings;

[Desktop Action settings]
Name=打开设置
Name[zh_CN]=打开设置
Comment=打开 WebApp Launcher 设置页
Exec=$BIN --config
EOF

# 隐藏 deb 自带的重复入口（同名 basename 的用户级文件按规范只用于覆盖）
if [[ -f "/usr/share/applications/WebappLauncher.desktop" ]]; then
  cat > "$APPS_DIR/WebappLauncher.desktop" <<'EOF'
[Desktop Entry]
Hidden=true
EOF
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi

echo "已注册桌面应用："
echo "  $APPS_DIR/$APP_ID.desktop"
echo "  Exec=$BIN  |  Icon=$ICON_FILE  |  右键 Actions: 打开设置"
echo "  (隐藏了系统自带的 WebappLauncher.desktop 重复项)"
echo
echo "在 Dock/程序菜单的图标上右键可看到【打开设置】。"
echo "图标以桌面引用文件为准：修改后重启应用生效；若仍显示旧图标，注销重登一次。"
