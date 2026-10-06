#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Microsoft Data Stack's README diagrams: architecture (the solution) and tech stack
(where each tool lives), on one layout. Run it to regenerate both .excalidraw.svg files here.
The kit is Rai's /media → diagram; RAI_DIAGRAM_KIT points elsewhere if needed.
"""

import os
import sys
from collections.abc import Callable
from pathlib import Path

DEFAULT_KIT = Path.home() / "helm/03-rai/skills/media/scripts/diagram"
KIT = Path(os.environ.get("RAI_DIAGRAM_KIT", DEFAULT_KIT))
sys.path.insert(0, str(KIT))
from lib import MUTED, VIOLET, Scene, render  # ty: ignore[unresolved-import]

HERE = Path(__file__).parent
# The product image Microsoft's registry shows for mcr.microsoft.com/mssql/server.
SQL_SERVER = ("url:https://mcr.microsoft.com/api/v1/catalog/productimage/"
              "fabff15d63c0a3bfc9feadca7f0a79bee59ca7a0da68798209bb9fa9b9b15b2c")
AIRFLOW = "url:https://airflow.apache.org/images/airflow-icon.svg"
CSV = "url:https://cdn.jsdelivr.net/npm/@tabler/icons@latest/icons/outline/file-type-csv.svg"
# zone: (x, y, w, h, title)
Z = {
    "source": (0, 150, 220, 320, "SOURCE"),
    "ingest": (390, 150, 320, 320, "INGEST"),
    "warehouse": (830, 150, 460, 320, "WAREHOUSE"),
    "consume": (1410, 150, 300, 320, "CONSUME"),
    "schema": (390, 580, 320, 230, "SCHEMA"),
    "transform": (830, 580, 460, 230, "TRANSFORM"),
    "checks": (340, 930, 1420, 190, "CHECKS"),
}
MID = 310


def frame(s: Scene, header: Callable[[Scene], None]) -> None:
    """Zones, the Docker Compose box and the labelled arrows: the same in both diagrams."""
    s.zone(340, 0, 1420, 860, None, dotted=True)
    header(s)
    for x, y, w, h, title in Z.values():
        s.zone(x, y, w, h, title)
    s.arrow([(222, MID), (388, MID)], label="extract\nJSON, CSV", at=(226, MID - 60, 108))
    s.arrow([(712, MID), (828, MID)], label="load\nraw tables", at=(711, MID - 60, 118))
    s.arrow([(1292, MID), (1408, MID)], label="query\nviews", at=(1291, MID - 60, 118))
    s.arrow([(990, 472), (990, 578)], label="read\nraw, staging", at=(866, 500, 116))
    s.arrow([(1130, 578), (1130, 472)], label="write\nstaging to marts",
            at=(1140, 500, 160))
    s.arrow([(712, 695), (770, 695), (770, 420), (828, 420)], color=VIOLET, dashed=True,
            label="create\ntables, views", at=(645, 500, 120))
    s.arrow([(420, 928), (420, 862)], color=MUTED, dashed=True,
            label="check\nthe project", at=(430, 870, 130))


def row(
    s: Scene, zone: str, items: list[tuple[str, str]], top: int | None = None
) -> None:
    """Logos with names, spread evenly across a zone."""
    x, y, w, h, _ = Z[zone]
    slot = w / len(items)
    top = y + h // 2 - 60 if top is None else top
    for j, (key, name) in enumerate(items):
        s.tool(x + slot * j + slot / 2, top, key, name, w=slot)


def tech_stack() -> None:
    s = Scene()

    def header(s: Scene) -> None:
        s.tool(450, 14, "si:docker", "Docker Compose", w=180)

    frame(s, header)
    row(s, "source", [("si:json", "Fake Store API")], top=205)
    row(s, "source", [(CSV, "sample CSVs")], top=335)
    row(s, "ingest", [(AIRFLOW, "Apache Airflow")])
    row(s, "warehouse", [(SQL_SERVER, "SQL Server")])
    row(s, "consume", [("si:apachesuperset", "Apache Superset")])
    row(s, "schema", [(SQL_SERVER, "sqlcmd")], top=660)
    row(s, "transform", [(AIRFLOW, "Apache Airflow")], top=660)
    row(s, "checks", [("si:uv", "uv"), ("si:ruff+#261230", "Ruff"),
                      ("si:pytest", "pytest")], top=980)
    s.save("tech-stack")


def architecture() -> None:
    s = Scene()

    frame(s, lambda s: None)

    def parts(
        zone: str, labels: list[str], top: int, h: int = 52, gap: int = 14,
        left: int = 20, w: int | None = None,
    ) -> None:
        x, _, zw, _, _ = Z[zone]
        for label in labels:
            s.part(x + left, top, w or zw - 2 * left, h, label)
            top += h + gap

    parts("source", ["Fake Store API", "sample CSV files"], top=250)
    parts("ingest", ["extract API, CSV", "flatten records", "log received, stored"],
          top=222)
    parts("warehouse", ["raw", "staging", "star schema", "marts"], top=205, h=48,
          gap=12, w=200)
    parts("warehouse", ["quality log", "dashboard views"], top=265, h=48, gap=12,
          left=240, w=200)
    parts("consume", ["sales dashboard", "quality dashboard", "SQL Lab"], top=222)
    parts("schema", ["init container", "SQL files, in order"], top=656)
    parts("transform", ["clean, validate", "load star schema", "rebuild marts"],
          top=631, h=48, gap=12)
    x, y, w, _, _ = Z["checks"]
    checks = ["lint, format", "types", "unit tests, API mocked"]
    slot = w / len(checks)
    for j, label in enumerate(checks):
        s.part(x + slot * j + slot / 2 - 160, y + 70, 320, 64, label)
    s.save("architecture")


tech_stack()
architecture()
render(HERE, "architecture", "tech-stack")
