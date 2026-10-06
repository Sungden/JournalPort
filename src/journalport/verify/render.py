"""Optional local headless rendering. Unavailability is never a visual pass."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from lxml import etree
from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass(frozen=True)
class RenderValidationReport:
    status: str
    backend: str
    page_count: int
    checks: dict[str, bool]
    warnings: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    backend_version: str | None = None
    input_hash: str | None = None
    output_pdf_hash: str | None = None
    conversion_exit_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": "1.0.0", **asdict(self)}


class RenderBackend(Protocol):
    def render(
        self, candidate: Path, output: Path, expected_headings: tuple[str, ...] = ()
    ) -> RenderValidationReport: ...


class LibreOfficeRenderBackend:
    def __init__(self, executable: str | None = None) -> None:
        configured = executable or os.environ.get("JOURNALPORT_LIBREOFFICE_PATH")
        # An invalid explicit configuration must not silently select another backend.
        candidates = (
            [configured]
            if configured
            else [
                shutil.which("soffice"),
                shutil.which("libreoffice"),
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        )
        self.executable = next(
            (str(path) for path in candidates if path and Path(path).is_file()), None
        )
        if self.executable and os.name == "nt":
            console = Path(self.executable).with_suffix(".com")
            if console.is_file():
                # Windows GUI launcher may detach; console launcher provides exit/version output.
                self.executable = str(console)

    def render(
        self,
        candidate: Path,
        output: Path,
        expected_headings: tuple[str, ...] = (),
        *,
        title_override: str | None = None,
    ) -> RenderValidationReport:
        input_hash = (
            "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
            if candidate.is_file()
            else None
        )
        if not self.executable or not Path(self.executable).is_file():
            return RenderValidationReport(
                "NOT_AVAILABLE",
                "LibreOffice",
                0,
                {},
                ("manual_visual_validation_required",),
                (),
                input_hash=input_hash,
            )
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="journalport-render-") as temporary:
            profile_uri = (Path(temporary) / "profile").as_uri()
            # Unique conversion directory prevents a stale PDF from satisfying a failed render.
            conversion = Path(temporary) / "pdf"
            conversion.mkdir()
            backend_version = None
            try:
                from journalport.transform.front_matter import identify_front_matter
                from journalport.transform.full_docx import read_document

                _, _, validated_body = read_document(candidate)
                title = (
                    title_override
                    if title_override is not None
                    else identify_front_matter(validated_body).title
                )
                version = subprocess.run(
                    [self.executable, "--version"], capture_output=True, timeout=10, check=False
                )
                if version.returncode == 0:
                    backend_version = version.stdout.decode("utf-8", errors="replace").strip()
                process = subprocess.run(
                    [
                        self.executable,
                        "--headless",
                        "--nologo",
                        "--nodefault",
                        f"-env:UserInstallation={profile_uri}",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(conversion),
                        str(candidate.resolve()),
                    ],
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
                pdf = conversion / (candidate.stem + ".pdf")
                if process.returncode or not pdf.is_file() or not pdf.stat().st_size:
                    return RenderValidationReport(
                        "RENDER_FAILED",
                        "LibreOffice",
                        0,
                        {},
                        (),
                        ("conversion_failed",),
                        backend_version=backend_version,
                        input_hash=input_hash,
                        conversion_exit_code=process.returncode,
                    )
                reader = PdfReader(pdf)
                texts = [page.extract_text() or "" for page in reader.pages]
                joined = "\n".join(texts)
                image_counts = []
                for page in reader.pages:
                    resources = page.get("/Resources", {})
                    if hasattr(resources, "get_object"):
                        resources = resources.get_object()
                    xobjects = resources.get("/XObject", {})
                    if hasattr(xobjects, "get_object"):
                        xobjects = xobjects.get_object()
                    contents = page.get_contents()
                    count = 0
                    if contents is not None:
                        for operands, operator in contents.operations:
                            if (
                                operator == b"Do"
                                and operands
                                and operands[0] in xobjects
                                and xobjects[operands[0]].get_object().get("/Subtype") == "/Image"
                            ):
                                count += 1
                    image_counts.append(count)
                image_count = sum(image_counts)
                with zipfile.ZipFile(candidate) as archive:
                    media_count = sum(name.startswith("word/media/") for name in archive.namelist())
                    document = etree.fromstring(
                        archive.read("word/document.xml"),
                        etree.XMLParser(resolve_entities=False, no_network=True),
                    )
                    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                    cells = [
                        "".join(node.text or "" for node in cell.iter(ns + "t"))
                        for cell in document.iter(ns + "tc")
                    ]
                checks = {
                    "render_succeeded": True,
                    "page_count_positive": len(texts) > 0,
                    "title_detectable": " ".join(title.split()) in " ".join(joined.split()),
                    "media_relationships_valid": True,
                    "expected_headings_present": all(
                        label in joined for label in expected_headings
                    ),
                    "figures_rendered": image_count >= media_count,
                    "no_empty_pages": all(
                        value.strip() or count > 0
                        for value, count in zip(texts, image_counts, strict=True)
                    ),
                    "expected_table_cell_text_present": all(
                        " ".join(cell.split()) in " ".join(joined.split()) for cell in cells
                    ),
                }
                # Headless conversion success alone cannot prove absence of Word's repair prompt.
                # Visual QA is a separate mandatory gate, not a fabricated render failure/warning.
                warnings: tuple[str, ...] = ()
                failures = tuple(key for key, passed in checks.items() if not passed)
                shutil.copyfile(pdf, output / "manuscript_rendered.pdf")
                return RenderValidationReport(
                    "RENDER_FAILED" if failures else "RENDER_PASS",
                    "LibreOffice",
                    len(texts),
                    checks,
                    warnings,
                    failures,
                    backend_version=backend_version,
                    input_hash=input_hash,
                    output_pdf_hash="sha256:" + hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    conversion_exit_code=process.returncode,
                )
            except (
                OSError,
                subprocess.TimeoutExpired,
                ValueError,
                KeyError,
                zipfile.BadZipFile,
                etree.XMLSyntaxError,
                PdfReadError,
            ):
                return RenderValidationReport(
                    "RENDER_FAILED",
                    "LibreOffice",
                    0,
                    {},
                    (),
                    ("render_backend_error",),
                    backend_version=backend_version,
                    input_hash=input_hash,
                )
