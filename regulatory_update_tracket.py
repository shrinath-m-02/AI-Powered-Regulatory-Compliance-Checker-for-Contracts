#!/usr/bin/env python3
"""
Regulatory Update Tracker (PDF Only + Email Alerts)

✔ Reads contract PDFs
✔ Removes outdated clauses (using remove_keywords)
✔ Inserts updated clause near relevant section
✔ Semantic fallback using BGE-small embeddings
✔ Writes clean updated PDFs
✔ Saves history
✔ Sends email notification
"""

import os
import json
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

# =============================================================================
#                           EMAIL CONFIG
# =============================================================================
SENDER_EMAIL = "example@gmail.com"
APP_PASSWORD = "uzpsiyqinbqaflim"      # <-- replace with your Gmail App Password
RECEIVER_EMAIL = "example@gmail.com"  # can be same or different


def send_email_notification(subject, body, attachment_path=None):
    """Send email using Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

         # If an attachment is included
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                attachment = MIMEText(f.read(), "base64", "utf-8")
                attachment.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(attachment_path)}"'
                )
                attachment.add_header("Content-Transfer-Encoding", "base64")
                msg.attach(attachment)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("📧 Email notification sent.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")


# =============================================================================
#                           DEPENDENCIES
# =============================================================================

try:
    import pypdf
except:
    print("ERROR: Install pypdf → pip install pypdf")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except:
    print("ERROR: Install reportlab → pip install reportlab")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except:
    print("ERROR: Install sentence-transformers + numpy → pip install sentence-transformers numpy")
    sys.exit(1)


# =============================================================================
#                           PATHS
# =============================================================================

DATA_DIR = "data"
CONTRACTS_DIR = os.path.join(DATA_DIR, "contracts")
UPDATED_DIR = os.path.join(DATA_DIR, "updated_contracts")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
REG_FILE = os.path.join(DATA_DIR, "regulations.json")
PREV_REG_FILE = os.path.join(HISTORY_DIR, "prev_regulations.json")

os.makedirs(CONTRACTS_DIR, exist_ok=True)
os.makedirs(UPDATED_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)


# =============================================================================
#                           LOADERS
# =============================================================================

def load_regulations():
    with open(REG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prev_regulations():
    if not os.path.exists(PREV_REG_FILE):
        return []
    with open(PREV_REG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prev_regulations(regs):
    with open(PREV_REG_FILE, "w", encoding="utf-8") as f:
        json.dump(regs, f, indent=2)


# =============================================================================
#                           PDF READING
# =============================================================================

def read_pdf(path):
    reader = pypdf.PdfReader(path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)


# =============================================================================
#                           PDF WRITING
# =============================================================================

def save_text_as_pdf(text, out_path):
    c = canvas.Canvas(out_path, pagesize=letter)
    width, height = letter
    margin = 50
    x = margin
    y = height - margin
    lh = 12

    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for w in words:
            if len(line + " " + w) > 110:
                c.drawString(x, y, line)
                y -= lh
                line = w
                if y < margin:
                    c.showPage()
                    y = height - margin
            else:
                line = (line + " " + w).strip()
        c.drawString(x, y, line)
        y -= lh
    c.save()


# =============================================================================
#                           RISK DETECTION
# =============================================================================

def check_risks(contract_text, regulations):
    missing = []
    lower = contract_text.lower()

    for reg in regulations:
        clause = reg.get("required_clause", "").lower()
        if clause in lower:
            continue

        missing.append(reg)

    return missing


# =============================================================================
#                           CHANGE DETECTION
# =============================================================================

def detect_regulation_changes(prev, curr):
    prev_map = {r["id"]: r for r in prev}
    changes = []

    for reg in curr:
        old = prev_map.get(reg["id"], {}).get("required_clause", "")
        new = reg.get("required_clause", "")

        if old.strip() != new.strip():
            changes.append(reg)

    return changes


# =============================================================================
#                           EMBEDDINGS
# =============================================================================

EMBED_MODEL = None


def get_model():
    global EMBED_MODEL
    if EMBED_MODEL is None:
        print("Loading embedding model BAAI/bge-small-en …")
        EMBED_MODEL = SentenceTransformer("BAAI/bge-small-en")
    return EMBED_MODEL


def embed(texts):
    model = get_model()
    return model.encode(texts, convert_to_numpy=True)


def cosine(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def best_semantic_index(paragraphs, clause):
    em_paras = embed(paragraphs)
    em_clause = embed([clause])[0]

    sims = [cosine(p, em_clause) for p in em_paras]
    return int(np.argmax(sims))

# =============================================================================
#                           AMENDMENT ENGINE
# =============================================================================

def apply_amendment(contract_file, reg_changes):
    path = os.path.join(CONTRACTS_DIR, contract_file)
    original = read_pdf(path)

    paragraphs = [p.strip() for p in original.split("\n\n") if p.strip()]
    low = [p.lower() for p in paragraphs]

    updated = False
    actions = []

    # ----------- REMOVE OLD CONTENT -----------
    for reg in reg_changes:
        for kw in reg.get("remove_keywords", []):
            new_list = []
            removed = False
            for p, lp in zip(paragraphs, low):
                if kw.lower() in lp:
                    removed = True
                    updated = True
                    continue
                new_list.append(p)
            if removed:
                actions.append(f"Removed outdated clause related to '{reg['title']}'")
            paragraphs = new_list
            low = [p.lower() for p in paragraphs]

    # ----------- INSERT NEW UPDATED CLAUSE -----------
    for reg in reg_changes:
        clause = reg.get("required_clause", "").strip()

        # If clause already exists, skip
        if clause.lower() in "\n".join(paragraphs).lower():
            continue

        ins_index = -1

        # Keyword-based insertion (first priority)
        for kw in reg.get("keywords", []):
            for idx, lp in enumerate(low):
                if kw.lower() in lp:
                    ins_index = idx
                    break
            if ins_index != -1:
                break

        # Semantic fallback (second priority)
        if ins_index == -1:
            ins_index = best_semantic_index(paragraphs, clause)

        # Place below the matched paragraph
        paragraphs.insert(ins_index + 1, clause)
        low.insert(ins_index + 1, clause.lower())

        updated = True
        actions.append(f"Inserted updated clause for '{reg['title']}'")

    if not updated:
        return None, []

    new_text = "\n\n".join(paragraphs)

    # ----------- SAVE UPDATED PDF -----------
    timestamp = int(time.time())
    base = os.path.splitext(contract_file)[0]
    new_pdf = f"{base}_v{timestamp}.pdf"
    out_path = os.path.join(UPDATED_DIR, new_pdf)

    save_text_as_pdf(new_text, out_path)

    # ----------- SAVE HISTORY -----------
    hist = {
        "timestamp": datetime.utcnow().isoformat(),
        "original": contract_file,
        "updated": new_pdf,
        "actions": actions
    }

    with open(os.path.join(HISTORY_DIR, f"{base}_history.json"), "a", encoding="utf-8") as f:
        f.write(json.dumps(hist) + "\n")

    # ----------- EMAIL WITH ATTACHED PDF -----------
    subject = f"Contract Updated: {new_pdf}"
    body = "Contract updated with the following changes:\n\n" + "\n".join(f"- {a}" for a in actions)

    # FIXED: Passed correct path (out_path instead of new_pdf_path)
    send_email_notification(subject, body, attachment_path=out_path)

    return new_pdf, actions


# =============================================================================
#                           MENU
# =============================================================================

def menu():

    while True:
        print("\n=========== Regulatory Update Tracker ===========")
        print("1. Show regulations")
        print("2. Show contract PDFs")
        print("3. Check risk")
        print("4. Apply amendments")
        print("5. Exit")

        ch = input("Select: ").strip()

        regs = load_regulations()
        prev = load_prev_regulations()
        pdfs = [f for f in os.listdir(CONTRACTS_DIR) if f.lower().endswith(".pdf")]

        if ch == "1":
            for r in regs:
                print(f"- {r['title']}: {r['required_clause'][:100]}...")

        elif ch == "2":
            for p in pdfs:
                print("•", p)

        elif ch == "3":
            for p in pdfs:
                text = read_pdf(os.path.join(CONTRACTS_DIR, p))
                issues = check_risks(text, regs)
                print(f"\n📌 {p}")
                if issues:
                    print("Missing:")
                    for i in issues:
                        print("-", i["required_clause"])
                else:
                    print("✔ Fully compliant")

        elif ch == "4":
            changes = detect_regulation_changes(prev, regs)
            if not changes:
                # treat missing clauses as changes
                for p in pdfs:
                    txt = read_pdf(os.path.join(CONTRACTS_DIR, p))
                    issues = check_risks(txt, regs)
                    newfile, actions = apply_amendment(p, issues)
                    if newfile:
                        print("Updated:", newfile)
                save_prev_regulations(regs)
            else:
                for p in pdfs:
                    newfile, actions = apply_amendment(p, changes)
                    if newfile:
                        print("Updated:", newfile)
                save_prev_regulations(regs)

        elif ch == "5":
            break

        else:
            print("Invalid choice!")


# =============================================================================
#                           RUN
# =============================================================================

if __name__ == "__main__":
    menu()
