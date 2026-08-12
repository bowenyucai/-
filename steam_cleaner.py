import os
import sys
import json
import winreg
import argparse
from typing import List, Set, Optional

def get_steam_install_path() -> Optional[str]:
    """获取Steam安装路径（跨平台支持）"""
    if sys.platform == "win32":
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                path = winreg.QueryValueEx(key, "SteamPath")[0]
            return os.path.normpath(path)
        except Exception:
            pass

    # 常见平台默认路径
    platform_paths = {
        "win32": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
            os.path.expandvars(r"%ProgramFiles%\Steam")
        ],
        "linux": [
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.local/share/Steam")
        ],
        "darwin": [
            os.path.expanduser("~/Library/Application Support/Steam")
        ]
    }

    for path in platform_paths.get(sys.platform, []):
        if os.path.isdir(path):
            return path
    
    return None

def parse_libraryfolders_vdf(vdf_path: str) -> List[str]:
    """解析Steam的libraryfolders.vdf文件"""
    if not os.path.isfile(vdf_path):
        return []

    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            data = {}
            for line in f:
                if '"path"' in line:
                    parts = line.strip().split('"')
                    if len(parts) >= 5:
                        path = parts[3].replace("\\\\", "\\")
                        data[parts[1]] = path
            return list(data.values())
    except Exception:
        return []

def find_steam_libraries(steam_path: str) -> Set[str]:
    """获取所有Steam库路径"""
    libraries = set()
    libraries.add(steam_path)  # 添加主库
    
    # 解析额外的库
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    for path in parse_libraryfolders_vdf(vdf_path):
        if os.path.isdir(path):
            libraries.add(os.path.normpath(path))
    
    return libraries

def find_common_dirs(libraries: Set[str]) -> List[str]:
    """获取所有common目录路径"""
    common_dirs = []
    for lib in libraries:
        common_path = os.path.join(lib, "steamapps", "common")
        if os.path.isdir(common_path):
            common_dirs.append(common_path)
    return common_dirs

def remove_empty_dirs(path: str, dry_run: bool = True) -> List[str]:
    """递归删除空文件夹并返回删除列表"""
    removed = []
    
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            dir_path = os.path.join(root, name)
            
            try:
                # 跳过非空目录和符号链接
                if not os.listdir(dir_path):
                    if not dry_run:
                        os.rmdir(dir_path)
                    removed.append(dir_path)
            except (PermissionError, FileNotFoundError, NotADirectoryError):
                continue
    
    return removed

def main():
    parser = argparse.ArgumentParser(description="清理Steam残留空文件夹")
    parser.add_argument("--apply", action="store_true", help="实际执行删除操作")
    parser.add_argument("--steam-path", help="指定Steam安装路径")
    args = parser.parse_args()

    # 获取Steam路径
    steam_path = args.steam_path or get_steam_install_path()
    if not steam_path or not os.path.isdir(steam_path):
        print("❌ 无法找到Steam安装目录，请手动指定路径：")
        print("    python script.py --steam-path \"你的Steam路径\"")
        return

    print(f"🔍 找到Steam安装目录: {steam_path}")
    
    # 获取所有库
    libraries = find_steam_libraries(steam_path)
    print(f"📚 找到 {len(libraries)} 个Steam库")
    
    # 获取common目录
    common_dirs = find_common_dirs(libraries)
    if not common_dirs:
        print("❌ 未找到任何游戏目录(steamapps/common)")
        return
    
    # 清理空文件夹
    total_removed = []
    for common in common_dirs:
        print(f"\n🔎 正在扫描: {common}")
        removed = remove_empty_dirs(common, dry_run=not args.apply)
        total_removed.extend(removed)
        
        if removed:
            print(f"🗑️ 找到 {len(removed)} 个空文件夹:")
            for path in removed:
                print(f"    {os.path.relpath(path, common)}")
        else:
            print("✅ 未发现空文件夹")
    
    # 结果汇总
    if total_removed:
        print(f"\n总计发现 {len(total_removed)} 个空文件夹")
        if args.apply:
            print("✅ 已成功删除所有空文件夹")
        else:
            print("\n⚠️ 注意：当前为预览模式，不会实际删除")
            print("    添加 --apply 参数执行删除操作")
    else:
        print("\n🎉 所有Steam库中均未发现残留空文件夹")

if __name__ == "__main__":
    main()