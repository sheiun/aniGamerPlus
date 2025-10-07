#!/usr/bin/env python3
"""Ani Gamer Next 主入口點。

這個文件提供了一個統一的入口，可以：
1. 運行下載器（等同於 ani_gamer_next.py）
2. 啟動 Dashboard Web 介面
3. 其他管理功能

使用方法：
    uv run app.py              # 運行下載器（默認）
    uv run app.py --dashboard  # 啟動 Dashboard
    uv run app.py --help       # 顯示幫助
"""

import argparse
import sys
from pathlib import Path


def main():
    """主入口函數。"""
    parser = argparse.ArgumentParser(
        description="aniGamerPlus - 巴哈姆特動畫瘋自動下載工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s                    運行自動下載器
  %(prog)s --dashboard        啟動 Web Dashboard
  %(prog)s --dashboard --port 8080  指定 Dashboard 端口
        """,
    )

    parser.add_argument(
        "--dashboard",
        "-d",
        action="store_true",
        help="啟動 Web Dashboard 介面",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Dashboard 監聽地址（默認: 0.0.0.0）",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=5000,
        help="Dashboard 監聽端口（默認: 5000）",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="開發模式（啟用 Vite HMR）",
    )

    args = parser.parse_args()

    if args.dashboard:
        # 啟動 Dashboard
        start_dashboard(args.host, args.port, args.dev)
    else:
        # 運行下載器
        run_downloader()


def start_dashboard(host: str, port: int, dev_mode: bool = False):
    """啟動 Dashboard Web 介面。"""
    import os

    print("\n" + "=" * 60)
    print("🌐 啟動 aniGamerPlus Dashboard")
    print("=" * 60)

    # 檢查構建產物
    root_dir = Path(__file__).parent.parent.parent  # 回到專案根目錄
    dist_dir = root_dir / "dist"

    if not dev_mode and not dist_dir.exists():
        print("\n⚠️  警告: Dashboard 前端未構建")
        print("請先運行: uv run build-dashboard")
        print("\n或者使用開發模式: uv run app.py --dashboard --dev")
        sys.exit(1)

    # 設置開發模式環境變量
    if dev_mode:
        os.environ["VITE_DEV_MODE"] = "true"
        print("\n🔧 開發模式已啟用")
        print("   - 確保 Vite 開發伺服器正在運行: npm run dev")
        print("")

    # 導入並運行 Dashboard
    try:
        import uvicorn

        from .dashboard_server import app

        print(f"\n✓ Dashboard 地址: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"✓ 模式: {'開發' if dev_mode else '生產'}")
        print("\n按 Ctrl+C 停止伺服器\n")
        print("=" * 60 + "\n")

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_config=None,
        )

    except ImportError as e:
        print(f"\n❌ 錯誤: 無法導入 Dashboard 模組")
        print(f"   詳細信息: {e}")
        print("\n請確保已安裝所有依賴: uv sync")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Dashboard 已停止")
        sys.exit(0)


def run_downloader():
    print("\n" + "=" * 60)
    print("📥 啟動 aniGamerPlus 自動下載器")
    print("=" * 60 + "\n")

    try:
        from . import ani_gamer_next
        ani_gamer_next.main()

    except (FileNotFoundError, ImportError) as e:
        print(f"\n❌ 錯誤: 找不到 ani_gamer_next.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  下載器已停止")
        sys.exit(0)


if __name__ == "__main__":
    main()
