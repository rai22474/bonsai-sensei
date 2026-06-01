import re
from pathlib import Path
from typing import Callable

from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)
REPORTS_INDEX_WIKI = _env.get_template("reports_index_wiki.j2")


def create_update_bonsai_reports_index_tool(
    list_wiki_files_func: Callable,
    write_wiki_page_func: Callable,
) -> Callable:
    @trace_tool_call
    async def update_bonsai_reports_index(bonsai_name: str) -> dict:
        """Regenerate the reports index page for a bonsai. Call this after writing any new report.

        Args:
            bonsai_name: Name of the bonsai whose reports index should be updated.

        Returns:
            {"status": "success"} always.
        """
        slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
        paths = list_wiki_files_func(f"bonsai/{slug}/reports")
        report_files = [path for path in paths if not path.endswith("index.md")]
        reports = sorted(
            filter(None, (_parse_report(path) for path in report_files)),
            key=lambda report: report["date"],
            reverse=True,
        )
        write_wiki_page_func(
            path=f"bonsai/{slug}/reports/index.md",
            content=REPORTS_INDEX_WIKI.render(bonsai_name=bonsai_name, reports=reports),
        )
        return {"status": "success"}

    return update_bonsai_reports_index


def _parse_report(path: str) -> dict | None:
    filename = path.split("/")[-1].removesuffix(".md")
    if len(filename) < 12 or filename[4] != "-" or filename[7] != "-":
        return None
    return {"date": filename[:10], "type": filename[11:], "path": path}
