import asyncio
import functools
import gzip
import hashlib
import http.server
import io
import tarfile
import threading
import zipfile

import pytest

from vtk_demo import data
from vtk_demo.data import ArchiveMember, DataSet, License, MetaData, RemoteLocation


def test_registry():
    datasets = data.list_datasets()
    assert len(datasets) > 50
    for ds in datasets:
        assert ds.tags, ds.name
        assert ds.meta.description, ds.name
        assert ds.size, ds.name
        for loc in ds.locations:
            assert loc.known_hash.startswith("sha256:"), ds.name
    assert "medical" in data.list_tags()


def test_filter_by_tags():
    medical = data.list_datasets(["medical"])
    assert data.get("head") in medical
    assert data.get("bunny") not in medical
    both = data.list_datasets(["medical", "pdb"])
    assert data.get("caffeine") in both
    assert data.get("head") in both


def test_license():
    assert License.BSD.value == "BSD-3-Clause"
    assert License.CC_BY_4.commercial_use
    assert not License.CC_BY_NC_SA_4.commercial_use


def test_print_usage(capsys):
    data.get("nefertiti").print_usage()
    out = capsys.readouterr().out
    assert "Dataset:     nefertiti" in out
    assert "CC-BY-NC-SA-4.0 (non-commercial" in out
    assert "Reference:   https://nefertitihack.alloversky.com/" in out
    assert "Nefertiti.obj.zip" in out

    usage = data.get("skybox").usage
    assert "Apache-2.0\n" in usage
    assert usage.count("/skybox/skybox-") == 6


def test_duplicate_name():
    with pytest.raises(ValueError, match="already registered"):
        DataSet("bunny", RemoteLocation("http://x/a.vtp"), MetaData("me", License.MIT))


def test_cannot_uncompress():
    with pytest.raises(ValueError, match="uncompress"):
        RemoteLocation("http://x/a.vtp", uncompress=True)


@pytest.fixture
def server(tmp_path, monkeypatch):
    """Serve ``tmp_path / "remote"`` over http, and cache in ``tmp_path / "cache"``."""
    monkeypatch.setenv("VTK_DEMO_DATA", str(tmp_path / "cache"))
    remote = tmp_path / "remote"
    remote.mkdir()
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(remote)
    )
    handler.log_message = lambda *args: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield remote, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    DataSet.AVAILABLE_DATASETS = {
        k: v for k, v in DataSet.AVAILABLE_DATASETS.items() if not k.startswith("test-")
    }


def wait_available(ds):
    async def main():  # asyncio.run() only takes awaitables from Python 3.12
        return await ds.available

    return asyncio.run(main())


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_download_files(server, tmp_path):
    remote, url = server
    (remote / "a.mhd").write_text("ElementDataFile = a.raw\n")
    with gzip.open(remote / "a.raw.gz", "wb") as f:
        f.write(b"raw")

    ds = DataSet(
        "test-files",
        [
            RemoteLocation(f"{url}/a.mhd", sha256(remote / "a.mhd"), fname="t/a.mhd"),
            RemoteLocation(f"{url}/a.raw.gz", uncompress=True, fname="t/a.raw.gz"),
        ],
        MetaData("me", License.MIT, tags={"test"}),
    )
    cache = tmp_path / "cache"
    assert not ds.is_local
    assert ds.files == [cache / "t/a.mhd", cache / "t/a.raw"]
    assert ds.path == cache / "t/a.mhd"
    assert ds.is_local
    assert (cache / "t/a.raw").read_bytes() == b"raw"


def test_download_archive(server, tmp_path):
    remote, url = server
    with zipfile.ZipFile(remote / "case.zip", "w") as z:
        z.writestr("case.foam", "")
        z.writestr("0/U", "U")

    ds = DataSet(
        "test-archive",
        RemoteLocation(f"{url}/case.zip", sha256(remote / "case.zip"), uncompress=True),
        MetaData("me", License.MIT),
        entry="case.foam",
    )
    assert ds.files == [tmp_path / "cache/case"]

    assert wait_available(ds) == tmp_path / "cache/case/case.foam"
    assert ds.path == tmp_path / "cache/case/case.foam"
    assert (tmp_path / "cache/case/0/U").read_text() == "U"


def _tar_xz(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:xz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_download_archive_member(server, tmp_path):
    remote, url = server
    (remote / "all.tar.xz").write_bytes(
        _tar_xz(
            {
                "all/a.tar.xz": _tar_xz({"a/x.vtu": b"ax"}),
                "all/b.tar.xz": _tar_xz({"b/y.vtu": b"by"}),
            }
        )
    )

    def member(name):
        return DataSet(
            f"test-member-{name}",
            ArchiveMember(
                f"{url}/all.tar.xz",
                sha256(remote / "all.tar.xz"),
                fname="m/all.tar.xz",
                member=f"all/{name}.tar.xz",
            ),
            MetaData("me", License.MIT),
            entry=name,
        )

    a, b = member("a"), member("b")
    cache = tmp_path / "cache"
    assert a.files == [cache / "m/a"]
    assert a.path == cache / "m/a/a"
    assert (cache / "m/a/a/x.vtu").read_bytes() == b"ax"
    assert not b.is_local
    assert wait_available(b) == cache / "m/b/b"
    assert (cache / "m/b/b/y.vtu").read_bytes() == b"by"
    assert sorted(p.name for p in (cache / "m").iterdir()) == ["a", "all.tar.xz", "b"]

    with pytest.raises(ValueError, match="tar archive"):
        ArchiveMember(f"{url}/all.tar.xz", member="all/a.vtu")


def test_available_shares_one_download(server, tmp_path):
    remote, url = server
    (remote / "a.vtp").write_text("a")
    ds = DataSet(
        "test-shared",
        RemoteLocation(f"{url}/a.vtp", sha256(remote / "a.vtp")),
        MetaData("me", License.MIT),
    )
    calls = []
    download = ds._download
    ds._download = lambda: calls.append(1) or download()

    async def main():
        return await asyncio.gather(ds.available, ds.available, ds.available)

    assert asyncio.run(main()) == [tmp_path / "cache/a.vtp"] * 3
    assert calls == [1]
    assert ds._future is None


def test_bad_hash(server):
    remote, url = server
    (remote / "a.vtp").write_text("a")
    ds = DataSet(
        "test-bad-hash",
        RemoteLocation(f"{url}/a.vtp", "sha256:" + "0" * 64),
        MetaData("me", License.MIT),
    )
    with pytest.raises(ValueError, match="SHA256"):
        ds.path  # noqa: B018
    assert not ds.is_local

    # Awaiting raises the failure, then retries on the next await
    for _ in range(2):
        with pytest.raises(ValueError, match="SHA256"):
            wait_available(ds)
        assert ds._future is None


def test_await_available(server, tmp_path):
    remote, url = server
    (remote / "a.vtp").write_text("a")
    ds = DataSet(
        "test-available",
        RemoteLocation(f"{url}/a.vtp", sha256(remote / "a.vtp")),
        MetaData("me", License.MIT),
    )

    available = ds.available  # lazy: nothing downloaded yet
    assert ds._future is None
    assert not ds.is_local

    async def main():
        await available
        assert ds.is_local
        return ds.path, await ds.available  # already local: returns right away

    assert asyncio.run(main()) == (tmp_path / "cache/a.vtp",) * 2
