"""
Structured Table Extraction and Data Analysis Service for Step 30: Multimodal AI.
Parses CSV and XLSX spreadsheets into normalized, budget-controlled TableArtifact models.
Supports schema-only, sample rows, statistical summary, and bounded extraction.
"""
import csv
import io
from typing import Any, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.services.multimodal.limits import (
    MULTIMODAL_MAX_TABLE_COLS,
    MULTIMODAL_MAX_TABLE_ROWS,
)
from backend.app.services.multimodal.schemas import TableArtifact


class TableService:
    """
    Extracts, bounds, and normalizes tabular data from CSV and Excel artifacts.
    Enforces strict column and row caps preventing prompt overflow.
    """

    @classmethod
    def extract_from_csv(
        cls,
        data: bytes,
        max_rows: int = MULTIMODAL_MAX_TABLE_ROWS,
        max_cols: int = MULTIMODAL_MAX_TABLE_COLS,
        sheet_name: Optional[str] = None,
        source_reference: Optional[str] = None,
    ) -> TableArtifact:
        """
        Parses CSV binary data into a normalized TableArtifact.
        """
        text_content = data.decode("utf-8", errors="replace")
        f = io.StringIO(text_content)
        reader = csv.reader(f)

        try:
            raw_headers = next(reader)
        except StopIteration:
            return TableArtifact(
                columns=[],
                rows=[],
                row_count=0,
                column_count=0,
                source_reference=source_reference,
                sheet_name=sheet_name or "Sheet1",
                metadata={"status": "empty"},
            )

        # Truncate columns if needed
        columns = [h.strip() or f"col_{idx}" for idx, h in enumerate(raw_headers[:max_cols])]
        col_count = len(columns)

        rows: List[List[Any]] = []
        total_rows_read = 0

        for row in reader:
            total_rows_read += 1
            if len(rows) < max_rows:
                # Pad or truncate row to match headers
                padded = row[:col_count]
                if len(padded) < col_count:
                    padded.extend([""] * (col_count - len(padded)))
                rows.append(padded)

        meta = {
            "total_rows": total_rows_read,
            "truncated": total_rows_read > max_rows or len(raw_headers) > max_cols,
            "original_col_count": len(raw_headers),
        }

        return TableArtifact(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            column_count=col_count,
            source_reference=source_reference,
            sheet_name=sheet_name or "Sheet1",
            metadata=meta,
        )

    @classmethod
    def extract_from_xlsx(
        cls,
        data: bytes,
        max_rows: int = MULTIMODAL_MAX_TABLE_ROWS,
        max_cols: int = MULTIMODAL_MAX_TABLE_COLS,
        sheet_name: Optional[str] = None,
        source_reference: Optional[str] = None,
    ) -> TableArtifact:
        """
        Parses XLSX data using openpyxl if available, otherwise falls back gracefully.
        """
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            active_sheet = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active

            rows: List[List[Any]] = []
            columns: List[str] = []
            total_rows_read = 0

            for idx, row in enumerate(active_sheet.iter_rows(values_only=True)):
                if idx == 0:
                    raw_cols = [str(c) if c is not None else f"col_{i}" for i, c in enumerate(row[:max_cols])]
                    columns = raw_cols
                else:
                    total_rows_read += 1
                    if len(rows) < max_rows:
                        row_vals = [c if c is not None else "" for c in row[:len(columns)]]
                        if len(row_vals) < len(columns):
                            row_vals.extend([""] * (len(columns) - len(row_vals)))
                        rows.append(row_vals)

            return TableArtifact(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                column_count=len(columns),
                source_reference=source_reference,
                sheet_name=active_sheet.title if active_sheet else "Sheet1",
                metadata={"total_rows": total_rows_read, "engine": "openpyxl"},
            )
        except Exception as e:
            logger.warning(f"[TableService] openpyxl extraction failed or uninstalled: {e}")
            return TableArtifact(
                columns=["status"],
                rows=[[f"XLSX extraction unavailable: {e}"]],
                row_count=1,
                column_count=1,
                source_reference=source_reference,
                sheet_name="Error",
                metadata={"error": str(e)},
            )

    @classmethod
    def generate_schema_summary(cls, table: TableArtifact) -> str:
        """Generates a compact Markdown description of the table schema and statistics."""
        lines = [
            f"Table: {table.sheet_name or 'Default'}",
            f"Rows: {table.row_count} | Columns: {table.column_count}",
            f"Columns: {', '.join(table.columns)}",
        ]
        if table.rows:
            sample_rows = table.rows[:3]
            lines.append("Sample Data (first 3 rows):")
            for r in sample_rows:
                lines.append(f"  - {r}")
        return "\n".join(lines)

    @classmethod
    def format_markdown_table(cls, table: TableArtifact, max_display_rows: int = 20) -> str:
        """Formats the table into a bounded Markdown table for context ingestion."""
        if not table.columns:
            return "*(Empty Table)*"

        header = "| " + " | ".join(str(c) for c in table.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(table.columns)) + " |"
        rows = []
        for r in table.rows[:max_display_rows]:
            row_str = "| " + " | ".join(str(val).replace("\n", " ").replace("|", "\\|") for val in r) + " |"
            rows.append(row_str)

        rendered = "\n".join([header, separator] + rows)
        if table.row_count > max_display_rows:
            rendered += f"\n\n*(Showing {max_display_rows} of {table.row_count} rows)*"
        return rendered
