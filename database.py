from langchain_community.document_loaders import WebBaseLoader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def scrape_webpages():
    urls = [
        "https://www.hrlineup.com/legal-and-compliance-checklist-for-hiring/",
        "https://www.businessnewsdaily.com/15985-small-business-hr-compliance.html",
        "https://www.aihr.com/blog/hr-compliance-checklist/",
        "https://qualitybsolutions.net/hr-compliance-checklist/",
        "https://rminc.com/insights/hr-compliance-checklist/"
    ]
    loader = WebBaseLoader(urls)
    docs = loader.load()
    combined_text = "\n\n".join([doc.page_content for doc in docs])
    return combined_text


def save_to_pdf(text, filename="scraped_data.pdf"):
    pdf = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    text_object = pdf.beginText(50, height - 50)
    text_object.setFont("Times-Roman", 10)

    for line in text.split("\n"):
        text_object.textLine(line)
        if text_object.getY() < 50:  # New page if space runs out
            pdf.drawText(text_object)
            pdf.showPage()
            text_object = pdf.beginText(50, height - 50)
            text_object.setFont("Times-Roman", 10)

    pdf.drawText(text_object)
    pdf.save()
    print(f"✅ PDF saved successfully as '{filename}'")


if __name__ == "__main__":
    print("🔍 Scraping compliance webpages...")
    text_data = scrape_webpages()
    print("📄 Saving scraped content into PDF...")
    save_to_pdf(text_data)
    print("✅ All done! PDF created with compliance information.")
