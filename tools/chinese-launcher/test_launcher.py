"""Unit checks plus optional regression against a local, unmodified game asset."""

import argparse
import contextlib
import hashlib
import io
import json
import logging
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import launcher
import font_repair


def close_log_handlers():
    for handler in list(logging.getLogger().handlers):
        handler.close()
        logging.getLogger().removeHandler(handler)


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ScheduleI-launcher-unit-")
        self.root = Path(self.temp.name).resolve()
        if not self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise RuntimeError("Test directory escaped the expected temporary root")
        self.home = self.root / "launcher path"
        self.home.mkdir()

    def tearDown(self):
        close_log_handlers()
        self.temp.cleanup()

    def test_preserves_steam_arguments_and_waits(self):
        game = self.root / "游戏 with spaces"
        game.mkdir()
        executable = game / "Schedule I.exe"
        executable.write_bytes(b"NOT AN EXECUTABLE; NEVER RUN THIS FIXTURE")
        arguments = [str(executable), "-beta", "--example=two words", "中文参数"]
        with patch.object(launcher, "HOME", self.home), \
             patch.object(launcher, "ensure_fonts", return_value={"status": "cached"}) as repair, \
             patch.object(launcher.subprocess, "Popen") as popen:
            popen.return_value.pid = 123
            popen.return_value.wait.return_value = 0
            self.assertEqual(launcher.main(["--"] + arguments), 0)
            repair.assert_called_once()
            popen.assert_called_once_with(arguments, cwd=str(game))
            popen.return_value.wait.assert_called_once_with()

    def test_bad_font_check_never_starts_game(self):
        executable = self.root / "Schedule I.exe"
        executable.write_bytes(b"FIXTURE")
        with patch.object(launcher, "HOME", self.home), \
             patch.object(launcher, "ensure_fonts", side_effect=RuntimeError("bad font")), \
             patch.object(launcher.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "bad font"):
                launcher.main(["--", str(executable)])
            popen.assert_not_called()

    def test_rejects_other_executable(self):
        executable = self.root / "other.exe"
        executable.write_bytes(b"FIXTURE")
        with patch.object(launcher, "HOME", self.home), patch.object(launcher.subprocess, "Popen") as popen:
            with self.assertRaises(RuntimeError):
                launcher.main(["--", str(executable)])
            popen.assert_not_called()

    def test_generates_path_for_this_computer(self):
        with patch.object(launcher, "HOME", self.home):
            options = launcher.launch_options()
        self.assertIn(f'"{self.home / "runtime/pythonw.exe"}"', options)
        self.assertIn(f'"{self.home / "launcher.py"}"', options)
        self.assertTrue(options.endswith(" -- %command%"))


def asset_regression(original_asset, chinese_font):
    import UnityPy
    from fontTools.ttLib import TTFont
    original_asset = original_asset.resolve()
    before_source_hash = font_repair.file_sha(original_asset)
    records = []
    with tempfile.TemporaryDirectory(prefix="ScheduleI-launcher-asset-") as temporary:
        root = Path(temporary).resolve()
        if not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise RuntimeError("Test directory escaped the expected temporary root")
        game, home = root / "game", root / "launcher"
        asset = game / "Schedule I_Data/sharedassets0.assets"
        asset.parent.mkdir(parents=True)
        (home / "fonts").mkdir(parents=True)
        shutil.copy2(original_asset, asset)
        shutil.copy2(chinese_font, home / "fonts/chinese.ttf")
        mod = game / "Mods/unchanged.dll"
        mod.parent.mkdir()
        mod.write_bytes(b"MOD SENTINEL")
        translation = game / "AutoTranslator/Translation/zh-CN/Text/unchanged.txt"
        translation.parent.mkdir(parents=True)
        translation.write_text("Continue=继续\n", encoding="utf-8")
        before = UnityPy.load(asset.read_bytes())
        selected = next(obj for obj in before.objects
                        if obj.type.name == "Font" and obj.peek_name() == "OpenSans-Regular")
        metadata = selected.read_typetree()
        metadata.pop("m_FontData")
        # The fixture is not the running game. Never stop or modify the installed game for these checks.
        with patch.object(font_repair, "game_running", return_value=False):
            began = time.perf_counter()
            first = font_repair.ensure_fonts(game, home)
            assert first["status"] == "repaired" and first["repaired_fonts"]
            repaired_hash = font_repair.file_sha(asset)
            records.append({"case": "repair_updated_assets", "passed": True,
                            "seconds": time.perf_counter() - began,
                            "fonts": len(first["repaired_fonts"]), "objects": first["objects_preserved"]})
            after = UnityPy.load(asset.read_bytes())
            selected = next(obj for obj in after.objects
                            if obj.type.name == "Font" and obj.peek_name() == "OpenSans-Regular")
            decoded = selected.read_typetree()
            raw_font = bytes(decoded.pop("m_FontData"))
            assert decoded == metadata
            assert hashlib.sha256(raw_font).hexdigest() == font_repair.file_sha(home / "fonts/chinese.ttf")
            with TTFont(io.BytesIO(raw_font)) as font:
                assert all(ord(ch) in font.getBestCmap() for ch in "中文继续退出")
            records.append({"case": "independent_decode_preserves_font_metadata", "passed": True})
            timestamp = asset.stat().st_mtime_ns
            second = font_repair.ensure_fonts(game, home)
            assert second["status"] == "cached" and asset.stat().st_mtime_ns == timestamp
            assert font_repair.file_sha(asset) == repaired_hash
            records.append({"case": "repeat_launch_does_not_rewrite", "passed": True})
            shutil.copy2(original_asset, asset)
            restored = font_repair.ensure_fonts(game, home)
            assert restored["status"] == "repaired" and font_repair.file_sha(asset) == repaired_hash
            records.append({"case": "steam_update_overwrites_fonts_then_repairs_again", "passed": True})
            (home / "fonts/chinese.ttf").write_bytes(b"INVALID FONT")
            failed = False
            try:
                font_repair.ensure_fonts(game, home)
            except Exception:
                failed = True
            assert failed and font_repair.file_sha(asset) == repaired_hash
            records.append({"case": "invalid_font_never_changes_assets", "passed": True})
        with patch.object(font_repair, "game_running", return_value=True):
            try:
                font_repair.ensure_fonts(game, home)
                raise AssertionError("A running game should prevent repair")
            except RuntimeError as error:
                assert "游戏还在运行" in str(error)
        assert mod.read_bytes() == b"MOD SENTINEL"
        assert translation.read_text(encoding="utf-8") == "Continue=继续\n"
        assert font_repair.file_sha(original_asset) == before_source_hash
        records.append({"case": "running_game_guard_and_unrelated_files", "passed": True})
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-asset", type=Path)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if bool(args.original_asset) != bool(args.font):
        parser.error("Supply --original-asset and --font together")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WrapperTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"wrapper_tests_passed": result.testsRun}
    if args.original_asset:
        report["asset_cases"] = asset_regression(args.original_asset, args.font)
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
