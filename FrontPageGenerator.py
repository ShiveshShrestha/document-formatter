import json
import os

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


class FrontPage:
    @staticmethod
    def generate_front_page():
        width, height = 2480, 3508
        page = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(page)

        front_page_json_path = os.path.join(baseDir, "JsonFile", "frontpage.json")
        with open(front_page_json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        regular_path, bold_path = font_paths(data.get("font_family", "Times New Roman"))
        font_title = ImageFont.truetype(regular_path, 120)
        font_sub = ImageFont.truetype(regular_path, 110)
        font_normal = ImageFont.truetype(regular_path, 68)
        font_normal_bold = ImageFont.truetype(bold_path, 73)
        font_bold = ImageFont.truetype(bold_path, 90)

        logo_path = os.path.join(baseDir, "logo.png")
        if not os.path.isfile(logo_path):
            raise FileNotFoundError("The cover page logo was not found. Place logo.png in the project folder.")

        with Image.open(logo_path) as source_logo:
            logo = source_logo.convert("RGBA")
            logo_scale = min(800 / logo.width, 300 / logo.height)
            logo_width = max(1, round(logo.width * logo_scale))
            logo_height = max(1, round(logo.height * logo_scale))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        page.paste(logo, ((width - logo.width) // 2, 120), logo)

        def text_width(text, font):
            box = draw.textbbox((0, 0), str(text), font=font)
            return box[2] - box[0]

        def draw_center(text, y, font):
            x = (width - text_width(text, font)) // 2
            draw.text((x, y), str(text), fill="black", font=font)

        def split_long_word(word, font, max_width):
            parts = []
            current = ""
            for character in str(word):
                candidate = current + character
                if current and text_width(candidate, font) > max_width:
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
                parts = split_long_word(word, font, max_width) if text_width(word, font) > max_width else [word]
                for part in parts:
                    candidate = (current + " " + part).strip()
                    if not current or text_width(candidate, font) <= max_width:
                        current = candidate
                    else:
                        lines.append(current)
                        current = part
            if current:
                lines.append(current)
            return lines or [""]

        def draw_center_wrapped(text, y, font, max_width, line_gap=22):
            line_height = font.size + line_gap
            for index, line in enumerate(wrap_text(text, font, max_width)):
                draw_center(line, y + index * line_height, font)

        def draw_left_wrapped(text, x, y, font, max_width, line_gap=16):
            lines = wrap_text(text, font, max_width)
            line_height = font.size + line_gap
            for index, line in enumerate(lines):
                draw.text((x, y + index * line_height), line, font=font, fill="black")
            return len(lines), line_height

        draw_center(data.get("CollegeName", ""), 480, font_title)
        draw_center(data.get("Address", ""), 600, font_sub)

        draw.line((1240, 800, 1240, 1900), fill="black", width=10)
        draw.line((1140, 1000, 1140, 1700), fill="black", width=10)
        draw.line((1340, 1000, 1340, 1700), fill="black", width=10)

        draw_center("Lab Report on", 2000, font_bold)
        draw_center_wrapped(data.get("ProjectTitle", ""), 2150, font_bold, width - 500)

        left_x = 300
        start_y = 2500
        gap = 150

        draw.text((left_x, start_y), "Submitted by:", font=font_normal_bold, fill="black")
        draw.text((left_x, start_y + gap), str(data.get("StudentName", "")), font=font_normal, fill="black")
        draw.text((left_x, start_y + 2 * gap), f"Roll No: {data.get('Roll', '')}", font=font_normal, fill="black")
        draw.text((left_x, start_y + 3 * gap), f"Section: {data.get('Section', '')}", font=font_normal, fill="black")
        draw.text((left_x, start_y + 4 * gap), f"Semester: {data.get('Semester', '')}", font=font_normal, fill="black")

        right_x = width - 900
        teacher_max_width = width - right_x - 180
        draw.text((right_x, start_y), "Submitted to:", font=font_normal_bold, fill="black")
        teacher_lines, teacher_line_height = draw_left_wrapped(
            data.get("TeacherName", ""), right_x, start_y + gap, font_normal, teacher_max_width, line_gap=14
        )
        signature_y = start_y + gap + max(2, teacher_lines) * teacher_line_height + 70
        draw.text((right_x, signature_y), "Signature", font=font_normal, fill="black")

        front_page_dir = os.path.join(baseDir, "FrontPage")
        os.makedirs(front_page_dir, exist_ok=True)
        page.save(os.path.join(front_page_dir, "frontpage_a4.png"), dpi=(300, 300))
