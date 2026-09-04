# 维护说明

本文记录 WebApp Launcher 中容易重复踩坑的实现细节，结构沿袭 NetEase Music Shell 的维护文档。

## 总体设计

- Tauri 2.11 + WebKitGTK。
- **无配置时默认打开配置页**（本地 `index.html`）；存在配置时直接打开主窗口加载目标网址。
- 配置存储在应用配置目录（`app_config_dir()`），失败时退回 `app_data_dir()`。
- 目标网页权限与 NetEase Music Shell 相同思路：仅开放窗口控制所需的最小权限，
  见 `src-tauri/capabilities/remote.json`。

## 图标

### 来源与缓存

- 三种来源：`default`（内置图标）、`auto`（探测站点 favicon）、`upload`（本地图片）。
- 非 `default` 来源解析出的 PNG 统一缓存到 `<配置目录>/app-icon.png`，
  之后的每次启动直接读缓存，不再联网。这样离线也能得到一致的窗口图标。
- 缓存采用“临时文件 + rename”原子写入，避免半截文件。

### favicon 探测顺序（`icons.rs::resolve_auto`）

1. 抓取站点首页 HTML，正则式扫描 `<link rel="...icon...">`（apple-touch-icon 优先）；
2. 兜底尝试 `/favicon.ico`、`/favicon.png`、`/apple-touch-icon.png`；
3. 任一下载成功即解码并统一转为 <=512px 的 PNG。

图片解码通过 Tauri 的 `image` 特性（`image-png`/`image-ico`/`image-jpeg`）及直接依赖的
`image` crate 完成，因此 favicon.ico 也能读取；最终统一编码回 PNG 以简化窗口图标设置。

### 内置默认图标

- `src-tauri/icons/32x32.png`、`128x128.png`、`icon.png`(256)。
- 由 `tools/gen-icons.py` 生成（Pillow），窗口/托盘图标通过 `include_bytes!` 编译期嵌入。
  修改图标后需要重新编译；单独替换 PNG 不会改变已生成的二进制。
- 窗口图标在运行时由缓存（如果有）覆盖；清除 `app-icon.png` 即回退到内置图标。

## 窗口与沉浸模式

- 默认配置 `immersive: true`（与 NetEase Music Shell 一致的观感优先）。
- 沉浸模式 = 无边框透明窗口 + 顶部 30px 悬浮控制栏 + 16px 圆角裁剪。
  注入脚本 `window.rs::IMMERSIVE_SCRIPT` 的原理与 NetEase Music Shell 相同：
  透明渐变占住根 canvas 背景，把 `body` 变成 fixed 后代的 containing block 后统一 `overflow: hidden`。
  只注入静态 CSS，不移动、不扫描站点 DOM。
- 悬浮栏额外提供 ⚙ 按钮，通过 `window.__TAURI__.event.emit("open-settings")`
  通知 Rust 打开配置页；因此 `remote.json` 需要 `core:event:allow-emit`。
- 圆角/透明在非合成器桌面（如纯 X11 无合成器）可能显示为黑块，README 已注明系统要求。

### 远程页面的拖动 / 最小化 / 最大化依赖 ACL（易踩坑）

Tauri v2 的 `data-tauri-drag-region` 拖动、窗口按钮等**全部走远程页面 IPC**（核心注入的
`drag.js` 会调用 `plugin:window|start_dragging` 等命令），因此 `capabilities/remote.json`
必须命中远程页面的真实 URL，否则窗口既拖不动、按钮也无效，且没有任何报错提示。

URLPattern 的坑：主机模式写 `https://*` 只匹配**未显式带端口**的 URL；
本地开发站（如 `http://localhost:5173`、`https://app:8443`）会静默失配。
必须写成：

```json
"urls": ["https://*:*", "http://*:*"]
```

即主机与端口都要用 `*` 通配。实测 `https://*:*` 能匹配任意 https 主机/端口/IP/路径。
如需限制为固定站点，把 `*` 换成具体域名即可（如 `https://example.com:*`）。

## 自定义命令与 ACL

- 应用没有声明 `AppManifest` 权限（`build.rs` 不配置 `commands`），`has_app_acl` 为 false，
  因此**本地配置页调用自定义命令无需 capability**；而远程页面仍被 ACL 拒绝调用自定义命令，
  只能使用 `remote.json` 中显式授予的 core:window / core:event 权限。
- 若以后在本地页引入 core/plugin API（如对话框插件），需要新增一个 `windows: ["config"]` 的 capability。

## 需要网络的操作

- `auto` 图标探测 / 上传解码都在 `save_config` / `probe_favicon` 命令内部通过
  `tauri::async_runtime::spawn_blocking` 执行，避免阻塞 UI。
- 图标解析失败不阻止启动：回退内置图标并在结果里返回 warnings 提示。

## 发布检查

```bash
cargo check --locked --manifest-path src-tauri/Cargo.toml
npm ci
npm run build
```

发布版本必须在 `package.json`、`src-tauri/Cargo.toml` 与 `src-tauri/tauri.conf.json` 保持一致。
发布前建议在真实桌面环境验证：首次配置流程、图标三种来源、沉浸/标准两种模式、
Wayland 与 X11 下的圆角与悬浮控制栏、托盘可见性（GNOME 需要 AppIndicator 扩展）。
