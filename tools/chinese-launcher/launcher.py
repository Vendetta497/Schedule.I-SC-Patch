"""Steam launch-options wrapper: repair after updates, then start the original game."""

import ctypes
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(__file__).resolve().parent
sys.path.insert(0, str(HOME))
from font_repair import ensure_fonts


def launch_options():
    return f'"{HOME / "runtime/pythonw.exe"}" "{HOME / "launcher.py"}" -- %command%'


def main(argv):
    if argv == ["--print-launch-options"]:
        print(launch_options())
        return 0
    if argv == ["--setup"]:
        target = HOME / "Steam启动选项.txt"
        target.write_text(launch_options() + "\n", encoding="utf-8-sig")
        os.startfile(str(target))
        return 0
    log_dir = HOME / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(log_dir / "latest.log"), level=logging.INFO,
                        format="%(asctime)s %(message)s", encoding="utf-8", filemode="w", force=True)
    def log(message):
        logging.info(message)
        if sys.stdout is not None:
            print(message, flush=True)
    log("中文自动修复启动器 1.0")
    repair_only = len(argv) == 2 and argv[0] in ("--repair-only", "--check-only")
    if repair_only:
        game = Path(argv[1]).resolve()
        command = None
    else:
        if argv and argv[0] == "--":
            argv = argv[1:]
        if not argv:
            raise RuntimeError("请从 Steam 开始游戏，或先用生成启动选项工具接入 Steam。")
        executable = Path(argv[0]).resolve()
        if executable.name.casefold() != "schedule i.exe" or not executable.is_file():
            raise RuntimeError(f"Steam 传入的游戏程序不正确：{executable}")
        game = executable.parent
        command = [str(executable)] + argv[1:]
    began = time.perf_counter()
    result = ensure_fonts(game, HOME, log, check_only=argv[0] == "--check-only")
    log("FONT_RESULT " + json.dumps(result, ensure_ascii=False))
    log(f"字体检查耗时 {time.perf_counter() - began:.2f} 秒。")
    if command is None:
        return 0
    # Do not relaunch Steam here: this is already the Steam child process.
    # Waiting for the game preserves Steam's running state and playtime tracking.
    log("GAME_LAUNCH " + json.dumps(command, ensure_ascii=False))
    child = subprocess.Popen(command, cwd=str(game))
    log(f"GAME_PID {child.pid}")
    code = child.wait()
    log(f"GAME_EXIT {code}")
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        logging.exception("启动失败，未继续启动游戏")
        message = f"中文自动修复启动失败：\n\n{error}\n\n详细日志：{HOME / 'logs/latest.log'}"
        if sys.stderr is not None:
            print(message, file=sys.stderr, flush=True)
        else:
            ctypes.windll.user32.MessageBoxW(None, message, "Schedule I 中文启动器", 0x10)
        raise SystemExit(1)
