import io
import os
import platform
import tempfile
import zipfile

from openpyxl.cell.cell import MergedCell
from openpyxl.styles import Alignment
from copy import copy
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage

from django.conf import settings
from docxtpl import DocxTemplate

RU_MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

EN_MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

FR_MONTHS = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre",
}


class DocumentService:
    path = str(settings.BASE_DIR) + os.sep

    def get_doc_pdf(self, context: dict, docx_temp: DocxTemplate):
        file_name = "temporary_file"
        pdf_bytes = io.BytesIO()
        docx_temp.render(context)
        docs_dir = tempfile.TemporaryDirectory(prefix=self.path)
        docx_temp.save(os.path.join(docs_dir.name, f"{file_name}.docx"))
        file_path = os.path.join(docs_dir.name, f"{file_name}.docx")
        output_dir = os.path.join(docs_dir.name)
        if platform.system().lower() == "windows":
            os.system(
                f"C:\Program^ Files\LibreOffice\program\soffice --headless --convert-to pdf --outdir {output_dir} {file_path}"
            )
        elif platform.system().lower() == "linux":
            os.system(
                f"soffice --headless --convert-to pdf --outdir {output_dir} {file_path}"
            )
        with open(
            os.path.join(docs_dir.name, f"{file_name}.pdf"), "rb"
        ) as pdf:
            pdf_bytes = io.BytesIO(pdf.read())
        return pdf_bytes

    def get_bytes_stream(self, relative_path: str):
        with open(relative_path, "rb") as file:
            file_bytes = io.BytesIO(file.read())
        return file_bytes


def write_cell(ws, row: int, col: int, value: str):
    cell = ws.cell(row=row, column=col)

    if isinstance(cell, MergedCell):
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                ws.cell(
                    row=merged_range.min_row,
                    column=merged_range.min_col
                ).value = value
                return

    cell.value = value
    
def split_text(text: str, max_len: int, max_lines: int):
    """
    Делит текст на max_lines строк, каждая не длиннее max_len,
    при этом слова не разрываются. Если слово не помещается, оно переносится на следующую строку.
    """
    if not text:
        return []

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if current_line:
            # если текущее слово влезает с пробелом
            if len(current_line) + 1 + len(word) <= max_len:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        else:
            # первая строка
            if len(word) <= max_len:
                current_line = word
            else:
                # слово длиннее max_len, режем его
                while len(word) > max_len:
                    lines.append(word[:max_len])
                    word = word[max_len:]
                current_line = word

        if len(lines) == max_lines:
            break

    if current_line and len(lines) < max_lines:
        lines.append(current_line)

    return lines[:max_lines]


def write_merged_cell(ws, row: int, start_col: int, value: str, merge_cols: int = 1):
    if merge_cols > 1:
        end_col = start_col + merge_cols - 1
        ws.merge_cells(
            start_row=row,
            start_column=start_col,
            end_row=row,
            end_column=end_col
        )
    ws.cell(row=row, column=start_col).value = value
    
    
def insert_education_row(ws, row):
    """
    Вставляет пустую строку для образования на позицию row,
    копирует стиль предыдущей строки и объединяет ячейки
    """
    # Сохраняем merge диапазоны
    merges = list(ws.merged_cells.ranges)

    # Вставляем пустую строку
    ws.insert_rows(row)

    # Сдвигаем merge диапазоны вниз
    ws.merged_cells.ranges = []
    for m in merges:
        min_col, min_row, max_col, max_row = m.bounds
        if min_row >= row:
            m.shift(0, 1)
        ws.merged_cells.add(m)

    # Копируем стиль с предыдущей строки
    for col in range(1, ws.max_column + 1):
        source = ws.cell(row=row-1, column=col)
        target = ws.cell(row=row, column=col)
        if source.has_style:
            target.font = copy(source.font)
            target.border = copy(source.border)
            target.fill = copy(source.fill)
            target.number_format = copy(source.number_format)
            target.alignment = copy(source.alignment)
            target.protection = copy(source.protection)

    # Объединяем ячейки под образование
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)  # A-E
    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=7)  # F-G
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=9)  # H-I
    ws.merge_cells(start_row=row, start_column=10, end_row=row, end_column=12)  # J-L
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)  # M-N

    return row 


def insert_employment_row(ws, row: int):
    """
    Вставляет строку для трудовой деятельности на позицию row.
    Копирует стиль предыдущей строки и объединяет ячейки под колонки таблицы.
    Таблица трудовой деятельности:
    Дата приема A
    Дата увольнения B-D
    Должность, наименование организации E-G
    Адрес, телефон организации H-I
    ФИО руководителя J-L
    Причина увольнения M-N
    """
    # Сохраняем merge диапазоны
    merges = list(ws.merged_cells.ranges)

    # Вставляем пустую строку
    ws.insert_rows(row)

    # Сдвигаем merge диапазоны вниз
    ws.merged_cells.ranges = []
    for m in merges:
        min_col, min_row, max_col, max_row = m.bounds
        if min_row >= row:
            m.shift(0, 1)
        ws.merged_cells.add(m)

    # Копируем стиль с предыдущей строки
    for col in range(1, ws.max_column + 1):
        source = ws.cell(row=row-1, column=col)
        target = ws.cell(row=row, column=col)
        if source.has_style:
            target.font = copy(source.font)
            target.border = copy(source.border)
            target.fill = copy(source.fill)
            target.number_format = copy(source.number_format)
            target.alignment = copy(source.alignment)
            target.protection = copy(source.protection)

    # Объединяем ячейки под колонки таблицы трудовой деятельности
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)   # Дата увольнения
    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)   # Должность, организация
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=9)   # Адрес, телефон организации
    ws.merge_cells(start_row=row, start_column=10, end_row=row, end_column=12) # ФИО руководителя
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14) # Причина увольнения
    
    
def insert_recommendation_row(ws, row: int):
    """
    Вставляет строку для рекомендации на позицию row.
    Копирует стиль предыдущей строки и объединяет ячейки под всю таблицу рекомендаций (A-N)
    """
    from copy import copy

    # Сохраняем merge диапазоны
    merges = list(ws.merged_cells.ranges)

    # Вставляем пустую строку
    ws.insert_rows(row)

    # Сдвигаем merge диапазоны вниз
    ws.merged_cells.ranges = []
    for m in merges:
        min_col, min_row, max_col, max_row = m.bounds
        if min_row >= row:
            m.shift(0, 1)
        ws.merged_cells.add(m)

    # Копируем стиль с предыдущей строки
    for col in range(1, ws.max_column + 1):
        source = ws.cell(row=row-1, column=col)
        target = ws.cell(row=row, column=col)
        if source.has_style:
            target.font = copy(source.font)
            target.border = copy(source.border)
            target.fill = copy(source.fill)
            target.number_format = copy(source.number_format)
            target.alignment = copy(source.alignment)
            target.protection = copy(source.protection)

    # Объединяем ячейки под всю таблицу рекомендаций A-N
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=14)


def write_recommendation_cell(ws, row: int, text: str, max_chars_per_line=75, line_height=11):
    """
    Записывает текст рекомендации в объединённую строку A-N,
    включает перенос текста и динамически подстраивает высоту строки.
    """
    # Объединяем ячейки A-N
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=14)

    cell = ws.cell(row=row, column=1)
    cell.value = text
    cell.alignment = Alignment(wrapText=True, vertical="top")

    # Оценка количества строк текста
    lines_count = sum((len(line) - 1) // max_chars_per_line + 1 for line in text.split("\n"))

    # Устанавливаем высоту строки
    ws.row_dimensions[row].height = max(line_height, lines_count * line_height)
    
    
def insert_family_row(ws, row: int):
    """
    Вставляет строку для таблицы «Состав семьи».
    Копирует стиль предыдущей строки и объединяет ячейки по шаблону:
    A-C | D-F | G-J | K-N
    """
    from copy import copy

    # Сохраняем merge диапазоны
    merges = list(ws.merged_cells.ranges)

    # Вставляем строку
    ws.insert_rows(row)

    # Корректно сдвигаем merge диапазоны
    ws.merged_cells.ranges = []
    for m in merges:
        min_col, min_row, max_col, max_row = m.bounds
        if min_row >= row:
            m.shift(0, 1)
        ws.merged_cells.add(m)

    # Копируем стиль с предыдущей строки
    for col in range(1, ws.max_column + 1):
        source = ws.cell(row=row - 1, column=col)
        target = ws.cell(row=row, column=col)
        if source.has_style:
            target.font = copy(source.font)
            target.border = copy(source.border)
            target.fill = copy(source.fill)
            target.number_format = copy(source.number_format)
            target.alignment = copy(source.alignment)
            target.protection = copy(source.protection)

    # Объединения ячеек по шаблону таблицы семьи
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)    # A–C Степень родства
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)    # D–F Год рождения
    ws.merge_cells(start_row=row, start_column=7, end_row=row, end_column=10)   # G–J Род деятельности
    ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=14)  # K–N Место проживания


def find_row_by_text(ws, needle: str) -> int | None:
    needle = needle.lower().strip()

    for i, row in enumerate(ws.iter_rows(), start=1):
        for cell in row:
            if cell.value:
                text = str(cell.value).lower().replace("\n", " ")
                if needle in text:
                    return i
    return None


def write_answer_block(
    ws,
    question_text: str,
    value: str,
    max_lines: int,
    max_len: int = 100,
    start_col: int = 1
):
    if not value:
        return

    question_row = find_row_by_text(ws, question_text)
    if not question_row:
        return

    start_row = question_row + 1
    lines = split_text(value, max_len=max_len, max_lines=max_lines)

    # фиксируем высоту строк из шаблона
    heights = [
        ws.row_dimensions[start_row + i].height
        for i in range(max_lines)
    ]

    for i in range(max_lines):
        if i < len(lines):
            write_cell(ws, start_row + i, start_col, lines[i])
        ws.row_dimensions[start_row + i].height = heights[i]


def write_created_at(ws, candidate):
    """
    Ищет строку с кавычками в ячейке A (игнорируем пробелы) 
    и заполняет день, месяц и год.
    """
    target_row = None
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if row and row[0]:
            cell_val = str(row[0]).replace(" ", "")
            if cell_val.count('"') == 2:
                target_row = i
                break

    if not target_row or not candidate.created_at:
        return

    day = candidate.created_at.day
    month_num = candidate.created_at.month
    year = candidate.created_at.year

    # Месяц на русском
    month_name = RU_MONTHS[month_num]

    # Записываем
    ws.cell(row=target_row, column=1).value = f'"{day}"'
    ws.merge_cells(start_row=target_row, start_column=2, end_row=target_row, end_column=5)
    ws.cell(row=target_row, column=2).value = month_name
    ws.merge_cells(start_row=target_row, start_column=6, end_row=target_row, end_column=7)
    ws.cell(row=target_row, column=6).value = str(year)
    if candidate.signature:
        insert_signature(ws, candidate.signature.path, target_row)
    
    
def insert_signature(ws, signature_path: str, row: int, target_width: int = 100):
    """
    Вставляет подпись в указанную строку в диапазон K-N,
    масштабируя пропорционально по ширине.
    """
    # Читаем оригинальное изображение, чтобы знать его размеры
    with PILImage.open(signature_path) as pil_img:
        orig_width, orig_height = pil_img.size

    # Вычисляем коэффициент масштабирования
    scale = target_width / orig_width
    target_height = int(orig_height * scale)

    # Создаём объект openpyxl Image
    img = XLImage(signature_path)
    img.width = target_width
    img.height = target_height

    # Вставляем в ячейку K{row}
    cell_address = f'K{row}'
    ws.add_image(img, cell_address)
    

def insert_candidate_photo(ws, photo_path: str, start_row: int = 2, end_row: int = 9, start_col: int = 12, end_col: int = 14):
    """
    Вставляет фото кандидата в указанный диапазон (по умолчанию L2:N9),
    масштабируя пропорционально по ширине.
    """
    # Читаем оригинальное изображение
    with PILImage.open(photo_path) as pil_img:
        orig_width, orig_height = pil_img.size

    # Рассчитываем ширину диапазона в пикселях (приблизительно, 1 столбец ≈ 64px)
    target_width = (end_col - start_col + 1) * 40
    scale = target_width / orig_width
    target_height = int(orig_height * scale)

    # Создаём объект openpyxl Image
    img = XLImage(photo_path)
    img.width = target_width
    img.height = target_height

    # Вставляем в верхний левый угол диапазона
    cell_address = f"{chr(64 + start_col)}{start_row}"  # столбец в букве
    ws.add_image(img, cell_address)
