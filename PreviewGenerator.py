import json
import os
import re
import sys

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import RandomOutputTextFinal
from FrontPageGenerator import FrontPage
from TableofContentGenerator import TOC

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

baseDir = os.path.dirname(os.path.abspath(__file__))
jsonDir = os.path.join(baseDir, "JsonFile")
codeDir = os.path.join(baseDir, "Default_Code_Folder")
snapshotDir = os.path.join(baseDir, "Default_Output_Snapshot_Folder")
tocDir = os.path.join(baseDir, "Table_Of_Content")
frontPagePath = os.path.join(baseDir, "FrontPage", "frontpage_a4.png")
outputTextPath = os.path.join(baseDir, "output_text.txt")
previewPdfPath = os.path.join(baseDir, "Preview_Report.pdf")
captionsPath = os.path.join(jsonDir, "output_captions.json")

for directory in (jsonDir, codeDir, snapshotDir):
    os.makedirs(directory, exist_ok=True)

SKIP_CODE_EXTENSIONS = {
    ".class", ".exe", ".dll", ".jar", ".war", ".ear", ".o", ".obj", ".bin",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".ico", ".svg", ".pdf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".7z",
    ".tar", ".gz", ".mp3", ".mp4", ".avi", ".mov",
}


def report_progress(message):
    print(message, flush=True)


def natural_sort_key(value):
    parts = re.split(r"(\d+)", str(value))
    return [(0, int(part)) if part.isdigit() else (1, part.lower()) for part in parts]


def safe_int(value, default, minimum=None, maximum=None):
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None and result < minimum:
        result = default
    if maximum is not None and result > maximum:
        result = default
    return result


def read_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def resolve_folder(path, default):
    path = str(path or "").strip()
    if not path:
        return default
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(baseDir, path)
    return os.path.abspath(path)


def register_fonts(font_family):
    if str(font_family).lower() == "arial":
        regular_name, bold_name = "arial.ttf", "arialbd.ttf"
        base_font, bold_font = "Arial", "Arial-Bold"
    else:
        regular_name, bold_name = "times.ttf", "timesbd.ttf"
        base_font, bold_font = "Times", "Times-Bold"

    regular_path = os.path.join(baseDir, "Fonts", regular_name)
    bold_path = os.path.join(baseDir, "Fonts", bold_name)
    missing = [name for name, path in ((regular_name, regular_path), (bold_name, bold_path)) if not os.path.isfile(path)]
    if missing:
        raise FileNotFoundError(
            "Missing font file(s): " + ", ".join(missing) + ". Place them in the Fonts folder."
        )

    pdfmetrics.registerFont(TTFont(base_font, regular_path))
    pdfmetrics.registerFont(TTFont(bold_font, bold_path))
    return base_font, bold_font


def read_settings():
    config = read_json(os.path.join(jsonDir, "config_data.json"), {})
    if not isinstance(config, dict):
        config = {}
    margins = config.get("Margins", {}) if isinstance(config.get("Margins", {}), dict) else {}
    figures = config.get("Figures", {}) if isinstance(config.get("Figures", {}), dict) else {}
    code = config.get("CodePage", {}) if isinstance(config.get("CodePage", {}), dict) else {}
    watermark = config.get("Watermark", {}) if isinstance(config.get("Watermark", {}), dict) else {}

    if margins.get("use_default", True):
        top, bottom, left, right = 72, 72, 90, 60
    else:
        top = safe_int(margins.get("top"), 72, 0)
        bottom = safe_int(margins.get("bottom"), 72, 0)
        left = safe_int(margins.get("left"), 90, 0)
        right = safe_int(margins.get("right"), 60, 0)

    page_width, page_height = A4
    if left + right >= page_width - 20 or top + bottom >= page_height - 20:
        raise ValueError("The selected margins leave no usable page area.")

    caption_mode = figures.get("output_caption_mode")
    if not caption_mode:
        if figures.get("dont_caption_output", False):
            caption_mode = "No captions"
        elif figures.get("match_output_name_with_file_name", False):
            caption_mode = "Use file names"
        elif figures.get("use_custom_output_captions", False):
            caption_mode = "Manual captions"
        else:
            caption_mode = "No captions"

    return {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "font": config.get("Typography", {}).get("font_family", "Times New Roman"),
        "include_figure": bool(figures.get("include_figure_labels", False)),
        "generate_output_pages": bool(figures.get("generate_output_pages", False)),
        "caption_mode": caption_mode,
        "code_folder_path": resolve_folder(code.get("code_folder_path"), codeDir),
        "output_folder_path": resolve_folder(figures.get("output_folder_path"), snapshotDir),
        "generate_cover": bool(config.get("CoverPage", {}).get("generate_cover_page", False)),
        "generate_toc": bool(config.get("TableOfContent", {}).get("generate_table_of_content", False)),
        "generate_code": bool(code.get("generate_code_page", False)),
        "output_after_code": bool(code.get("output_after_code", False)),
        "generate_watermark": bool(watermark.get("generate_watermark", False)),
        "watermark_name": str(read_json(os.path.join(jsonDir, "watermark.json"), {}).get("name", "")),
    }


def get_code_page_settings():
    code_page = read_json(os.path.join(jsonDir, "code_page.json"), {})
    line_height = safe_int(code_page.get("line_height"), 32, 10, 120)
    return line_height


def is_probably_code_file(path):
    name = os.path.basename(path)
    if name.startswith(".") or not os.path.isfile(path):
        return False
    if os.path.splitext(name)[1].lower() in SKIP_CODE_EXTENSIONS:
        return False
    try:
        with open(path, "rb") as file:
            chunk = file.read(4096)
        if b"\x00" in chunk:
            return False
        if not chunk:
            return True
        try:
            chunk.decode("utf-8")
        except UnicodeDecodeError:
            chunk.decode("latin-1")
        return True
    except Exception:
        return False


def discover_code_files(code_folder):
    if not os.path.isdir(code_folder):
        return []
    discovered = []
    for root, dirs, files in os.walk(code_folder):
        dirs[:] = [
            name for name in dirs
            if not name.startswith(".") and name not in {"__pycache__", "node_modules", ".git"}
        ]
        dirs.sort(key=natural_sort_key)
        for name in sorted(files, key=natural_sort_key):
            full_path = os.path.join(root, name)
            if not is_probably_code_file(full_path):
                continue
            relative_path = os.path.relpath(full_path, code_folder)
            relative_folder = os.path.dirname(relative_path)
            discovered.append(
                {
                    "path": full_path,
                    "file_name": name,
                    "relative_path": relative_path.replace(os.sep, "/"),
                    "folder": relative_folder.replace(os.sep, "/") if relative_folder else "",
                }
            )
    return sorted(discovered, key=lambda item: natural_sort_key(item["relative_path"]))


def read_code_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return [line.rstrip("\r\n") for line in file]
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as file:
            return [line.rstrip("\r\n") for line in file]


def choose_output_text():
    try:
        with open(outputTextPath, "r", encoding="utf-8") as file:
            lines = file.read().splitlines()
        return RandomOutputTextFinal.chooseRandomText(lines)
    except Exception:
        return "The output screen is shown below."


def read_output_captions():
    data = read_json(captionsPath, {})
    return data if isinstance(data, dict) else {}


def get_custom_caption(captions, file_name, stem):
    for key in (file_name, stem, file_name.lower(), stem.lower()):
        value = captions.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def build_output_caption(custom_caption, file_stem, caption_mode, include_figure, figure_counter):
    if caption_mode == "No captions":
        return ""
    if caption_mode == "Manual captions":
        if not custom_caption:
            return ""
        return f"Figure {figure_counter} : {custom_caption}" if include_figure else custom_caption
    if caption_mode == "Use file names":
        return f"Figure {figure_counter} : {file_stem}" if include_figure else file_stem
    return ""


class PreviewPDF:
    def __init__(self, settings):
        self.settings = settings
        self.base_font, self.bold_font = register_fonts(settings["font"])
        self.canvas = canvas.Canvas(previewPdfPath, pagesize=A4)
        self.page_width, self.page_height = A4
        self.gap = 18
        self.page_count = 0

    def draw_watermark_if_needed(self):
        if not self.settings["generate_watermark"] or not self.settings["watermark_name"].strip():
            return
        self.canvas.saveState()
        self.canvas.setFont(self.bold_font, 72)
        self.canvas.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.2)
        self.canvas.translate(self.page_width / 2, self.page_height / 2)
        self.canvas.rotate(45)
        self.canvas.drawCentredString(0, 0, self.settings["watermark_name"])
        self.canvas.restoreState()

    def finish_page(self, watermark=False):
        if watermark:
            self.draw_watermark_if_needed()
        self.canvas.showPage()
        self.page_count += 1

    def draw_full_page_image(self, image_path):
        self.canvas.drawImage(
            image_path, 0, 0, width=self.page_width, height=self.page_height, preserveAspectRatio=True
        )
        self.finish_page()

    def draw_cover_sample(self):
        if not self.settings["generate_cover"]:
            return
        report_progress("Preview: creating cover page...")
        FrontPage.generate_front_page()
        self.draw_full_page_image(frontPagePath)

    def draw_toc_sample(self):
        if not self.settings["generate_toc"]:
            return
        report_progress("Preview: creating table of contents...")
        TOC.generate_toc()
        files = sorted(
            [name for name in os.listdir(tocDir) if name.lower().endswith((".png", ".jpg", ".jpeg"))],
            key=natural_sort_key,
        )
        if not files:
            raise ValueError("No table of contents pages were generated.")
        self.draw_full_page_image(os.path.join(tocDir, files[0]))

    def fit_prefix_length(self, text, max_width, font_name, font_size):
        low, high = 1, len(text)
        best = 1
        while low <= high:
            middle = (low + high) // 2
            if self.canvas.stringWidth(text[:middle], font_name, font_size) <= max_width:
                best = middle
                low = middle + 1
            else:
                high = middle - 1
        return best

    def wrap_exact_text(self, text, max_width, font_name, font_size):
        text = str(text).expandtabs(4)
        if text == "":
            return [""]
        lines = []
        remaining = text
        while remaining:
            if self.canvas.stringWidth(remaining, font_name, font_size) <= max_width:
                lines.append(remaining)
                break
            length = self.fit_prefix_length(remaining, max_width, font_name, font_size)
            lines.append(remaining[:length])
            remaining = remaining[length:]
        return lines

    def wrap_words(self, text, max_width, font_name, font_size):
        text = str(text)
        if not text:
            return [""]
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if self.canvas.stringWidth(word, font_name, font_size) > max_width:
                if current:
                    lines.append(current)
                    current = ""
                lines.extend(self.wrap_exact_text(word, max_width, font_name, font_size))
                continue
            candidate = (current + " " + word).strip()
            if not current or self.canvas.stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def draw_code_header(self, file_info, y, line_height, font_size, continuity=False):
        max_width = self.page_width - self.settings["left"] - self.settings["right"]
        self.canvas.setFont(self.bold_font, font_size + 2)
        self.canvas.drawString(self.settings["left"], y, "Code Preview")
        y -= line_height
        self.canvas.setFont(self.bold_font, font_size)
        if file_info.get("folder"):
            for line in self.wrap_words(f"Folder: {file_info['folder']}", max_width, self.bold_font, font_size):
                self.canvas.drawString(self.settings["left"], y, line)
                y -= line_height
        file_label = f"File name: {file_info['file_name']}"
        if continuity:
            file_label += " (continued)"
        for line in self.wrap_words(file_label, max_width, self.bold_font, font_size):
            self.canvas.drawString(self.settings["left"], y, line)
            y -= line_height
        self.canvas.drawString(self.settings["left"], y, "Code:")
        y -= line_height
        self.canvas.line(self.settings["left"], y, self.page_width - self.settings["right"], y)
        y -= line_height
        self.canvas.setFont(self.base_font, font_size)
        return y

    def draw_code_sample(self, max_pages=2):
        if not self.settings["generate_code"]:
            return
        report_progress("Preview: creating up to two code pages...")
        source_files = discover_code_files(self.settings["code_folder_path"])
        if not source_files:
            raise ValueError("No supported source-code or text files were found for the preview.")

        line_height = get_code_page_settings()
        font_size = 12
        max_width = self.page_width - self.settings["left"] - self.settings["right"]
        pages_added = 0

        for file_info in source_files:
            if pages_added >= max_pages:
                break
            y = self.draw_code_header(file_info, self.page_height - self.settings["top"], line_height, font_size)
            lines = read_code_lines(file_info["path"])
            for source_line in lines:
                for wrapped_line in self.wrap_exact_text(source_line, max_width, self.base_font, font_size):
                    if y <= self.settings["bottom"]:
                        self.finish_page(watermark=True)
                        pages_added += 1
                        if pages_added >= max_pages:
                            return
                        y = self.draw_code_header(
                            file_info,
                            self.page_height - self.settings["top"],
                            line_height,
                            font_size,
                            continuity=True,
                        )
                    self.canvas.drawString(self.settings["left"], y, wrapped_line)
                    y -= line_height
            self.finish_page(watermark=True)
            pages_added += 1

    def draw_output_sample(self, max_pages=2):
        if not self.settings["generate_output_pages"]:
            return
        report_progress("Preview: creating up to two output pages...")
        output_folder = self.settings["output_folder_path"]
        if not os.path.isdir(output_folder):
            raise FileNotFoundError(f"Output image folder not found: {output_folder}")
        input_images = sorted(
            [
                name for name in os.listdir(output_folder)
                if name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp"))
            ],
            key=natural_sort_key,
        )
        if self.settings["output_after_code"] and self.settings["generate_code"]:
            source_files = discover_code_files(self.settings["code_folder_path"])
            remaining = list(input_images)
            ordered = []
            for source_file in source_files:
                source_stem = os.path.splitext(source_file["file_name"])[0].lower()
                for index, image_name in enumerate(remaining):
                    if os.path.splitext(image_name)[0].lower() == source_stem:
                        ordered.append(remaining.pop(index))
                        break
            input_images = ordered + remaining
        input_images = input_images[:max_pages]
        if not input_images:
            raise ValueError("No supported output images were found for the preview.")

        captions = read_output_captions()
        max_width = self.page_width - self.settings["left"] - self.settings["right"]
        for figure_counter, file_name in enumerate(input_images, start=1):
            report_progress(f"Preview: adding output image {figure_counter} of {len(input_images)}: {file_name}")
            full_path = os.path.join(output_folder, file_name)
            stem = os.path.splitext(file_name)[0]
            caption = build_output_caption(
                get_custom_caption(captions, file_name, stem),
                stem,
                self.settings["caption_mode"],
                self.settings["include_figure"],
                figure_counter,
            )

            y = self.page_height - self.settings["top"]
            self.canvas.setFont(self.bold_font, 14)
            self.canvas.drawString(self.settings["left"], y, "Program Output")
            y -= self.gap * 2
            self.canvas.setFont(self.base_font, 14)
            for line in self.wrap_words(choose_output_text(), max_width, self.base_font, 14):
                self.canvas.drawString(self.settings["left"], y, line)
                y -= 18
            y -= self.gap

            try:
                with Image.open(full_path) as image:
                    image_width, image_height = image.size
            except Exception as exc:
                raise ValueError(f"Could not read output image '{file_name}': {exc}") from exc

            caption_lines = self.wrap_words(caption, max_width, self.bold_font, 12) if caption else []
            caption_height = len(caption_lines) * 16 + self.gap if caption_lines else 0
            max_height = y - self.settings["bottom"] - caption_height
            if max_height <= 0:
                raise ValueError("The selected margins leave no room for output images.")
            scale = min(1, max_width / image_width, max_height / image_height)
            draw_width = image_width * scale
            draw_height = image_height * scale
            image_y = y - draw_height

            self.canvas.drawImage(
                full_path,
                self.settings["left"],
                image_y,
                width=draw_width,
                height=draw_height,
            )
            self.canvas.setLineWidth(1)
            self.canvas.setStrokeColorRGB(0, 0, 0)
            self.canvas.rect(self.settings["left"], image_y, draw_width, draw_height)

            if caption_lines:
                caption_y = image_y - self.gap
                self.canvas.setFont(self.bold_font, 12)
                for line in caption_lines:
                    self.canvas.drawString(self.settings["left"], caption_y, line)
                    caption_y -= 16
            self.finish_page(watermark=True)

    def save(self):
        self.canvas.save()


def main():
    settings = read_settings()
    if not any(
        settings[key] for key in ("generate_cover", "generate_toc", "generate_code", "generate_output_pages")
    ):
        raise ValueError("Enable at least one report section before creating a preview.")
    if settings["generate_watermark"] and not settings["watermark_name"].strip():
        raise ValueError("Watermark text is empty.")

    report_progress("Creating report preview...")
    builder = PreviewPDF(settings)
    builder.draw_cover_sample()
    builder.draw_toc_sample()
    builder.draw_code_sample(max_pages=2)
    builder.draw_output_sample(max_pages=2)
    if builder.page_count == 0:
        raise ValueError("The preview contains no pages.")
    builder.save()
    report_progress(f"[OK] Preview created: {previewPdfPath}")


if __name__ == "__main__":
    main()
