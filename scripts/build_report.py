from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "6G_Factory_Intelligence_Technical_Report.pdf"


def section(title, body, styles):
    return [Spacer(1, 14), Paragraph(title, styles["Section"]), Spacer(1, 5), Paragraph(body, styles["BodyText"])]


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleBlock", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=30, textColor=colors.HexColor("#14213D"), alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["BodyText"], fontSize=12, leading=17, textColor=colors.HexColor("#52627D"), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=colors.HexColor("#1458D6"), spaceBefore=8, spaceAfter=2))
    styles["BodyText"].fontSize = 10.4
    styles["BodyText"].leading = 15
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=.8*inch, rightMargin=.8*inch, topMargin=.7*inch, bottomMargin=.7*inch, title="6G Factory Intelligence Technical Report", author="Unified Mentor Project")
    story = [Paragraph("6G Factory Intelligence", styles["TitleBlock"]), Paragraph("Technical project report: Impact of network performance on smart-factory efficiency", styles["Subtitle"]), Spacer(1, 24)]
    story += section("Executive summary", "This project turns manufacturing telemetry into a practical dashboard. It helps operations teams see whether network delay and packet loss are associated with lower production speed, higher defects, higher error rates, and maintenance risk. The aim is to support quicker decisions in connected factories that depend on reliable 6G-style communication.", styles)
    story += section("Business problem", "In smart factories, machines exchange control and monitoring data continuously. When the network is slow or unreliable, instructions can arrive late, sensor data can be incomplete, and production loss can be mistaken for a mechanical issue. Managers need one place to compare network health with production and quality outcomes.", styles)
    story += section("Data and method", "The dashboard analyses the supplied Thales Group Manufacturing dataset containing 100,000 observations from 1 January to 10 March 2025. It uses latency, packet loss, machine condition, production speed, defect rate, error rate, and maintenance score. A derived Network Stability Index combines latency and packet loss; a derived Efficiency Index combines network quality, product quality, and maintenance readiness.", styles)
    table_data = [["Dashboard area", "Question answered", "Decision enabled"], ["Network overview", "Is the connection healthy?", "Investigate high latency or packet-loss periods"], ["Efficiency analysis", "Does network performance affect output?", "Prioritize low-latency service for critical lines"], ["Quality and errors", "Which machines are at risk?", "Schedule maintenance and quality checks"], ["6G optimization", "Where is the largest opportunity?", "Allocate network slices and set guardrails"]]
    table = Table(table_data, colWidths=[1.5*inch, 2.2*inch, 2.2*inch], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1458D6")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.6), ("LEADING", (0, 0), (-1, -1), 11), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#D8E0EC")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FC")), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story += [Spacer(1, 15), KeepTogether([Paragraph("Dashboard deliverables", styles["Section"]), Spacer(1, 5), table])]
    story += section("Expected solution", "The application provides date, machine, operation-mode, and latency filters; KPI cards; time trends; correlation views; machine rankings; an optimization panel; and data export. These views make it easier to identify whether production issues align with weak network conditions before they become expensive factory downtime.", styles)
    story += section("Conclusion", "Reliable low-latency communication is a production enabler, not only an IT metric. By connecting network indicators with output and quality, the project gives factory teams an evidence-based way to protect critical operations and improve manufacturing efficiency.", styles)
    story += [Spacer(1, 18), Paragraph("Project artifact - prepared for academic/project submission. This technical report is not presented as a peer-reviewed publication.", ParagraphStyle(name="Footnote", parent=styles["BodyText"], fontSize=8.5, leading=11, textColor=colors.HexColor("#6B7280")))]
    doc.build(story)


if __name__ == "__main__":
    build()
