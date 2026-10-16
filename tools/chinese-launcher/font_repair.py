"""Patch only embedded font bytes in the current assets; preserve other objects."""

import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA = 1
SAMPLE = "简体中文游戏设置开始继续退出保存读取星期任务员工汽油酷乐电池巨型豆"


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def game_running():
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["tasklist.exe", "/FI", "IMAGENAME eq Schedule I.exe", "/FO", "CSV", "/NH"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW, check=True,
    )
    return b'"schedule i.exe"' in result.stdout.lower()


def require_closed():
    if game_running():
        raise RuntimeError("游戏还在运行。请先正常退出游戏，再重新点击开始游戏。")


@contextmanager
def repair_lock(folder):
    import msvcrt
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "repair.lock").open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError("另一个启动器正在检查字体，请稍候再试。") from error
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def font_span(obj, raw):
    """Locate m_FontData from its type tree without decoding millions of bytes."""
    from UnityPy.helpers.TypeTreeHelper import TypeTreeConfig, read_value
    from UnityPy.streams import EndianBinaryReader
    reader = EndianBinaryReader(raw, endian=obj.reader.endian)
    config = TypeTreeConfig(True, obj.assets_file, False)
    for child in obj._get_typetree_node().m_Children:
        if child.m_Name != "m_FontData":
            read_value(child, reader, config)
            continue
        if child.m_Type != "vector" or len(child.m_Children) != 1:
            raise RuntimeError("新版字体数据结构改变，已停止修复，原文件保持不变。")
        array = child.m_Children[0]
        if array.m_Type != "Array" or len(array.m_Children) != 2:
            raise RuntimeError("无法识别字体字节数组，原文件保持不变。")
        if array.m_Children[1].m_Type not in ("char", "UInt8", "unsigned char"):
            raise RuntimeError("字体数组不是字节数据，原文件保持不变。")
        align = bool(((child.m_MetaFlag or 0) | (array.m_MetaFlag or 0)) & 0x4000)
        begin = reader.Position
        length = reader.read_int()
        if length < 0 or begin + 4 + length > len(raw):
            raise RuntimeError("字体数据长度错误，原文件保持不变。")
        data = reader.read_bytes(length)
        if align:
            reader.align_stream()
        return begin, reader.Position, data, align
    raise RuntimeError("未找到内嵌字体数据，原文件保持不变。")


def replace_font_raw(obj, raw, replacement):
    begin, end, old, align = font_span(obj, raw)
    field = struct.pack(obj.reader.endian + "i", len(replacement)) + replacement
    if align:
        field += b"\0" * (-(begin + len(field)) % 4)
    return raw[:begin] + field + raw[end:], old


def chinese_supported(raw):
    from fontTools.ttLib import TTFont
    with TTFont(io.BytesIO(raw)) as font:
        cmap = font.getBestCmap() or {}
        return all(ord(character) in cmap for character in SAMPLE)


def protected_hashes(game):
    files = [game / "AutoTranslator/Config.ini"]
    for relative in ("Mods", "UserLibs", "AutoTranslator/Translation/zh-CN/Text"):
        files.extend(p for p in (game / relative).rglob("*") if p.is_file())
    return {str(p.relative_to(game)): file_sha(p) for p in files if p.is_file()}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def ensure_fonts(game, home, log=print, check_only=False):
    game, home = Path(game).resolve(), Path(home).resolve()
    source = game / "Schedule I_Data/sharedassets0.assets"
    font_path = home / "fonts/chinese.ttf"
    if not source.is_file():
        raise RuntimeError(f"找不到游戏资源文件：{source}")
    if not font_path.is_file():
        raise RuntimeError(f"启动器的中文字库丢失：{font_path}")
    require_closed()
    with repair_lock(home / "state"):
        source_hash = file_sha(source)
        replacement_hash = file_sha(font_path)
        key = hashlib.sha256(str(source).casefold().encode("utf-8")).hexdigest()[:20]
        state_path = home / "state" / f"{key}.json"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            state = {}
        if (state.get("schema") == SCHEMA and state.get("installed_sha256") == source_hash
                and state.get("font_sha256") == replacement_hash):
            log("字体文件未变化，跳过修复。")
            return {"status": "cached", "asset_sha256": source_hash, "game_directory": str(game)}

        log("检测到新版资源或首次启动，检查中文字体。")
        import UnityPy
        replacement = font_path.read_bytes()
        if not chinese_supported(replacement):
            raise RuntimeError("启动器字体校验失败，原游戏文件保持不变。")
        before_protected = protected_hashes(game)
        # In-memory loading avoids Windows file handles blocking the atomic replacement.
        env = UnityPy.load(source.read_bytes())
        objects = env.file.objects
        original = {pid: (obj.type.name, hashlib.sha256(obj.get_raw_data()).hexdigest())
                    for pid, obj in objects.items()}
        expected = dict(original)
        missing, checked = [], []
        for obj in objects.values():
            if obj.type.name != "Font":
                continue
            name = obj.peek_name()
            if not (name == "LiberationSans" or (name or "").startswith("OpenSans-")):
                continue
            raw = obj.get_raw_data()
            _, _, current, _ = font_span(obj, raw)
            checked.append({"id": obj.path_id, "name": name})
            if chinese_supported(current):
                continue
            patched_raw, _ = replace_font_raw(obj, raw, replacement)
            # Prefix/suffix are retained byte for byte; only the font array and its alignment change.
            obj.set_raw_data(patched_raw)
            expected[obj.path_id] = (obj.type.name, hashlib.sha256(patched_raw).hexdigest())
            missing.append({"id": obj.path_id, "name": name})
        if not checked:
            raise RuntimeError("新版资源中没有可识别的界面字体，已停止自动修复。")
        if check_only:
            return {"status": "needs_repair" if missing else "already_chinese",
                    "checked_fonts": checked, "missing_fonts": missing, "asset_sha256": source_hash}

        backup_dir = home / "backups" / source_hash[:20]
        report = {"schema": SCHEMA, "game_directory": str(game), "source_sha256": source_hash,
                  "font_sha256": replacement_hash, "checked_fonts": checked,
                  "repaired_fonts": missing, "objects_preserved": len(original),
                  "checked_at": datetime.now().astimezone().isoformat()}
        if missing:
            log(f"修复 {len(missing)} 个字体；校验全部 {len(original)} 个资源对象。")
            backup_dir.mkdir(parents=True, exist_ok=True)
            original_backup = backup_dir / "sharedassets0.original.assets"
            if original_backup.exists():
                if file_sha(original_backup) != source_hash:
                    raise RuntimeError("备份文件摘要不一致，已停止修复。")
            else:
                shutil.copy2(source, original_backup)
                if file_sha(original_backup) != source_hash:
                    raise RuntimeError("原文件备份校验失败，已停止修复。")
            temporary = source.with_name(f"sharedassets0.assets.chinese-{os.getpid()}.tmp")
            try:
                with temporary.open("xb") as stream:
                    stream.write(env.file.save())
                    stream.flush()
                    os.fsync(stream.fileno())
                check_env = UnityPy.load(temporary.read_bytes())
                if set(check_env.file.objects) != set(original):
                    raise RuntimeError("资源对象编号变化，已停止修复。")
                for pid, obj in check_env.file.objects.items():
                    actual = (obj.type.name, hashlib.sha256(obj.get_raw_data()).hexdigest())
                    if actual != expected[pid]:
                        raise RuntimeError(f"资源对象校验失败：{pid}，已停止修复。")
                require_closed()
                if file_sha(source) != source_hash:
                    raise RuntimeError("Steam 正在更新资源，请更新完成后再启动。")
                if protected_hashes(game) != before_protected:
                    raise RuntimeError("词库或模组文件发生外部变化，请稍后再启动。")
                prepared_hash = file_sha(temporary)
                os.replace(temporary, source)
                if file_sha(source) != prepared_hash:
                    shutil.copy2(original_backup, source)
                    raise RuntimeError("安装校验失败，已恢复原资源。")
            finally:
                if temporary.exists():
                    temporary.unlink()
            report.update(status="repaired", installed_sha256=prepared_hash,
                          backup_directory=str(backup_dir), protected_files_unchanged=True)
            save_json(backup_dir / "repair-report.json", report)
            log("字体修复与资源校验通过。")
        else:
            report.update(status="already_chinese", installed_sha256=source_hash)
            log("当前字体已经支持中文，无需改动。")
        save_json(state_path, report)
        return report
