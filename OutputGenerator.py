import json
import os
import re
import subprocess
import sys
from io import BytesIO

from PIL import Image
from pypdf import PdfReader, PdfWriter
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
snapshotDir = os.path.join(baseDir, "Default_Output_Snapshot_Folder")
codeDir = os.path.join(baseDir, "Default_Code_Folder")
tocDir = os.path.join(baseDir, "Table_Of_Content")
frontPagePath = os.path.join(baseDir, "FrontPage", "frontpage_a4.png")
outputTextPath = os.path.join(baseDir, "output_text.txt")
outputPdfPath = os.path.join(baseDir, "Output.pdf")
codePdfPath = os.path.join(baseDir, "code.pdf")
finalPdfPath = os.path.join(baseDir, "Final_Report.pdf")
tempPdfPath = os.path.join(baseDir, "Final_Report_Base.pdf")
manifestPath = os.path.join(jsonDir, "code_page_manifest.json")
captionsPath = os.path.join(jsonDir, "output_captions.json")
summaryPath = os.path.join(baseDir, "Generation_Summary.txt")

for directory in (jsonDir, snapshotDir, codeDir):
    os.makedirs(directory, exist_ok=True)


def read_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception:
        return default


def read_config_data():
    data = read_json(os.path.join(jsonDir, "config_data.json"), {})
    return data if isinstance(data, dict) else {}


def safe_int(value, default, minimum=None):
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None and result < minimum:
        result = default
    return result


def resolve_folder(path, default):
    path = str(path or "").strip()
    if not path:
        return default
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(baseDir, path)
    return os.path.abspath(path)


def resolve_file_path(path, default, required_ext=None):
    path = str(path or "").strip() or default
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(baseDir, path)
    path = os.path.abspath(path)
    if required_ext and not path.lower().endswith(required_ext.lower()):
        path += required_ext
    return path


def configured_final_pdf_path():
    config = read_config_data()
    export = config.get("Export", {}) if isinstance(config.get("Export", {}), dict) else {}
    return resolve_file_path(
        export.get("final_pdf_path") or export.get("output_pdf_path") or export.get("save_pdf_path"),
        os.path.join(baseDir, "Final_Report.pdf"),
        ".pdf",
    )


def configured_output_input_dir():
    config = read_config_data()
    figures = config.get("Figures", {}) if isinstance(config.get("Figures", {}), dict) else {}
    return resolve_folder(figures.get("output_folder_path"), snapshotDir)


def configured_code_input_dir():
    config = read_config_data()
    code_page = config.get("CodePage", {}) if isinstance(config.get("CodePage", {}), dict) else {}
    return resolve_folder(code_page.get("code_folder_path"), codeDir)


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


def natural_sort_key(value):
    parts = re.split(r"(\d+)", str(value))
    return [(0, int(part)) if part.isdigit() else (1, part.lower()) for part in parts]


def report_progress(message):
    print(message, flush=True)


def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)


def read_code_extension():
    data = read_json(os.path.join(jsonDir, "code_page.json"), {})
    if not isinstance(data, dict):
        return ""
    return str(data.get("file_extension", "")).strip().lower().lstrip(".")


def normalize_match_stem(value):
    name = os.path.basename(str(value or "")).strip().lower()
    if not name:
        return ""

    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    while True:
        stem, extension = os.path.splitext(name)
        if extension.lower() in image_extensions:
            name = stem
        else:
            break

    extensions = []
    configured_extension = read_code_extension()
    if configured_extension:
        extensions.append("." + configured_extension)
    extensions.extend(
        [
            ".java", ".jsp", ".py", ".cpp", ".c", ".h", ".hpp", ".cs", ".js",
            ".jsx", ".ts", ".tsx", ".php", ".rb", ".go", ".kt", ".swift", ".html",
            ".htm", ".css", ".sql", ".xml", ".json", ".txt",
        ]
    )
    for extension in extensions:
        if extension and name.endswith(extension):
            name = name[:-len(extension)]
            break
    return name.strip()


def matching_keys(*values):
    keys = []
    for value in values:
        raw = str(value or "")
        for candidate in (raw, os.path.splitext(raw)[0]):
            key = normalize_match_stem(candidate)
            if key and key not in keys:
                keys.append(key)
    return keys


def order_output_files(output_files, code_manifest):
    remaining = list(output_files)
    ordered = []
    for code_entry in code_manifest:
        code_keys = set(matching_keys(code_entry.get("file_name", ""), code_entry.get("stem", "")))
        match_index = None
        for index, file_name in enumerate(remaining):
            output_keys = set(matching_keys(file_name, os.path.splitext(file_name)[0]))
            if code_keys & output_keys:
                match_index = index
                break
        if match_index is not None:
            ordered.append(remaining.pop(match_index))
    ordered.extend(remaining)
    return ordered


def add_watermark_to_pdf(input_pdf, output_pdf, bold_font, skip_first_pages=0):
    watermark_data = read_json(os.path.join(jsonDir, "watermark.json"), {})
    watermark_text = str(watermark_data.get("name", "")).strip()
    if not watermark_text:
        raise ValueError("Watermark text is empty.")

    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    page_width, page_height = A4
    packet = BytesIO()
    watermark_canvas = canvas.Canvas(packet, pagesize=A4)
    watermark_canvas.setFont(bold_font, 72)
    watermark_canvas.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.2)
    watermark_canvas.translate(page_width / 2, page_height / 2)
    watermark_canvas.rotate(45)
    watermark_canvas.drawCentredString(0, 0, watermark_text)
    watermark_canvas.save()
    packet.seek(0)
    watermark_page = PdfReader(packet).pages[0]

    for page_index, page in enumerate(reader.pages):
        if page_index >= skip_first_pages:
            try:
                page.merge_page(watermark_page, over=True)
            except TypeError:
                page.merge_page(watermark_page)
        writer.add_page(page)

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf)), exist_ok=True)
    with open(output_pdf, "wb") as file:
        writer.write(file)


def merge_pdfs(pdf_paths, output_pdf):
    writer = PdfWriter()
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            continue
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf)), exist_ok=True)
    with open(output_pdf, "wb") as file:
        writer.write(file)


def merge_code_with_matching_outputs(
    output_pdf, code_pdf, output_entries, code_manifest, first_output_pages, output_pdf_path
):
    writer = PdfWriter()
    output_reader = PdfReader(output_pdf)
    code_reader = PdfReader(code_pdf)

    for page_index in range(min(first_output_pages, len(output_reader.pages))):
        writer.add_page(output_reader.pages[page_index])

    outputs_by_key = {}
    for entry in output_entries:
        for key in matching_keys(entry.get("file_name", ""), entry.get("stem", "")):
            outputs_by_key.setdefault(key, []).append(entry)

    used_output_pages = set()
    for code_entry in code_manifest:
        start_page = safe_int(code_entry.get("start_page"), 0, 0)
        page_count = safe_int(code_entry.get("page_count"), 0, 0)
        for page_index in range(start_page, start_page + page_count):
            if 0 <= page_index < len(code_reader.pages):
                writer.add_page(code_reader.pages[page_index])

        matching_output = None
        for key in matching_keys(code_entry.get("file_name", ""), code_entry.get("stem", "")):
            candidates = outputs_by_key.get(key, [])
            while candidates:
                candidate = candidates.pop(0)
                candidate_page = safe_int(candidate.get("page_index"), -1)
                if candidate_page not in used_output_pages:
                    matching_output = candidate
                    break
            if matching_output:
                break

        if matching_output:
            output_page_index = safe_int(matching_output.get("page_index"), -1)
            if 0 <= output_page_index < len(output_reader.pages):
                writer.add_page(output_reader.pages[output_page_index])
                used_output_pages.add(output_page_index)
                report_progress(
                    f"Matched source code '{code_entry.get('file_name', '')}' with output image "
                    f"'{matching_output.get('file_name', '')}'."
                )
        else:
            report_progress(f"[WARNING] No matching output image for code file: {code_entry.get('file_name', '')}")

    for output_entry in output_entries:
        output_page_index = safe_int(output_entry.get("page_index"), -1)
        if output_page_index not in used_output_pages and 0 <= output_page_index < len(output_reader.pages):
            writer.add_page(output_reader.pages[output_page_index])
            report_progress(
                f"[WARNING] No matching code file for output image: {output_entry.get('file_name', '')}. "
                "It was added later."
            )

    with open(output_pdf_path, "wb") as file:
        writer.write(file)


def merge_sections_in_sidebar_order(
    output_pdf, code_pdf, output_entries, first_output_pages, output_pdf_path, include_code
):
    writer = PdfWriter()
    added_output_pages = set()
    output_reader = PdfReader(output_pdf) if os.path.exists(output_pdf) else None

    if output_reader is not None:
        intro_pages = min(first_output_pages, len(output_reader.pages))
        for page_index in range(intro_pages):
            writer.add_page(output_reader.pages[page_index])
            added_output_pages.add(page_index)

    if include_code and os.path.exists(code_pdf):
        code_reader = PdfReader(code_pdf)
        for page in code_reader.pages:
            writer.add_page(page)

    if output_reader is not None:
        page_indexes = [safe_int(entry.get("page_index"), -1) for entry in output_entries]
        if not output_entries:
            page_indexes = list(range(first_output_pages, len(output_reader.pages)))
        for page_index in page_indexes:
            if page_index in added_output_pages:
                continue
            if 0 <= page_index < len(output_reader.pages):
                writer.add_page(output_reader.pages[page_index])
                added_output_pages.add(page_index)

    with open(output_pdf_path, "wb") as file:
        writer.write(file)


def read_settings():
    config = read_config_data()
    margins = config.get("Margins", {}) if isinstance(config.get("Margins", {}), dict) else {}
    figures = config.get("Figures", {}) if isinstance(config.get("Figures", {}), dict) else {}
    cover = config.get("CoverPage", {}) if isinstance(config.get("CoverPage", {}), dict) else {}
    toc = config.get("TableOfContent", {}) if isinstance(config.get("TableOfContent", {}), dict) else {}
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
        "caption_mode": caption_mode,
        "include_figure": bool(figures.get("include_figure_labels", False)),
        "generate_output_pages": bool(figures.get("generate_output_pages", False)),
        "generate_cover": bool(cover.get("generate_cover_page", False)),
        "generate_toc": bool(toc.get("generate_table_of_content", False)),
        "generate_code": bool(code.get("generate_code_page", False)),
        "output_after_code": bool(code.get("output_after_code", False)),
        "generate_watermark": bool(watermark.get("generate_watermark", False)),
    }


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


def wrap_pdf_text(pdf, text, max_width, font_name, font_size):
    text = str(text)
    if not text:
        return [""]
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if pdf.stringWidth(word, font_name, font_size) > max_width:
            if current:
                lines.append(current)
                current = ""
            piece = ""
            for character in word:
                candidate = piece + character
                if piece and pdf.stringWidth(candidate, font_name, font_size) > max_width:
                    lines.append(piece)
                    piece = character
                else:
                    piece = candidate
            current = piece
            continue
        candidate = (current + " " + word).strip()
        if not current or pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def create_generation_summary(
    final_pdf, output_files, code_manifest, pages_without_watermark, watermark_enabled,
    output_after_code, captions
):
    try:
        total_pages = len(PdfReader(final_pdf).pages)
    except Exception:
        total_pages = 0
    try:
        pdf_size_mb = os.path.getsize(final_pdf) / (1024 * 1024)
    except Exception:
        pdf_size_mb = 0

    code_files = [entry.get("relative_path") or entry.get("file_name", "") for entry in code_manifest]
    code_stems = {normalize_match_stem(name) for name in code_files if normalize_match_stem(name)}
    output_stems = {normalize_match_stem(name) for name in output_files if normalize_match_stem(name)}
    matched = len(code_stems & output_stems)
    unmatched_code = sorted([name for name in code_files if normalize_match_stem(name) not in output_stems], key=natural_sort_key)
    unmatched_output = sorted([name for name in output_files if normalize_match_stem(name) not in code_stems], key=natural_sort_key)
    custom_caption_count = sum(1 for value in captions.values() if isinstance(value, str) and value.strip())
    ready_note = "Report created successfully."
    if output_after_code and (unmatched_code or unmatched_output):
        ready_note = "Report created, but some code and output file names did not match."

    lines = [
        "GENERATION SUMMARY",
        "=" * 60,
        f"Status: {ready_note}",
        "",
        "Final Report",
        "-" * 60,
        f"Location : {final_pdf}",
        f"Pages    : {total_pages}",
        f"File size: {pdf_size_mb:.2f} MB",
        "",
        "Included Content",
        "-" * 60,
        f"Code files                : {len(code_files)}",
        f"Output images             : {len(output_files)}",
        f"Manual captions           : {custom_caption_count}",
        f"Watermark                 : {'Yes' if watermark_enabled else 'No'}",
        f"Place output after code   : {'Yes' if output_after_code else 'No'}",
        f"Pages without watermark   : {pages_without_watermark}",
        "",
        "File Matching",
        "-" * 60,
        f"Matching names             : {matched}",
        f"Code files without output  : {len(unmatched_code)}",
        f"Outputs without code file  : {len(unmatched_output)}",
    ]

    if output_after_code:
        lines.append("Output images are placed after code files with matching names.")
    else:
        lines.append("Output images were placed in the standard output section.")

    if unmatched_code:
        lines.extend(["", "Code files without matching output images", "-" * 60])
        lines.extend([f"- {name}" for name in unmatched_code[:25]])
        if len(unmatched_code) > 25:
            lines.append(f"- ... and {len(unmatched_code) - 25} more")

    if unmatched_output:
        lines.extend(["", "Output images without matching code files", "-" * 60])
        lines.extend([f"- {name}" for name in unmatched_output[:25]])
        if len(unmatched_output) > 25:
            lines.append(f"- ... and {len(unmatched_output) - 25} more")

    lines.extend(["", "Next Step", "-" * 60])
    if output_after_code and (unmatched_code or unmatched_output):
        lines.append("Review the items above and update file names or captions if needed.")
    else:
        lines.append("The report is ready for review.")

    summary = "\n".join(lines)
    with open(summaryPath, "w", encoding="utf-8") as file:
        file.write(summary)
    return summary


def main():
    global finalPdfPath
    finalPdfPath = configured_final_pdf_path()
    os.makedirs(os.path.dirname(os.path.abspath(finalPdfPath)), exist_ok=True)

    settings = read_settings()
    has_content = any(
        settings[key] for key in ("generate_cover", "generate_toc", "generate_code", "generate_output_pages")
    )
    if not has_content:
        raise ValueError("Enable at least one report section before generating the report.")

    base_font, bold_font = register_fonts(settings["font"])
    report_progress("Preparing the report...")
    report_progress(f"Final report location: {finalPdfPath}")

    code_manifest = []
    if settings["generate_code"]:
        script_path = os.path.join(baseDir, "CodeGenerator.py")
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Code generator not found: {script_path}")
        report_progress("Creating code pages...")
        subprocess.run([sys.executable, "-u", script_path], check=True, cwd=baseDir)
        code_manifest_data = read_json(manifestPath, [])
        code_manifest = code_manifest_data if isinstance(code_manifest_data, list) else []
        if not code_manifest or not os.path.exists(codePdfPath):
            raise ValueError("Code pages could not be generated.")
    else:
        report_progress("Code pages are disabled.")

    output_source_dir = configured_output_input_dir()
    supported_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
    output_files = []
    if settings["generate_output_pages"]:
        if not os.path.isdir(output_source_dir):
            raise FileNotFoundError(f"Output image folder not found: {output_source_dir}")
        output_files = sorted(
            [name for name in os.listdir(output_source_dir) if name.lower().endswith(supported_extensions)],
            key=natural_sort_key,
        )
        if not output_files:
            raise ValueError(f"No supported output images were found in: {output_source_dir}")
        if settings["output_after_code"] and settings["generate_code"]:
            output_files = order_output_files(output_files, code_manifest)
        report_progress(f"Found {len(output_files)} output image(s) in: {output_source_dir}")
    else:
        report_progress("Output images are disabled.")

    page_width, page_height = A4
    pdf = canvas.Canvas(outputPdfPath, pagesize=A4)
    pages_without_watermark = 0

    if settings["generate_cover"]:
        report_progress("Creating cover page...")
        FrontPage.generate_front_page()
        pdf.drawImage(frontPagePath, 0, 0, width=page_width, height=page_height, preserveAspectRatio=True)
        pdf.showPage()
        pages_without_watermark += 1

    if settings["generate_toc"]:
        report_progress("Creating table of contents...")
        TOC.generate_toc()
        toc_files = sorted(
            [name for name in os.listdir(tocDir) if name.lower().endswith((".png", ".jpg", ".jpeg"))],
            key=natural_sort_key,
        )
        if not toc_files:
            raise ValueError("No table of contents pages were generated.")
        for file_name in toc_files:
            toc_path = os.path.join(tocDir, file_name)
            pdf.drawImage(toc_path, 0, 0, width=page_width, height=page_height, preserveAspectRatio=True)
            pdf.showPage()
            pages_without_watermark += 1

    output_entries = []
    captions = read_output_captions()
    figure_counter = 1
    gap = 18
    max_width = page_width - settings["left"] - settings["right"]

    for output_index, file_name in enumerate(output_files, start=1):
        report_progress(f"Adding output image {output_index} of {len(output_files)}: {file_name}")
        full_path = os.path.join(output_source_dir, file_name)
        stem = os.path.splitext(file_name)[0]
        custom_caption = get_custom_caption(captions, file_name, stem)
        caption_text = build_output_caption(
            custom_caption, stem, settings["caption_mode"], settings["include_figure"], figure_counter
        )
        output_entries.append(
            {"file_name": file_name, "stem": stem, "page_index": pdf.getPageNumber() - 1}
        )

        y = page_height - settings["top"]
        pdf.setFont(bold_font, 14)
        pdf.drawString(settings["left"], y, "Program Output")
        y -= gap * 2

        pdf.setFont(base_font, 14)
        for line in wrap_pdf_text(pdf, choose_output_text(), max_width, base_font, 14):
            pdf.drawString(settings["left"], y, line)
            y -= 18
        y -= gap

        try:
            with Image.open(full_path) as image:
                image_width, image_height = image.size
        except Exception as exc:
            raise ValueError(f"Could not read output image '{file_name}': {exc}") from exc
        if image_width <= 0 or image_height <= 0:
            raise ValueError(f"Output image '{file_name}' has invalid dimensions.")

        caption_lines = wrap_pdf_text(pdf, caption_text, max_width, bold_font, 12) if caption_text else []
        caption_height = len(caption_lines) * 16 + gap if caption_lines else 0
        max_height = y - settings["bottom"] - caption_height
        if max_height <= 0:
            raise ValueError("The selected margins leave no room for output images.")
        scale = min(1, max_width / image_width, max_height / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale
        image_y = y - draw_height

        pdf.drawImage(full_path, settings["left"], image_y, width=draw_width, height=draw_height)
        pdf.setLineWidth(1)
        pdf.setStrokeColorRGB(0, 0, 0)
        pdf.rect(settings["left"], image_y, draw_width, draw_height)

        if caption_lines:
            caption_y = image_y - gap
            pdf.setFont(bold_font, 12)
            for line in caption_lines:
                pdf.drawString(settings["left"], caption_y, line)
                caption_y -= 16

        figure_counter += 1
        pdf.showPage()

    pdf.save()

    if settings["output_after_code"] and settings["generate_code"] and settings["generate_output_pages"]:
        report_progress("Placing output images after matching code files...")
        merge_code_with_matching_outputs(
            outputPdfPath, codePdfPath, output_entries, code_manifest, pages_without_watermark, tempPdfPath
        )
    else:
        report_progress("Combining report sections in order: Cover, Contents, Code, Output...")
        merge_sections_in_sidebar_order(
            outputPdfPath,
            codePdfPath,
            output_entries,
            pages_without_watermark,
            tempPdfPath,
            settings["generate_code"] and os.path.exists(codePdfPath),
        )

    if not os.path.exists(tempPdfPath) or len(PdfReader(tempPdfPath).pages) == 0:
        raise ValueError("The report contains no pages.")

    if settings["generate_watermark"]:
        report_progress("Applying watermark...")
        add_watermark_to_pdf(tempPdfPath, finalPdfPath, bold_font, skip_first_pages=pages_without_watermark)
    else:
        report_progress("Saving final report...")
        merge_pdfs([tempPdfPath], finalPdfPath)

    remove_file_if_exists(tempPdfPath)
    for intermediate_pdf in (
        outputPdfPath,
        codePdfPath,
        os.path.join(baseDir, "Output_Watermarked.pdf"),
        os.path.join(baseDir, "code_Watermarked.pdf"),
    ):
        if os.path.abspath(intermediate_pdf) != os.path.abspath(finalPdfPath):
            remove_file_if_exists(intermediate_pdf)

    summary = create_generation_summary(
        finalPdfPath,
        output_files,
        code_manifest,
        pages_without_watermark,
        settings["generate_watermark"],
        settings["output_after_code"],
        captions,
    )
    report_progress(summary)
    report_progress(f"[OK] Generation summary saved: {summaryPath}")
    report_progress(f"[OK] Final report created: {finalPdfPath}")


if __name__ == "__main__":
    main()
