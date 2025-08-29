
import io
import streamlit as st
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Invoice-to-PDF", page_icon="🧾", layout="centered")

st.title("🧾 Invoice → PDF (met briefpapier)")

st.markdown("""
Upload hieronder je **factuur Excel** (volgens de meegeleverde template) en optioneel je **briefpapier (PDF)**.
De app genereert een nette **PDF-factuur** en voegt indien gewenst elke pagina samen met je briefpapier.
""")

# --- Helpers ---
def load_invoice_from_excel(file) -> dict:
    """Expect a workbook with two sheets:
    1) 'meta' with two columns: key | value (e.g. 'invoice_number', 'client_name', etc.)
    2) 'items' with columns: description | qty | unit_price | vat_pct
    """
    xls = pd.ExcelFile(file)
    required_sheets = {"meta", "items"}
    if not required_sheets.issubset(set(xls.sheet_names)):
        raise ValueError("Excel mist verplichte sheets: 'meta' en/of 'items'.")

    meta_df = pd.read_excel(xls, "meta")
    items_df = pd.read_excel(xls, "items")

    # Normalize columns
    meta_df.columns = [c.strip().lower() for c in meta_df.columns]
    items_df.columns = [c.strip().lower() for c in items_df.columns]

    if not set(meta_df.columns) >= {"key", "value"}:
        raise ValueError("Sheet 'meta' moet kolommen hebben: key, value.")
    if not set(items_df.columns) >= {"description", "qty", "unit_price", "vat_pct"}:
        raise ValueError("Sheet 'items' moet kolommen hebben: description, qty, unit_price, vat_pct.")

    meta = {str(k): str(v) for k, v in zip(meta_df["key"], meta_df["value"])}

    # Coerce numeric
    items_df["qty"] = pd.to_numeric(items_df["qty"], errors="coerce").fillna(0)
    items_df["unit_price"] = pd.to_numeric(items_df["unit_price"], errors="coerce").fillna(0.0)
    items_df["vat_pct"] = pd.to_numeric(items_df["vat_pct"], errors="coerce").fillna(0.0)
    items_df["line_total_excl"] = items_df["qty"] * items_df["unit_price"]
    items_df["vat_amount"] = items_df["line_total_excl"] * (items_df["vat_pct"] / 100.0)
    items_df["line_total_incl"] = items_df["line_total_excl"] + items_df["vat_amount"]

    totals = {
        "subtotal_excl": float(items_df["line_total_excl"].sum()),
        "total_vat": float(items_df["vat_amount"].sum()),
        "grand_total": float(items_df["line_total_incl"].sum()),
    }

    return {"meta": meta, "items": items_df, "totals": totals}

def euro(n: float) -> str:
    return f"€ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def build_invoice_pdf(meta: dict, items_df: pd.DataFrame, totals: dict) -> bytes:
    """Render a clean invoice PDF. Returns raw PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=22*mm, bottomMargin=22*mm)
    story = []
    styles = getSampleStyleSheet()
    H1 = styles["Heading1"]
    H2 = styles["Heading2"]
    N = styles["Normal"]

    # Header block
    supplier_name = meta.get("supplier_name", "Bedrijfsnaam BV")
    supplier_address = meta.get("supplier_address", "Straat 1\\n1234 AB Plaats")
    supplier_kvk = meta.get("supplier_kvk", "KVK 00000000")
    supplier_vat = meta.get("supplier_vat", "NL000000000B01")
    invoice_number = meta.get("invoice_number", "2025-0001")
    invoice_date = meta.get("invoice_date", str(date.today()))
    due_date = meta.get("due_date", "")

    client_name = meta.get("client_name", "Klantnaam")
    client_address = meta.get("client_address", "Klantstraat 1\\n9999 ZZ Klantplaats")

    story.append(Paragraph(supplier_name, H1))
    story.append(Paragraph(supplier_address.replace("\\\\n", "\\n"), N))
    story.append(Paragraph(f"{supplier_kvk} • {supplier_vat}", N))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Factuur <b>{invoice_number}</b>", H2))
    story.append(Paragraph(f"Factuurdatum: {invoice_date}", N))
    if due_date:
        story.append(Paragraph(f"Vervaldatum: {due_date}", N))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Factuur aan</b>", N))
    story.append(Paragraph(client_name, N))
    story.append(Paragraph(client_address.replace('\\\\n', '\\n'), N))
    story.append(Spacer(1, 12))

    # Items table
    table_data = [["Omschrijving", "Aantal", "Stukprijs", "BTW %", "Totaal ex."]]
    for _, r in items_df.iterrows():
        table_data.append([
            str(r["description"]),
            f"{r['qty']:.2f}".rstrip("0").rstrip("."),
            euro(float(r["unit_price"])),
            f"{float(r['vat_pct']):.0f}%",
            euro(float(r["line_total_excl"])),
        ])
    tbl = Table(table_data, colWidths=[None, 25*mm, 30*mm, 20*mm, 35*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F0F0F0")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("ALIGN", (0,0), (0,-1), "LEFT"),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#DDDDDD")),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    # Totals
    totals_data = [
        ["Subtotaal (excl. btw):", euro(totals["subtotal_excl"])],
        ["Totaal btw:", euro(totals["total_vat"])],
        ["Te betalen:", f"<b>{euro(totals['grand_total'])}</b>"],
    ]
    t2 = Table(totals_data, colWidths=[90*mm, 35*mm], hAlign="RIGHT")
    t2.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,-1), "RIGHT"),
        ("FONT", (0,0), (0,-1), "Helvetica"),
        ("FONT", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t2)

    # Payment note
    note = meta.get("payment_note", "Graag binnen 14 dagen betalen o.v.v. factuurnummer.")
    story.append(Spacer(1, 12))
    story.append(Paragraph(note, N))

    doc.build(story)
    return buf.getvalue()

def merge_with_letterhead(invoice_pdf_bytes: bytes, letterhead_pdf_bytes: bytes) -> bytes:
    inv_reader = PdfReader(io.BytesIO(invoice_pdf_bytes))
    letter_reader = PdfReader(io.BytesIO(letterhead_pdf_bytes))
    writer = PdfWriter()

    # If letterhead has zero pages (unlikely), just return invoice
    if len(letter_reader.pages) == 0:
        return invoice_pdf_bytes

    for i, page in enumerate(inv_reader.pages):
        base = letter_reader.pages[min(i, len(letter_reader.pages)-1)]
        base.merge_page(page)
        writer.add_page(base)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

excel_file = st.file_uploader("Upload factuur Excel (template)", type=["xlsx"], key="xlsx")
letterhead_file = st.file_uploader("Upload briefpapier (PDF, optioneel)", type=["pdf"], key="pdf")

if excel_file is not None:
    try:
        parsed = load_invoice_from_excel(excel_file)
        meta = parsed["meta"]
        items = parsed["items"]
        totals = parsed["totals"]

        st.subheader("Gegevens")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Verkoper**")
            st.write(meta.get("supplier_name", "—"))
            st.write(meta.get("supplier_address", "—"))
            st.write(meta.get("supplier_kvk", "—"), "•", meta.get("supplier_vat", "—"))
        with col2:
            st.write("**Klant**")
            st.write(meta.get("client_name", "—"))
            st.write(meta.get("client_address", "—"))

        st.subheader("Regels")
        show_df = items[["description", "qty", "unit_price", "vat_pct", "line_total_excl"]].copy()
        st.dataframe(show_df, use_container_width=True)

        st.subheader("Totaal")
        st.write(f"Subtotaal: **{totals['subtotal_excl']:.2f}**")
        st.write(f"BTW: **{totals['total_vat']:.2f}**")
        st.write(f"Te betalen: **{totals['grand_total']:.2f}**")

        pdf_bytes = build_invoice_pdf(meta, items, totals)
        if letterhead_file is not None:
            merged = merge_with_letterhead(pdf_bytes, letterhead_file.read())
            st.success("PDF gegenereerd en samengevoegd met briefpapier.")
            st.download_button("Download PDF met briefpapier", merged, file_name=f"factuur_{meta.get('invoice_number','')}.pdf", mime="application/pdf")
        else:
            st.success("PDF gegenereerd.")
            st.download_button("Download PDF", pdf_bytes, file_name=f"factuur_{meta.get('invoice_number','')}.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Er ging iets mis: {e}")

st.divider()
with st.expander("📄 Excel-template & tips"):
    st.markdown(\"\"\"
**Template-indeling**  
- **Sheet `meta`** met kolommen: `key`, `value`  
  Voorbeelden van keys:  
  - `supplier_name`, `supplier_address`, `supplier_kvk`, `supplier_vat`  
  - `invoice_number`, `invoice_date`, `due_date`  
  - `client_name`, `client_address`  
  - `payment_note`

- **Sheet `items`** met kolommen:  
  `description` | `qty` | `unit_price` | `vat_pct`

**BTW** vul per regel het btw-percentage in (bijv. 21 of 9).  
**Adresregels** kun je scheiden met een '\\\\n' in Excel.
\"\"\")
