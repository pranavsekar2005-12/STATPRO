"""Excel and PDF report builders."""

from datetime import datetime
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INDIGO = colors.HexColor("#605BFF")
INK = colors.HexColor("#030229")
MUTED = colors.HexColor("#8A8AA0")
SOFT = colors.HexColor("#F4F4FA")
BORDER = colors.HexColor("#E6E6F0")


def _safe_sheet(name, used):
    base = "".join(ch for ch in name if ch not in '[]:*?/\\')[:31] or "Sheet"
    candidate, i = base, 2
    while candidate in used:
        candidate = f"{base[:28]}_{i}"
        i += 1
    used.add(candidate)
    return candidate


def build_excel(df, overview, results, include_data=True):
    buffer = BytesIO()
    used = set()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(list(overview.items()), columns=["Metric", "Value"]).to_excel(
            writer, sheet_name=_safe_sheet("Overview", used), index=False)
        for res in results.values():
            rows = [{"Metric": k, "Value": v} for k, v in res["summary"].items()]
            if res.get("interpretation"):
                rows.append({"Metric": "Interpretation", "Value": res["interpretation"]})
            pd.DataFrame(rows).to_excel(writer, sheet_name=_safe_sheet(res["title"], used), index=False)
            for tname, table in res["tables"].items():
                table.to_excel(writer, sheet_name=_safe_sheet(f"{res['title'][:18]} - {tname}", used), index=False)
        if include_data:
            df.to_excel(writer, sheet_name=_safe_sheet("Data", used), index=False)
        for ws in writer.book.worksheets:
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 60)
    return buffer.getvalue()


def _fmt_cell(v):
    if isinstance(v, float):
        if v != v:
            return "—"
        return f"{v:,.4f}" if abs(v) < 1e6 else f"{v:.3e}"
    return str(v)


def _table(data, col_widths=None, header=True):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, SOFT]),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), INDIGO), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def _df_table(df, max_rows=40, max_cols=9, width=260 * mm):
    df = df.iloc[:max_rows, :max_cols]
    data = [[str(c) for c in df.columns]] + [[_fmt_cell(v) for v in row] for row in df.itertuples(index=False)]
    return _table(data, col_widths=[width / len(df.columns)] * len(df.columns))


def build_pdf(title, author, notes, overview, results, preview_df=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm, title=title, author=author or "STATPRO")
    ss = getSampleStyleSheet()
    h_title = ParagraphStyle("t", parent=ss["Title"], textColor=INK, fontSize=22, alignment=0, spaceAfter=4)
    h_sub = ParagraphStyle("s", parent=ss["Normal"], textColor=MUTED, fontSize=10, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=INDIGO, fontSize=13, spaceBefore=12, spaceAfter=6)
    h3 = ParagraphStyle("h3", parent=ss["Heading3"], textColor=INK, fontSize=10, spaceBefore=6, spaceAfter=4)
    body = ParagraphStyle("b", parent=ss["Normal"], textColor=INK, fontSize=9.5, leading=13)

    story = [
        Paragraph(title, h_title),
        Paragraph(f"Generated {datetime.now():%d %B %Y, %H:%M}" + (f" · Prepared by {author}" if author else "")
                  + " · STATPRO Statistical Analysis Suite", h_sub),
    ]
    if notes:
        story += [Paragraph("Executive notes", h2), Paragraph(notes.replace("\n", "<br/>"), body)]

    story.append(Paragraph("Dataset overview", h2))
    story.append(_table([["Metric", "Value"]] + [[k, str(v)] for k, v in overview.items()], [80 * mm, 120 * mm]))

    if preview_df is not None and not preview_df.empty:
        story.append(Paragraph("Data preview (first rows)", h3))
        story.append(_df_table(preview_df, max_rows=10))

    for res in results.values():
        story.append(PageBreak() if len(story) > 40 else Spacer(1, 6))
        story.append(Paragraph(f"{res['title']}  <font color='#8A8AA0' size='8'>· {res['category']} · "
                               f"{res['timestamp']}</font>", h2))
        story.append(_table([["Metric", "Value"]] + [[k, v] for k, v in res["summary"].items()],
                            [80 * mm, 120 * mm]))
        if res.get("interpretation"):
            story += [Spacer(1, 4), Paragraph(f"<b>Interpretation:</b> {res['interpretation']}", body)]
        for tname, table in res["tables"].items():
            story.append(Paragraph(tname, h3))
            story.append(_df_table(table))
            if len(table) > 40 or table.shape[1] > 9:
                story.append(Paragraph("<font color='#8A8AA0' size='7'>Table truncated — see the Excel export "
                                       "for the full version.</font>", body))

    def _decorate(canvas, doc_):
        canvas.saveState()
        canvas.setFillColor(INDIGO)
        canvas.rect(0, landscape(A4)[1] - 5, landscape(A4)[0], 5, stroke=0, fill=1)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, 8 * mm, "STATPRO · Statistical Analysis & Reporting")
        canvas.drawRightString(landscape(A4)[0] - 16 * mm, 8 * mm, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_decorate, onLaterPages=_decorate)
    return buffer.getvalue()
