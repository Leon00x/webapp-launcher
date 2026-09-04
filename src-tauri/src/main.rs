// WebApp Launcher —— 通用网页应用启动器
// 无任何设置时默认打开配置页；配置后按设置启动用户选择的网页与图标。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod desktop;
mod icons;
mod tray;
mod window;

use tauri::{AppHandle, Listener};

use config::{IconMode, LauncherConfig};
use window::SETTINGS_EVENT;

fn main() {
    // 某些 GNOME 会话（启用了 at-spi 无障碍桥）下 WebKitGTK 注册 webview 时会
    // 在 libatk-bridge 中段错误；在 GTK 初始化前关闭本应用的 ATK 桥可稳定绕过。
    // 仅在本应用内生效，不影响系统其他程序的无障碍。
    if std::env::var_os("NO_AT_BRIDGE").is_none() {
        std::env::set_var("NO_AT_BRIDGE", "1");
    }

    tauri::Builder::default()
        // 单实例：重复启动（如 .desktop 右键“打开设置”）转发到已运行实例
        .plugin(tauri_plugin_single_instance::init(|app, argv, _cwd| {
            if argv.iter().any(|a| a == "--config" || a == "-c") {
                if let Err(e) = window::open_settings_window(app) {
                    eprintln!("open settings window: {e}");
                }
            }
        }))
        .setup(|app| {
            let handle = app.handle().clone();
            let settings_handle = handle.clone();
            // 远程页面（沉浸式悬浮栏 ⚙）发出的“打开设置”请求
            let _ = handle.listen(SETTINGS_EVENT, move |_| {
                if let Err(e) = window::open_settings_window(&settings_handle) {
                    eprintln!("open settings window: {e}");
                }
            });

            // 托盘可选：由配置 show_tray 控制；失败不阻止启动
            let cfg = LauncherConfig::load(&handle);
            tray::apply(&handle, cfg.as_ref());

            boot(&handle, cfg.as_ref()).map_err(|e| format!("启动失败: {e}"))?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_setup_state,
            commands::probe_favicon,
            commands::save_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// 启动决策：
/// - 存在配置且未加 --config → 直接打开主窗口（加载目标网址）
/// - 无配置，或带 --config 参数 → 打开配置页（首次运行的默认页）
fn boot(handle: &AppHandle, cfg: Option<&LauncherConfig>) -> Result<(), String> {
    let force_config = std::env::args().skip(1).any(|a| a == "--config" || a == "-c");

    match (cfg, force_config) {
        (Some(cfg), false) => {
            window::create_main_window(handle, cfg, false)?;
        }
        (Some(cfg), true) => {
            window::create_main_window(handle, cfg, false)?;
            window::open_settings_window(handle)?;
        }
        (None, _) => {
            window::open_settings_window(handle)?;
        }
    }

    // 把“当前生效图标”同步到桌面引用文件（每次启动都执行，无需手动再保存）
    let png = cfg
        .filter(|c| c.icon != IconMode::Default)
        .and_then(|_| icons::cached_png(handle))
        .unwrap_or_else(|| icons::DEFAULT_ICON_PNG.to_vec());
    icons::sync_desktop_icon(&png);

    // 同步桌面入口（应用名称/图标/右键菜单随配置更新）
    if let Some(cfg) = cfg {
        desktop::sync(cfg);
    }

    Ok(())
}
