
import io
import streamlit as st
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="PDF op briefpapier", page_icon="🧾", layout="centered")
st.title("🧾 PDF op briefpapier")

st.markdown("""
Upload hieronder **je factuur als PDF** en **je briefpapier (PDF)**.  
De app zet je factuur **bovenop** je briefpapier (per pagina) en geeft één samengevoegde PDF terug.
""")

invoice_file = st.file_uploader("Factuur (PDF)", type=["pdf"], key="invoice")
letterhead_file = st.file_uploader("Briefpapier (PDF)", type=["pdf"], key="letterhead")

def merge_invoice_with_letterhead(invoice_bytes: bytes, letterhead_bytes: bytes) -> bytes:
    inv = PdfReader(io.BytesIO(invoice_bytes))
    lh = PdfReader(io.BytesIO(letterhead_bytes))
    out = PdfWriter()

    if len(inv.pages) == 0:
        raise ValueError("Factuur-PDF bevat geen pagina's.")
    if len(lh.pages) == 0:
        return invoice_bytes  # geen briefpapier? geef factuur terug

    for i, inv_page in enumerate(inv.pages):
        base = lh.pages[min(i, len(lh.pages)-1)]
        # Leg factuur bovenop het briefpapier
        base.merge_page(inv_page)
        out.add_page(base)

    buf = io.BytesIO()
    out.write(buf)
    return buf.getvalue()

if invoice_file and letterhead_file:
    try:
        merged = merge_invoice_with_letterhead(invoice_file.read(), letterhead_file.read())
        st.success("Samengevoegde PDF is klaar.")
        st.download_button("Download samengevoegde PDF", merged, file_name="factuur_op_briefpapier.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Er ging iets mis: {e}")
else:
    st.info("Upload beide bestanden om te starten.")
