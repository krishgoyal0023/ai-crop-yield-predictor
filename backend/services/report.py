from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def build_field_report(payload: dict) -> BytesIO:
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=36,bottomMargin=36)
    styles=getSampleStyleSheet()
    story=[Paragraph("AI Crop Yield Predictor — Field Assessment",styles["Title"]),
           Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",styles["Normal"]),Spacer(1,12)]
    loc=payload.get("location",{})
    story.append(Paragraph(f"Location: {loc.get('latitude','—')}, {loc.get('longitude','—')} | District: {payload.get('district','—')}",styles["Normal"]))
    story.append(Paragraph(f"Crop: {payload.get('crop','—')} | Area: {payload.get('area_ha','—')} ha",styles["Normal"]))
    pred=payload.get("prediction",{})
    story.append(Spacer(1,12))
    story.append(Paragraph("Yield",styles["Heading2"]))
    story.append(Paragraph(f"Predicted yield: {pred.get('predicted_yield','—')} {pred.get('unit','tonnes_per_hectare')}",styles["Normal"]))
    story.append(Paragraph(f"Reliability: {pred.get('reliability','—')}",styles["Normal"]))
    for title,key in [("Fertilizer","fertilizer"),("Irrigation","irrigation"),("Disease Risk","disease"),("Economics","economics"),("Crop Rotation","rotation")]:
        story.append(Spacer(1,10)); story.append(Paragraph(title,styles["Heading2"]))
        value=payload.get(key,{})
        text=str(value)[:2500].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        story.append(Paragraph(text,styles["BodyText"]))
    story.append(Spacer(1,12))
    story.append(Paragraph("Important: This is decision-support output, not a certified agronomic, financial, subsidy, loan or crop-insurance assessment. Verify recommendations with current local extension/PAU guidance and field observations.",styles["BodyText"]))
    doc.build(story)
    buf.seek(0)
    return buf
