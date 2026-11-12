import threading

from PIL import Image

from evrakci.ui.thumbnails import ThumbnailService


class CountingRenderer:
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, pid, height):
        with self.lock:
            self.calls.append(pid)
        return Image.new("RGB", (int(height * 0.7), height), "white")


def test_only_requested_pages_are_rendered_in_a_1000_page_job(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=100)
    visible = [f"b1/{i}" for i in range(200, 212)]
    got = []
    service.ready.connect(lambda pid, image: got.append((pid, image.height())))
    for pid in visible:
        service.request(pid)
    qtbot.waitUntil(lambda: len(got) == len(visible), timeout=5000)
    assert sorted(renderer.calls) == sorted(visible)
    assert all(height == 100 for _, height in got)


def test_cached_pages_are_not_rendered_twice(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=100)
    got = []
    service.ready.connect(lambda pid, image: got.append(pid))
    service.request("b1/0")
    qtbot.waitUntil(lambda: len(got) == 1, timeout=5000)
    service.request("b1/0")
    assert got == ["b1/0", "b1/0"]
    assert renderer.calls == ["b1/0"]


def test_cache_is_bounded(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=20, capacity=5, workers=1)  # fixed order
    got = []
    service.ready.connect(lambda pid, image: got.append(pid))
    for i in range(12):
        service.request(f"b1/{i}")
    qtbot.waitUntil(lambda: len(got) == 12, timeout=5000)
    assert len(service.cache) == 5
    assert "b1/11" in service.cache and "b1/0" not in service.cache


def test_requests_no_longer_visible_are_dropped(qtbot):
    gate = threading.Event()
    renderer = CountingRenderer()

    def slow(pid, height):
        gate.wait(2)
        return renderer(pid, height)

    service = ThumbnailService(slow, height=20, workers=1)
    for i in range(10):
        service.request(f"b1/{i}")
    service.keep_only({"b1/0", "b1/9"})
    gate.set()
    qtbot.waitUntil(lambda: service.idle(), timeout=5000)
    assert set(renderer.calls) <= {"b1/0", "b1/9"}


def test_job_renderer_draws_a_real_page_at_the_requested_height(tmp_path):
    from fakes import job_from_kinds, make_pdf, text_page

    from evrakci.ui.thumbnails import job_renderer

    pdf = make_pdf(tmp_path / "b1.pdf", [text_page("A"), text_page("B")])
    job = job_from_kinds({"b1": "pp"})
    job.rotate("b1/1", 90)
    render = job_renderer(job, lambda: {"b1": pdf})
    assert render("b1/0", 100).height == 100
    rotated = render("b1/1", 100)
    assert rotated.height == 100 and rotated.width > 100  # landscape after rotation
