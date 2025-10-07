#!/usr/bin/env python3
"""自動構建 Dashboard 前端的腳本。

此腳本會：
1. 檢查 Node.js 和 npm 是否已安裝
2. 安裝前端依賴（如果需要）
3. 構建前端資源
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """運行命令並返回結果。"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"命令未找到: {cmd[0]}"


def check_node_installed() -> bool:
    """檢查 Node.js 是否已安裝。"""
    returncode, stdout, _ = run_command(["node", "--version"])
    if returncode == 0:
        print(f"✓ Node.js 版本: {stdout.strip()}")
        return True
    return False


def check_npm_installed() -> bool:
    """檢查 npm 是否已安裝。"""
    returncode, stdout, _ = run_command(["npm", "--version"])
    if returncode == 0:
        print(f"✓ npm 版本: {stdout.strip()}")
        return True
    return False


def build_dashboard():
    """構建 Dashboard 前端。"""
    print("\n" + "=" * 60)
    print("🚀 開始構建 Dashboard 前端")
    print("=" * 60 + "\n")

    # 獲取項目根目錄和 frontend 目錄
    root_dir = Path(__file__).parent.parent
    frontend_dir = root_dir / "src" / "frontend"

    if not frontend_dir.exists():
        print(f"❌ 錯誤: Frontend 目錄不存在 ({frontend_dir})")
        sys.exit(1)

    # 檢查 Node.js 和 npm
    print("📦 檢查依賴...")
    if not check_node_installed():
        print("\n❌ 錯誤: 未安裝 Node.js")
        print("請訪問 https://nodejs.org/ 下載安裝 Node.js")
        sys.exit(1)

    if not check_npm_installed():
        print("\n❌ 錯誤: 未安裝 npm")
        print("npm 通常隨 Node.js 一起安裝")
        sys.exit(1)

    # 檢查是否需要安裝依賴
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("\n📥 安裝前端依賴...")
        returncode, stdout, stderr = run_command(["npm", "install"], cwd=frontend_dir)
        if returncode != 0:
            print(f"\n❌ 安裝依賴失敗:\n{stderr}")
            sys.exit(1)
        print("✓ 依賴安裝完成")

    # 構建前端
    print("\n🔨 構建前端資源...")
    returncode, stdout, stderr = run_command(["npm", "run", "build"], cwd=frontend_dir)

    if returncode != 0:
        print(f"\n❌ 構建失敗:\n{stderr}")
        sys.exit(1)

    # 檢查構建產物
    dist_dir = root_dir / "dist"
    if not dist_dir.exists():
        print("\n❌ 錯誤: 構建產物目錄不存在")
        sys.exit(1)

    print("\n✅ Dashboard 前端構建成功！")
    print(f"   構建產物位於: {dist_dir}")

    # 顯示構建產物大小
    total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
    print(f"   總大小: {total_size / 1024:.2f} KB")

    print("\n" + "=" * 60)
    print("🎉 構建完成！現在可以啟動 Dashboard 了")
    print("=" * 60)


if __name__ == "__main__":
    try:
        build_dashboard()
    except KeyboardInterrupt:
        print("\n\n⚠️  構建已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 構建過程中發生錯誤: {e}")
        sys.exit(1)
