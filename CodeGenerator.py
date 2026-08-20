import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

baseDir = os.path.dirname(os.path.abspath(__file__))




defaultCodeDir = os.path.join(baseDir, "Default_Code_Folder")
jsonDir = os.path.join(baseDir, "JsonFile")
manifestPath = os.path.join(jsonDir, "code_page_manifest.json")




with open(os.path.join(jsonDir, "config_data.json"), encoding="utf-8") as f:
    config = json.load(f)



#find folder path
def resolve_folder(path, default):
    path = str(path or "").strip()
    if not path:
        return default
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(baseDir, path)
    return os.path.abspath(path)


codeDir = resolve_folder(config.get("CodePage", {}).get("code_folder_path"), defaultCodeDir)




codePagePath = os.path.join(jsonDir, "code_page.json")
if os.path.exists(codePagePath):
    with open(codePagePath, "r", encoding="utf-8") as f:
        code_page_config = json.load(f)
    LINE_HEIGHT = int(code_page_config.get("line_height", "32"))
else:
    LINE_HEIGHT = 32

print("Code line height:", LINE_HEIGHT)




fontsDir = os.path.join(baseDir, "Fonts")
pdfmetrics.registerFont(TTFont("Times", os.path.join(fontsDir, "times.ttf")))
pdfmetrics.registerFont(TTFont("Times-Bold", os.path.join(fontsDir, "timesbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial", os.path.join(fontsDir, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", os.path.join(fontsDir, "arialbd.ttf")))




font_config = config.get("Typography", {}).get("font_family", "Times New Roman")
if font_config.lower() == "arial":
    BASE_FONT = "Arial"
    BOLD_FONT = "Arial-Bold"
else:
    BASE_FONT = "Times"
    BOLD_FONT = "Times-Bold"




configPath = os.path.join(jsonDir, "config_data.json")
with open(configPath, "r", encoding="utf-8") as file:
    config = json.load(file)

dMargin = config["Margins"]
default = dMargin["use_default"]
if default:
    TOP = 72
    BOTTOM = 72
    LEFT = 90
    RIGHT = 60
else:
    TOP = int(dMargin["top"])
    BOTTOM = int(dMargin["bottom"])
    LEFT = int(dMargin["left"])
    RIGHT = int(dMargin["right"])




FONT_SIZE = config.get("font_size", 12)
HEADER = config.get("header_text", "Source Code")
outputPdfPath = config.get("output_file", "code.pdf")
OUTPUT_AFTER_CODE = config.get("CodePage", {}).get("output_after_code", False)
if not os.path.isabs(outputPdfPath):
    outputPdfPath = os.path.join(baseDir, outputPdfPath)
PAGE_WIDTH, PAGE_HEIGHT = A4


SKIP_EXTENSIONS = {
    ".class",
    ".exe",
    ".dll",
    ".jar",
    ".war",
    ".ear",
    ".o",
    ".obj",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".webp",
    ".ico",
    ".svg",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
}




c = None



def natural_sort_key(value):
    parts = re.split(r"(\d+)", str(value))
    return [(0, int(part)) if part.isdigit() else (1, part.lower()) for part in parts]



def is_probably_code_file(path):

    name = os.path.basename(path)
    if name.startswith("."):
        return False
    ext = os.path.splitext(name)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return False
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
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



#find code files
def discover_code_files():

    discovered = []
    if not os.path.isdir(codeDir):
        return discovered

    for root, dirs, files in os.walk(codeDir):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in {"__pycache__", "node_modules", ".git"}
        ]
        dirs.sort(key=natural_sort_key)
        for name in sorted(files, key=natural_sort_key):
            full_path = os.path.join(root, name)
            if not is_probably_code_file(full_path):
                continue
            rel_path = os.path.relpath(full_path, codeDir)
            rel_folder = os.path.dirname(rel_path)
            discovered.append(
                {
                    "path": full_path,
                    "file_name": name,
                    "relative_path": rel_path.replace(os.sep, "/"),
                    "folder": rel_folder.replace(os.sep, "/") if rel_folder else "",
                    "stem": os.path.splitext(name)[0],
                }
            )

    return sorted(discovered, key=lambda item: natural_sort_key(item["relative_path"]))






def split_long_word(word, max_width):
    pieces = []
    current = ""
    for ch in word:
        test = current + ch
        if c.stringWidth(test, BASE_FONT, FONT_SIZE) <= max_width:
            current = test
        else:
            if current:
                pieces.append(current)
            current = ch
    if current:
        pieces.append(current)
    return pieces



#wrap long code lines
def wrap_text(text, max_width, font=BASE_FONT, font_size=FONT_SIZE):
    if not text:
        return [""]
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        if c.stringWidth(word, font, font_size) > max_width:
            if current:
                lines.append(current)
                current = ""
            lines.extend(split_long_word(word, max_width))
            continue
        test_line = current + (" " if current else "") + word
        if c.stringWidth(test_line, font, font_size) <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]






def draw_header(file_info, y, continuity=False):
    max_width = PAGE_WIDTH - LEFT - RIGHT
    c.setFont(BOLD_FONT, FONT_SIZE + 2)
    c.drawString(LEFT, y, HEADER)
    y -= LINE_HEIGHT

    c.setFont(BOLD_FONT, FONT_SIZE)
    if file_info.get("folder"):
        for line in wrap_text(f"Folder : {file_info['folder']}", max_width, BOLD_FONT, FONT_SIZE):
            c.drawString(LEFT, y, line)
            y -= LINE_HEIGHT

    file_label = f"File Name : {file_info['file_name']}"
    if continuity:
        file_label += " (continued)"
    for line in wrap_text(file_label, max_width, BOLD_FONT, FONT_SIZE):
        c.drawString(LEFT, y, line)
        y -= LINE_HEIGHT

    c.drawString(LEFT, y, "Code:")
    y -= LINE_HEIGHT
    c.line(LEFT, y, PAGE_WIDTH - RIGHT, y)
    y -= LINE_HEIGHT
    c.setFont(BASE_FONT, FONT_SIZE)
    return y



def read_code_lines(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.rstrip() for line in f if line.strip()]
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            return [line.rstrip() for line in f if line.strip()]






#add code file to pdf
def process_file(file_info):
    y = PAGE_HEIGHT - TOP
    y = draw_header(file_info, y)
    max_width = PAGE_WIDTH - LEFT - RIGHT

    try:
        lines = read_code_lines(file_info["path"])
    except Exception as exc:
        lines = [f"Could not read file: {exc}"]

    i = 0
    total_lines = len(lines)
    last_line_buffer = ""
    pending_braces = ""

    while i < total_lines:
        line = lines[i]
        wrapped_lines = wrap_text(line, max_width)

        for wline in wrapped_lines:
            if wline.strip() and all(ch == "}" for ch in wline.strip()):
                pending_braces += wline.strip()
                continue

            if last_line_buffer:
                last_line_buffer += pending_braces
                if y <= BOTTOM:
                    c.showPage()
                    c.setFont(BASE_FONT, FONT_SIZE)
                    y = PAGE_HEIGHT - TOP
                    y = draw_header(file_info, y, continuity=True)
                c.drawString(LEFT, y, last_line_buffer)
                y -= LINE_HEIGHT
                pending_braces = ""
                last_line_buffer = ""

            last_line_buffer = wline

        i += 1

    if last_line_buffer:
        last_line_buffer += pending_braces
        if y <= BOTTOM:
            c.showPage()
            c.setFont(BASE_FONT, FONT_SIZE)
            y = PAGE_HEIGHT - TOP
            y = draw_header(file_info, y, continuity=True)
        c.drawString(LEFT, y, last_line_buffer)
        y -= LINE_HEIGHT




if __name__ == "__main__":
    c = canvas.Canvas(outputPdfPath, pagesize=A4)
    c.setFont(BASE_FONT, FONT_SIZE)

    source_files = discover_code_files()
    print(f"Code folder: {codeDir}")
    print(f"Source files found: {len(source_files)}")

    code_manifest = []
    for file_info in source_files:
        start_page = c.getPageNumber() - 1
        process_file(file_info)
        end_page = c.getPageNumber() - 1
        code_manifest.append(
            {
                "file_name": file_info["file_name"],
                "folder": file_info["folder"],
                "relative_path": file_info["relative_path"],
                "stem": file_info["stem"],
                "start_page": start_page,
                "page_count": end_page - start_page + 1,
            }
        )
        c.showPage()

    c.save()

    os.makedirs(jsonDir, exist_ok=True)
    with open(manifestPath, "w", encoding="utf-8") as f:
        json.dump(code_manifest, f, indent=4)

    print(f"[OK] Code PDF created: {os.path.abspath(outputPdfPath)}")
    if OUTPUT_AFTER_CODE:
        print(f"[OK] Code manifest created: {manifestPath}")
