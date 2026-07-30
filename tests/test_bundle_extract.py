import io
import tarfile
from pathlib import Path

import pytest

from atlas_memory.commands_sync import UnsafeBundleError, export_bundle, extract_bundle, import_bundle


def add_file(tar: tarfile.TarFile, name: str, content: bytes = b"pwned\n") -> None:
    info = tarfile.TarInfo(name)
    info.size = len(content)
    tar.addfile(info, io.BytesIO(content))


def test_parent_traversal_is_refused(tmp_path: Path):
    bundle = tmp_path / "evil.tar.gz"
    with tarfile.open(bundle, "w:gz") as tar:
        add_file(tar, "../../escaped.txt")

    with pytest.raises(UnsafeBundleError, match="escapes"):
        extract_bundle(bundle, tmp_path / "out")
    assert not (tmp_path.parent / "escaped.txt").exists()


def test_absolute_path_is_refused(tmp_path: Path):
    bundle = tmp_path / "evil.tar.gz"
    with tarfile.open(bundle, "w:gz") as tar:
        add_file(tar, "/tmp/atlas-pwned.txt")

    with pytest.raises(UnsafeBundleError):
        extract_bundle(bundle, tmp_path / "out")


def test_symlink_is_refused(tmp_path: Path):
    bundle = tmp_path / "evil.tar.gz"
    with tarfile.open(bundle, "w:gz") as tar:
        link = tarfile.TarInfo("atlas/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "../../../../etc/passwd"
        tar.addfile(link)

    with pytest.raises(UnsafeBundleError, match="link"):
        extract_bundle(bundle, tmp_path / "out")


def test_device_files_are_refused(tmp_path: Path):
    bundle = tmp_path / "evil.tar.gz"
    with tarfile.open(bundle, "w:gz") as tar:
        dev = tarfile.TarInfo("atlas/dev")
        dev.type = tarfile.CHRTYPE
        tar.addfile(dev)

    with pytest.raises(UnsafeBundleError, match="special file"):
        extract_bundle(bundle, tmp_path / "out")


def test_nothing_is_written_when_a_member_is_unsafe(tmp_path: Path):
    bundle = tmp_path / "mixed.tar.gz"
    with tarfile.open(bundle, "w:gz") as tar:
        add_file(tar, "atlas/ok.txt")
        add_file(tar, "../escaped.txt")

    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(UnsafeBundleError):
        extract_bundle(bundle, dest)
    assert list(dest.iterdir()) == []


def test_a_normal_bundle_still_round_trips(tmp_path: Path):
    source = tmp_path / "source"
    cursor = source / ".cursor"
    (cursor / "atlas-drawers" / "architecture").mkdir(parents=True)
    (cursor / "mempalace-index.md").write_text("# wings\n", encoding="utf-8")
    (cursor / "project-cache.md").write_text("# Project Source Cache\n", encoding="utf-8")
    (cursor / "atlas-drawers" / "architecture" / "a.drawer.md").write_text(
        "[type:decision] [status:active]\nsummary: keep it\nwhy: because\n", encoding="utf-8"
    )
    bundle = export_bundle(source)

    target = tmp_path / "target"
    (target / ".cursor").mkdir(parents=True)
    actions = import_bundle(target, bundle)

    assert (target / ".cursor" / "mempalace-index.md").exists()
    assert any("drawer" in a for a in actions)
