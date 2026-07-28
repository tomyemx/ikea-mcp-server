import markdown
from xhtml2pdf import pisa
import os

# Configuration
input_file = r"C:\Users\tomye\.gemini\antigravity\brain\f85bd67d-a925-4f31-b079-19ebe9cd3a35\bedroom_design_proposal.md"
output_file = r"C:\Users\tomye\.gemini\antigravity\brain\f85bd67d-a925-4f31-b079-19ebe9cd3a35\bedroom_design_proposal.pdf"

# Custom CSS for the PDF
pdf_css = """
<style>
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: Helvetica, sans-serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #333;
    }
    h1 {
        color: #0058a3; /* IKEA Blue-ish */
        font-size: 24pt;
        border-bottom: 2px solid #ffdb00; /* IKEA Yellowish */
        padding-bottom: 10px;
        margin-top: 20px;
    }
    h2 {
        color: #0058a3;
        font-size: 18pt;
        margin-top: 20px;
        border-bottom: 1px solid #ccc;
    }
    h3 {
        color: #444;
        font-size: 14pt;
        margin-top: 15px;
    }
    img {
        max-width: 100%;
        height: auto;
        margin: 10px 0;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    a {
        color: #0058a3;
        text-decoration: none;
    }
</style>
"""

def convert_md_to_pdf(source_md, output_pdf):
    # 1. Read Markdown
    with open(source_md, "r", encoding="utf-8") as f:
        text = f.read()

    # 2. Convert to HTML
    html_content = markdown.markdown(text, extensions=['tables'])

    # 3. Combine with CSS
    final_html = f"""
    <html>
    <head>{pdf_css}</head>
    <body>
    {html_content}
    </body>
    </html>
    """

    # 4. Generate PDF
    with open(output_pdf, "wb") as f:
        pisa_status = pisa.CreatePDF(final_html, dest=f)

    if pisa_status.err:
        print(f"Error converting to PDF: {pisa_status.err}")
    else:
        print(f"Successfully created PDF at: {output_pdf}")

if __name__ == "__main__":
    if os.path.exists(input_file):
        convert_md_to_pdf(input_file, output_file)
    else:
        print(f"Input file not found: {input_file}")
