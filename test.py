from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Flowable

# --- Регистрация шрифтов ---
pdfmetrics.registerFont(
    TTFont("Calibri-Italic", r"C:\Users\User\Dev\hr_project\fonts\Calibri\Calibri_italic.ttf")
)
pdfmetrics.registerFont(
    TTFont("Calibri-Bold", r"C:\Users\User\Dev\hr_project\fonts\Calibri\Calibri_bold.ttf")
)

# --- Цвет текста ---
TEXT_COLOR = Color(34 / 255, 84 / 255, 124 / 255)

class Checkbox(Flowable):
    def __init__(self, checked: bool, label: str, size=10, gap=4, style=None):
        super().__init__()
        self.checked = checked
        self.label = label
        self.size = size
        self.gap = gap
        self.style = style or ParagraphStyle(
            name="CheckboxLabel",
            fontName="Calibri-Italic",
            fontSize=11,
            textColor=TEXT_COLOR,
        )
    
    def draw(self):
        self.canv.setStrokeColor(TEXT_COLOR)
        self.canv.setLineWidth(1)
        self.canv.rect(0, -3.3, self.size, self.size, stroke=1, fill=0)

        if self.checked:
            self.canv.setFont("Helvetica-Bold", self.size)
            offset_y = -1  
            self.canv.setFillColor(TEXT_COLOR)
            self.canv.drawString(1, offset_y, "✔")

        # Рисуем текст рядом
        p = Paragraph(self.label, self.style)
        w, h = p.wrapOn(self.canv, 400, self.size)
        p.drawOn(self.canv, self.size + self.gap, -2)


def generate_consent_pdf(output_path: str, organization_name: str, contact_email: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = {
        "title": ParagraphStyle(
            name="Title",
            fontName="Calibri-Bold",
            fontSize=11,
            textColor=TEXT_COLOR,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "text": ParagraphStyle(
            name="Text",
            fontName="Calibri-Italic",
            fontSize=11,
            textColor=TEXT_COLOR,
            leading=15,
            spaceAfter=10,
        ),
    }

    story = []

    story.append(Paragraph("Согласие на обработку персональных данных", styles["title"]))

    story.append(Paragraph(
        f"Поставив галочку в этом поле, я прямо и добровольно даю свое явное согласие "
        f"на сбор и обработку персональных данных, предоставленных в этой форме, "
        f"с целью рассмотрения моей кандидатуры на трудоустройство в <b>{organization_name}</b>.",
        styles["text"]
    ))

    story.append(Paragraph(
        "Предоставленные в форме данные необходимы потенциальному работодателю, "
        "указанному выше, для рассмотрения моей кандидатуры на замещение вакантной должности.",
        styles["text"]
    ))

    story.append(Paragraph(
        "Я подтверждаю, что мои данные будут обрабатываться в соответствии "
        "с действующим законодательством на территории Российской Федерации "
        "о защите персональных данных.",
        styles["text"]
    ))

    story.append(Paragraph(
        f"Я понимаю, что могу отозвать свое согласие в любое время с последующим действием, "
        f"связавшись с нами по адресу: <b>{contact_email}</b>, "
        "без ущерба для законности обработки данных на основании согласия до его отзыва.",
        styles["text"]
    ))

    story.append(Spacer(1, 20))

    story.append(Checkbox(
        checked=True,
        label="Я согласен(на) на обработку персональных данных, как описано выше."
    ))

    doc.build(story)


generate_consent_pdf(
    output_path="consent.pdf",
    organization_name="ООО «Рога и Копыта»",
    contact_email="hr@example.com",
)
