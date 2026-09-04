<div align="center">
  <img src="src-tauri/icons/icon.png" width="112" alt="WebApp Launcher icon">
  <h1>WebApp Launcher</h1>
  <p>把任意网页变成独立的 Linux 桌面应用</p>

  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
    <a href="docs/maintenance.md"><img src="https://img.shields.io/badge/tech-Tauri%202%20%2F%20WebKitGTK-5b8cff.svg" alt="Tech"></a>
    <a href="https://github.com/Leon00x/webapp-launcher/releases/latest"><img src="https://img.shields.io/badge/download-latest-38bdf8.svg" alt="Releases"></a>
  </p>
</div>

WebApp Launcher 是一个**通用网页应用启动器**(结构继承自
[NetEase Music Shell](https://github.com/Leon00x/netease-music-shell)):
首次运行没有任何设置时自动打开配置页,填写**网页地址**与**图标**(自动获取 favicon / 本地图片 / 内置默认)即可把它变成一个独立桌面应用。

## 特性

- 首次运行默认进入配置页,设置持久化,随时可改(托盘 / 沉浸悬浮栏 ⚙ / `--config`)
- 图标三种来源:自动探测 favicon、本地上传、内置默认;保存即同步到 Dock/任务栏
- 可选**沉浸模式**:无边框透明圆角窗口 + 顶部悬浮控制栏(沿袭 NetEase Music Shell)
- 可自定义应用名称,程序列表 / Dock 显示名随配置更新
- 独立 WebKit 数据目录,保留目标站点登录状态;Chrome UA 通过站点兼容检测
- 支持 Wayland 与 X11;提供 deb 与 AppImage

## 快速开始

```bash
# Ubuntu / Debian 依赖
sudo apt install -y libwebkit2gtk-4.1-dev libayatana-appindicator3-dev \
  build-essential curl wget file \
  libxdo-dev libssl-dev librsvg2-dev pkg-config

npm ci
npm run dev     # 首次运行打开配置页; --config 可随时打开设置
```

打包:

```bash
npm run build   # 产物: src-tauri/target/release/bundle/{deb,appimage}/
```

## 使用

- 程序列表 / Dock 图标右键 → **打开设置**
- 系统托盘(可关闭):打开设置 / 重新加载 / 退出
- 配置与图标缓存在 `~/.config/com.leon.webapp-launcher/`

## 项目结构

```text
src/                  # 配置页（纯 HTML/CSS/JS，无构建步骤）
src-tauri/
├── capabilities/     # 远程页面最小窗口控制权限
├── icons/            # 默认图标（tools/gen-icons.py 生成）
└── src/
    ├── main.rs       # 入口 / 单实例 / 启动决策
    ├── config.rs     # 配置模型与持久化
    ├── desktop.rs    # 桌面入口（名称/图标/右键菜单自动同步）
    ├── icons.rs      # favicon 探测 / 图片处理 / 缓存
    ├── tray.rs       # 可关闭的系统托盘
    ├── window.rs     # 窗口构建与注入脚本
    └── commands.rs   # 设置页 Tauri 命令
tools/                # 图标生成、桌面入口注册脚本
```

## 系统要求

- Linux x86_64 + WebKitGTK 4.1
- 沉浸模式需要支持透明窗口的合成器;GNOME Wayland 下桌面图标/名称随应用自身维护的 `.desktop` 更新

实现细节与踩坑记录见 [docs/maintenance.md](docs/maintenance.md)。

## 许可证

[MIT](LICENSE)。被启动的第三方网页及其内容权利归各自权利人所有。
