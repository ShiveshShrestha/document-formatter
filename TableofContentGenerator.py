import json
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

baseDir = os.path.dirname(os.path.abspath(__file__))


def font_paths(font_family):
    if str(font_family).lower() == "arial":
        regular_name, bold_name = "arial.ttf", "arialbd.ttf"
    else:
        regular_name, bold_name = "times.ttf", "timesbd.ttf"

    regular_path = os.path.join(baseDir, "Fonts", regular_name)
    bold_path = os.path.join(baseDir, "Fonts", bold_name)
    missing = [name for name, path in ((regular_name, regular_path), (bold_name, bold_path)) if not os.path.isfile(path)]
    if missing:
        raise FileNotFoundError(
            "Missing font file(s): " + ", ".join(missing) + ". Place them in the Fonts folder."
        )
    return regular_path, bold_path


class TOC:
    @staticmethod
    def generate_toc():
        a4_width = 1654
        a4_height = 2339
        margin = 120
        top = 260
        max_bottom = a4_height - 200
        lab_number_column = margin
        lab_name_column = 360
        date_column = 1080
        signature_column = 1280
        column_end = a4_width - margin
        header_height = 90
        minimum_row_height = 90
        gap = 30
        border_width = 4

        toc_output_dir = os.path.join(baseDir, "Table_Of_Content")
        os.makedirs(toc_output_dir, exist_ok=True)
        for entry in os.listdir(toc_output_dir):
            entry_path = os.path.join(toc_output_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
            else:
                os.remove(entry_path)

        toc_json_path = os.path.join(baseDir, "JsonFile", "table_of_content.json")
        with open(toc_json_path, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)
        if not isinstance(loaded_data, dict):
            raise ValueError("The table of contents file must contain an object of lab entries.")

        data = list(loaded_data.items())
        font_family = "Times New Roman"
        if data and data[-1][0] == "font_family":
            font_family = str(data[-1][1])
            data = data[:-1]
        if not data:
            raise ValueError("No table of contents entries were provided.")

        regular_path, bold_path = font_paths(font_family)
        title_font_size = 48
        topic_font_size = 32
        body_font_size = 30
        title_font = ImageFont.truetype(bold_path, title_font_size)
        topic_font = ImageFont.truetype(bold_path, topic_font_size)
        body_font = ImageFont.truetype(regular_path, body_font_size)

        def draw_centered_text(draw, text, font, center_x, center_y):
            text = str(text)
            box = font.getbbox(text)
            text_width = box[2] - box[0]
            text_height = box[3] - box[1]
            draw.text(
                (center_x - text_width / 2 - box[0], center_y - text_height / 2 - box[1]),
                text,
                font=font,
                fill="black",
            )

        def split_long_word(word, font, max_width):
            parts = []
            current = ""
            for character in str(word):
                candidate = current + character
                if current and font.getlength(candidate) > max_width:
                    parts.append(current)
                    current = character
                else:
                    current = candidate
            if current:
                parts.append(current)
            return parts or [str(word)]

        def wrap_text(text, font, max_width):
            words = str(text).split()
            lines = []
            current = ""
            for word in words:
                parts = split_long_word(word, font, max_width) if font.getlength(word) > max_width else [word]
                for part in parts:
                    candidate = (current + " " + part).strip()
                    if not current or font.getlength(candidate) <= max_width:
                        current = candidate
                    else:
                        lines.append(current)
                        current = part
            if current:
                lines.append(current)
            return lines or [""]

        def draw_wrapped_text(draw, lines, font, x, row_top, row_bottom, line_height):
            text_height = len(lines) * line_height
            y = row_top + ((row_bottom - row_top) - text_height) / 2
            for line in lines:
                box = font.getbbox(line)
                draw.text((x, y - box[1]), line, font=font, fill="black")
                y += line_height

        def draw_table_header(draw):
            header_bottom = top + header_height
            draw.rectangle([lab_number_column, top, column_end, header_bottom], outline="black", width=border_width)
            for x in [lab_number_column, lab_name_column, date_column, signature_column, column_end]:
                draw.line([(x, top), (x, header_bottom)], fill="black", width=border_width)

            center_y = top + header_height / 2
            draw_centered_text(draw, "Lab Number", topic_font, (lab_number_column + lab_name_column) / 2, center_y)
            draw_centered_text(draw, "Lab Questions", topic_font, (lab_name_column + date_column) / 2, center_y)
            draw_centered_text(draw, "Date", topic_font, (date_column + signature_column) / 2, center_y)
            draw_centered_text(draw, "Signature", topic_font, (signature_column + column_end) / 2, center_y)

        def draw_row(draw, lab_number, question, row_top, row_bottom):
            draw.rectangle([lab_number_column, row_top, column_end, row_bottom], outline="black", width=border_width)
            for x in [lab_number_column, lab_name_column, date_column, signature_column, column_end]:
                draw.line([(x, row_top), (x, row_bottom)], fill="black", width=border_width)

            center_y = (row_top + row_bottom) / 2
            draw_centered_text(draw, lab_number, body_font, (lab_number_column + lab_name_column) / 2, center_y)
            maximum_width = date_column - lab_name_column - gap * 2
            wrapped_lines = wrap_text(question, body_font, maximum_width)
            draw_wrapped_text(
                draw, wrapped_lines, body_font, lab_name_column + gap, row_top, row_bottom, body_font_size + 10
            )

        def required_row_height(question):
            wrapped = wrap_text(question, body_font, date_column - lab_name_column - gap * 2)
            return max(minimum_row_height, len(wrapped) * (body_font_size + 10) + gap * 2)

        page_number = 1
        index = 0
        while index < len(data):
            image = Image.new("RGB", (a4_width, a4_height), "white")
            draw = ImageDraw.Draw(image)
            draw_centered_text(draw, "Table of Content", title_font, a4_width / 2, 140)
            draw_table_header(draw)
            cursor = top + header_height

            while index < len(data):
                label = str(data[index][0]).strip()
                lab_number = label if label.lower().startswith("lab") else f"Lab {label}"
                question = str(data[index][1])
                row_height = required_row_height(question)
                row_top = cursor
                row_bottom = cursor + row_height
                if row_bottom > max_bottom and cursor > top + header_height:
                    break
                row_bottom = min(row_bottom, max_bottom)
                draw_row(draw, lab_number, question, row_top, row_bottom)
                cursor = row_bottom
                index += 1

            image.save(os.path.join(toc_output_dir, f"TOCMANUALTEST{page_number}.png"))
            page_number += 1


if __name__ == "__main__":
    TOC.generate_toc()
