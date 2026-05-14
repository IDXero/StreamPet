"""
Generates StreamPet_Setup_Guide.pdf — run once from the streampet/ directory.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Flowable

# ── Colour palette ─────────────────────────────────────────────────────────────
PINK      = colors.HexColor("#db2777")
PINK_LITE = colors.HexColor("#fce7f3")
PINK_MID  = colors.HexColor("#f472b6")
DARK      = colors.HexColor("#1e1e2e")
GRAY      = colors.HexColor("#6b7280")
CODE_BG   = colors.HexColor("#1e1b4b")
CODE_FG   = colors.HexColor("#e2e8f0")
WARN_BG   = colors.HexColor("#fef9c3")
WARN_BOR  = colors.HexColor("#ca8a04")
INFO_BG   = colors.HexColor("#eff6ff")
INFO_BOR  = colors.HexColor("#3b82f6")
OK_BG     = colors.HexColor("#f0fdf4")
OK_BOR    = colors.HexColor("#16a34a")

W, H = A4


# ── Custom flowables ───────────────────────────────────────────────────────────

class ColorBar(Flowable):
    """Left-border accent bar for callout boxes."""
    def __init__(self, text_flowables, bg, border_color, padding=10):
        super().__init__()
        self._items = text_flowables
        self._bg = bg
        self._bc = border_color
        self._pad = padding

    def wrap(self, aw, ah):
        self._aw = aw
        total = self._pad * 2
        for item in self._items:
            w, h = item.wrap(aw - self._pad * 2 - 6, ah)
            item._cached_h = h
            total += h + 4
        self._total_h = total
        return aw, total

    def draw(self):
        self.canv.setFillColor(self._bg)
        self.canv.roundRect(0, 0, self._aw, self._total_h, 6, fill=1, stroke=0)
        self.canv.setFillColor(self._bc)
        self.canv.rect(0, 0, 5, self._total_h, fill=1, stroke=0)
        y = self._total_h - self._pad
        for item in self._items:
            h = item._cached_h
            y -= h
            item.drawOn(self.canv, self._pad + 8, y)
            y -= 4
        y -= self._pad


# ── Styles ─────────────────────────────────────────────────────────────────────

def make_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": s("ct", fontName="Helvetica-Bold", fontSize=36,
                         textColor=colors.white, leading=44, alignment=TA_CENTER),
        "cover_sub":   s("cs", fontName="Helvetica", fontSize=16,
                         textColor=colors.HexColor("#fbcfe8"), leading=22, alignment=TA_CENTER),
        "cover_tag":   s("ctag", fontName="Helvetica", fontSize=11,
                         textColor=colors.HexColor("#f9a8d4"), leading=16, alignment=TA_CENTER),
        "h1": s("h1", fontName="Helvetica-Bold", fontSize=22, textColor=PINK,
                leading=28, spaceBefore=18, spaceAfter=8),
        "h2": s("h2", fontName="Helvetica-Bold", fontSize=15, textColor=DARK,
                leading=20, spaceBefore=14, spaceAfter=5),
        "h3": s("h3", fontName="Helvetica-Bold", fontSize=12, textColor=GRAY,
                leading=16, spaceBefore=10, spaceAfter=3),
        "body": s("body", fontName="Helvetica", fontSize=10, textColor=DARK,
                  leading=15, spaceAfter=6),
        "body_small": s("bs", fontName="Helvetica", fontSize=9, textColor=GRAY,
                        leading=13),
        "code": s("code", fontName="Courier", fontSize=9, textColor=CODE_FG,
                  backColor=CODE_BG, leading=13, leftIndent=10, rightIndent=10,
                  spaceBefore=4, spaceAfter=4),
        "code_inline": s("ci", fontName="Courier", fontSize=9.5, textColor=PINK,
                         leading=14),
        "callout": s("callout", fontName="Helvetica", fontSize=10, textColor=DARK,
                     leading=14),
        "callout_bold": s("calloutb", fontName="Helvetica-Bold", fontSize=10,
                          textColor=DARK, leading=14),
        "bullet": s("bullet", fontName="Helvetica", fontSize=10, textColor=DARK,
                    leading=15, leftIndent=16, bulletIndent=6, spaceAfter=3),
        "step_num": s("sn", fontName="Helvetica-Bold", fontSize=18, textColor=PINK_MID,
                      leading=22, alignment=TA_CENTER),
        "toc_entry": s("toc", fontName="Helvetica", fontSize=11, textColor=DARK,
                       leading=18, leftIndent=12),
        "toc_h": s("toch", fontName="Helvetica-Bold", fontSize=11, textColor=PINK,
                   leading=18),
        "footer": s("footer", fontName="Helvetica", fontSize=8, textColor=GRAY,
                    alignment=TA_CENTER),
        "table_h": s("th", fontName="Helvetica-Bold", fontSize=9,
                     textColor=colors.white, alignment=TA_CENTER, leading=12),
        "table_c": s("tc", fontName="Helvetica", fontSize=9, textColor=DARK,
                     leading=12),
        "table_code": s("tcode", fontName="Courier", fontSize=8, textColor=DARK,
                        leading=12),
    }


ST = make_styles()


def h1(txt):  return Paragraph(txt, ST["h1"])
def h2(txt):  return Paragraph(txt, ST["h2"])
def h3(txt):  return Paragraph(txt, ST["h3"])
def body(txt): return Paragraph(txt, ST["body"])
def bsmall(txt): return Paragraph(txt, ST["body_small"])
def sp(n=6):  return Spacer(1, n)
def hr():     return HRFlowable(width="100%", thickness=1, color=PINK_LITE, spaceAfter=6, spaceBefore=6)
def bullet(txt): return Paragraph(f"<bullet>&bull;</bullet> {txt}", ST["bullet"])


def code_block(lines):
    text = "<br/>".join(lines)
    return Paragraph(text, ST["code"])


def callout(label, lines, kind="info"):
    bg  = {"warn": WARN_BG, "ok": OK_BG, "info": INFO_BG}[kind]
    bor = {"warn": WARN_BOR, "ok": OK_BOR, "info": INFO_BOR}[kind]
    icon = {"warn": "&#9888; ", "ok": "&#10003; ", "info": "&#9432; "}[kind]
    items = [Paragraph(f"<b>{icon}{label}</b>", ST["callout_bold"])]
    for ln in lines:
        items.append(Paragraph(ln, ST["callout"]))
    return ColorBar(items, bg, bor)


def step_table(num, title, content_flowables):
    """Numbered step block."""
    num_para = Paragraph(str(num), ST["step_num"])
    title_para = Paragraph(title, ST["h2"])
    inner = [title_para, sp(4)] + content_flowables
    tbl = Table(
        [[num_para, inner]],
        colWidths=[1.2*cm, None],
    )
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEAFTER", (0, 0), (0, 0), 1.5, PINK_MID),
    ]))
    return tbl


# ── Page templates ─────────────────────────────────────────────────────────────

def on_page(canvas, doc):
    canvas.saveState()
    # Footer bar
    canvas.setFillColor(PINK_LITE)
    canvas.rect(doc.leftMargin, 1.2*cm, W - doc.leftMargin - doc.rightMargin, 0.45*cm, fill=1, stroke=0)
    canvas.setFillColor(PINK)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(doc.leftMargin + 4, 1.35*cm, "StreamPet — Self-Hosted Twitch Stream Pet")
    canvas.drawRightString(W - doc.rightMargin - 4, 1.35*cm, f"Page {doc.page}")
    canvas.restoreState()


def cover_page():
    story = []
    story.append(Spacer(1, 2.8*cm))

    # Big pink gradient title block via table
    title_block = Table(
        [[Paragraph("StreamPet", ST["cover_title"]),]],
        colWidths=[W - 4*cm],
    )
    title_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PINK),
        ("ROWPADDING", (0, 0), (-1, -1), 18),
        ("ROUNDEDCORNERS", [12, 12, 12, 12]),
    ]))
    story.append(title_block)
    story.append(sp(14))
    story.append(Paragraph("Self-Hosted Twitch Stream Pet", ST["cover_sub"]))
    story.append(sp(6))
    story.append(Paragraph("Setup &amp; Configuration Guide", ST["cover_sub"]))
    story.append(sp(30))

    tag_data = [
        ["LLM: Ollama (GPU)", "TTS: Piper (Local)", "Bot: TwitchIO", "UI: OBS Browser Source"],
    ]
    tag_tbl = Table(tag_data, colWidths=[3.6*cm]*4)
    tag_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PINK),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fbcfe8")),
    ]))
    story.append(tag_tbl)
    story.append(sp(40))
    story.append(Paragraph("RTX 3060 12 GB &bull; Linux VM &bull; OBS Studio", ST["cover_tag"]))
    story.append(sp(8))
    story.append(Paragraph("Revision 1.2 — May 2026", ST["cover_tag"]))
    story.append(PageBreak())
    return story


def toc_page():
    story = [h1("Table of Contents"), hr(), sp(6)]
    entries = [
        ("1",  "System Overview",          "Architecture and component map"),
        ("2",  "Prerequisites",            "What you need before starting"),
        ("3",  "Installation",             "Step-by-step install walkthrough"),
        ("4",  "Twitch Credentials",       "Registering an app and running get_token.py"),
        ("5",  "Environment Configuration","All .env variables explained"),
        ("6",  "LLM Configuration",        "Ollama models and GPU setup"),
        ("7",  "TTS Configuration",        "Piper voices and audio routing"),
        ("8",  "Pet Artwork",              "Swapping pet_idle.png / pet_talk.png"),
        ("9",  "OBS Setup",               "VM IP, firewall, browser source, audio"),
        ("10", "SSH & Headless Operation", "Token flow, tmux, SSH tunnelling"),
        ("11", "Running StreamPet",        "Persistent system service, management commands"),
        ("12", "Customisation",            "Personality, cooldowns, bubble style"),
        ("13", "Troubleshooting",          "Common issues and fixes"),
        ("14", "File Reference",           "Every file in the project explained"),
    ]
    rows = []
    for num, title, desc in entries:
        rows.append([
            Paragraph(f"<b>{num}</b>", ST["toc_h"]),
            Paragraph(title, ST["toc_h"]),
            Paragraph(desc, ST["body_small"]),
        ])
    tbl = Table(rows, colWidths=[1.2*cm, 5.5*cm, None])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, PINK_LITE]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, PINK_MID),
    ]))
    story.append(tbl)
    story.append(PageBreak())
    return story


# ── Section builders ───────────────────────────────────────────────────────────

def section_overview():
    story = [h1("1. System Overview"), hr()]

    story.append(body(
        "StreamPet is a fully self-hosted Twitch chat bot and animated overlay. "
        "Viewers type <b>!ask &lt;question&gt;</b> in your Twitch channel; the pet "
        "responds with a spoken, animated reply generated entirely on your local machine "
        "— no cloud APIs, no subscriptions, no data leaving your VM."
    ))
    story.append(sp(10))

    story.append(h2("Architecture"))
    arch_rows = [
        [Paragraph("Component", ST["table_h"]), Paragraph("Role", ST["table_h"]),
         Paragraph("Technology", ST["table_h"])],
        [Paragraph("Twitch Bot", ST["table_c"]),
         Paragraph("Listens for !ask, posts replies to chat", ST["table_c"]),
         Paragraph("TwitchIO 2.x (pinned &lt;3.0)", ST["table_c"])],
        [Paragraph("LLM Engine", ST["table_c"]),
         Paragraph("Generates natural language answers", ST["table_c"]),
         Paragraph("Ollama + llama3.2 (GPU)", ST["table_c"])],
        [Paragraph("TTS Engine", ST["table_c"]),
         Paragraph("Converts text to speech WAV", ST["table_c"]),
         Paragraph("Piper TTS binary + ONNX model", ST["table_c"])],
        [Paragraph("Web Server", ST["table_c"]),
         Paragraph("Serves browser source + audio files", ST["table_c"]),
         Paragraph("FastAPI + Uvicorn (Python)", ST["table_c"])],
        [Paragraph("WebSocket", ST["table_c"]),
         Paragraph("Pushes events from bot to browser", ST["table_c"]),
         Paragraph("FastAPI WebSocket endpoint", ST["table_c"])],
        [Paragraph("Browser Source", ST["table_c"]),
         Paragraph("Renders pet, speech bubble, plays TTS", ST["table_c"]),
         Paragraph("OBS Browser Source (HTML/JS)", ST["table_c"])],
    ]
    arch_tbl = Table(arch_rows, colWidths=[3.5*cm, 6.5*cm, 5*cm])
    arch_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(arch_tbl)
    story.append(sp(12))

    story.append(h2("Data Flow"))
    flow_rows = [
        [Paragraph("Step", ST["table_h"]), Paragraph("Action", ST["table_h"])],
        [Paragraph("1", ST["table_c"]), Paragraph("Viewer types !ask What is gravity? in Twitch chat", ST["table_c"])],
        [Paragraph("2", ST["table_c"]), Paragraph("TwitchIO bot receives the message, checks cooldown", ST["table_c"])],
        [Paragraph("3", ST["table_c"]), Paragraph("Bot broadcasts thinking event via WebSocket — bubble appears", ST["table_c"])],
        [Paragraph("4", ST["table_c"]), Paragraph("Bot sends question to Ollama REST API (localhost:11434)", ST["table_c"])],
        [Paragraph("5", ST["table_c"]), Paragraph("Ollama runs llama3.2 (GPU-accelerated) and returns answer text", ST["table_c"])],
        [Paragraph("6", ST["table_c"]), Paragraph("Answer piped to Piper TTS binary; WAV saved to static/audio/", ST["table_c"])],
        [Paragraph("7", ST["table_c"]), Paragraph("Bot broadcasts speak event with text + audio URL via WebSocket", ST["table_c"])],
        [Paragraph("8", ST["table_c"]), Paragraph("OBS Browser Source receives event, plays WAV, animates pet mouth", ST["table_c"])],
        [Paragraph("9", ST["table_c"]), Paragraph("Bot also posts the text reply back to Twitch chat", ST["table_c"])],
    ]
    flow_tbl = Table(flow_rows, colWidths=[1.2*cm, None])
    flow_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
    ]))
    story.append(flow_tbl)
    story.append(PageBreak())
    return story


def section_prerequisites():
    story = [h1("2. Prerequisites"), hr()]
    story.append(body("Before running the installer, confirm these items are in place:"))
    story.append(sp(8))

    reqs = [
        [Paragraph("Item", ST["table_h"]), Paragraph("Requirement", ST["table_h"]),
         Paragraph("Notes", ST["table_h"])],
        [Paragraph("OS", ST["table_c"]), Paragraph("Linux (Ubuntu/Debian)", ST["table_c"]),
         Paragraph("The installer uses apt-style tooling", ST["table_c"])],
        [Paragraph("GPU", ST["table_c"]), Paragraph("NVIDIA Turing or newer (GTX 16xx / RTX 20xx+)", ST["table_c"]),
         Paragraph("Minimum 4 GB VRAM. CUDA driver required for Ollama GPU acceleration. See GPU guide below.", ST["table_c"])],
        [Paragraph("Python", ST["table_c"]), Paragraph("Python 3.10+", ST["table_c"]),
         Paragraph("Python 3.14 confirmed working", ST["table_c"])],
        [Paragraph("python3-venv", ST["table_c"]), Paragraph("apt package", ST["table_c"]),
         Paragraph("sudo apt install python3.14-venv", ST["table_c"])],
        [Paragraph("curl", ST["table_c"]), Paragraph("Command-line tool", ST["table_c"]),
         Paragraph("Used by install.sh to download Piper and Ollama", ST["table_c"])],
        [Paragraph("OBS Studio", ST["table_c"]), Paragraph("Any recent version", ST["table_c"]),
         Paragraph("Browser Source plugin included by default", ST["table_c"])],
        [Paragraph("Twitch account", ST["table_c"]), Paragraph("Bot account", ST["table_c"]),
         Paragraph("Separate bot account recommended (free)", ST["table_c"])],
        [Paragraph("Internet", ST["table_c"]), Paragraph("For initial setup only", ST["table_c"]),
         Paragraph("Downloads Piper binary, voice model, and Ollama model", ST["table_c"])],
    ]
    tbl = Table(reqs, colWidths=[3*cm, 4.5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(12))

    story.append(h2("GPU Selection Guide"))
    story.append(body(
        "Ollama runs the LLM entirely on the GPU. The model you choose determines the minimum "
        "VRAM required. Piper TTS runs on CPU and uses no VRAM. "
        "All GPUs listed are Turing architecture (2018) or newer and support the CUDA versions "
        "required by Ollama."
    ))
    story.append(sp(8))

    gpu_rows = [
        [Paragraph("Model", ST["table_h"]), Paragraph("VRAM needed", ST["table_h"]),
         Paragraph("Quality", ST["table_h"]), Paragraph("Suggested GPUs", ST["table_h"])],

        [Paragraph("llama3.2 3B\n(default)", ST["table_c"]),
         Paragraph("~3 GB", ST["table_c"]),
         Paragraph("Good — fast responses, solid for chat", ST["table_c"]),
         Paragraph("GTX 1660 Super (6 GB), RTX 2060 (6 GB), RTX 3050 (8 GB), RTX 3060 (12 GB), RTX 4060 (8 GB)", ST["table_c"])],

        [Paragraph("phi3:mini 3.8B", ST["table_c"]),
         Paragraph("~3 GB", ST["table_c"]),
         Paragraph("Good — very fast, optimised for instruction following", ST["table_c"]),
         Paragraph("GTX 1660 Super (6 GB), RTX 2060 (6 GB), RTX 3050 (8 GB), RTX 4060 (8 GB)", ST["table_c"])],

        [Paragraph("llama3.2 7B\nmistral 7B", ST["table_c"]),
         Paragraph("~5 GB", ST["table_c"]),
         Paragraph("Better — more natural, creative answers", ST["table_c"]),
         Paragraph("RTX 2060 Super (8 GB), RTX 2070 (8 GB), RTX 3060 (12 GB), RTX 3070 (8 GB), RTX 4060 Ti (8/16 GB)", ST["table_c"])],

        [Paragraph("llama3.1 8B\ngemma2 9B", ST["table_c"]),
         Paragraph("~6 GB", ST["table_c"]),
         Paragraph("Very good — noticeably higher quality", ST["table_c"]),
         Paragraph("RTX 2070 Super (8 GB), RTX 2080 (8 GB), RTX 3060 (12 GB), RTX 3070 Ti (8 GB), RTX 4070 (12 GB)", ST["table_c"])],

        [Paragraph("llama3 70B\n(quantised)", ST["table_c"]),
         Paragraph("~24 GB+", ST["table_c"]),
         Paragraph("Excellent — overkill for stream chat", ST["table_c"]),
         Paragraph("RTX 3090 (24 GB), RTX 4090 (24 GB), or dual-GPU setups", ST["table_c"])],
    ]
    gpu_tbl = Table(gpu_rows, colWidths=[3*cm, 2.2*cm, 4*cm, None])
    gpu_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(gpu_tbl)
    story.append(sp(10))

    story.append(callout(
        "Recommended sweet spot",
        [
            "For most streamers: RTX 3060 12 GB or RTX 4060 Ti 16 GB. Both run llama3.1 8B "
            "comfortably with headroom for a quantised 13B model. The extra VRAM also means "
            "the full model stays loaded between questions — no reload delay.",
        ],
        kind="ok"
    ))
    story.append(sp(8))

    story.append(callout(
        "NVIDIA Driver Note",
        [
            "Ollama auto-detects your GPU via CUDA. If nvidia-smi is not in your PATH "
            "or returns no output, install the NVIDIA drivers before proceeding "
            "(prepare_vm.sh handles this automatically).",
            "Check: nvidia-smi",
            "Manual install guide: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/",
        ],
        kind="warn"
    ))
    story.append(PageBreak())
    return story


def section_installation():
    story = [h1("3. Installation"), hr()]
    story.append(body(
        "Follow these steps in order. The full process takes about 10–15 minutes on first run, "
        "mostly waiting for model downloads."
    ))
    story.append(sp(10))

    story.append(KeepTogether([
        step_table(1, "Prepare the VM (first time only — requires sudo)", [
            body("Run the VM preparation script as root. It installs the NVIDIA driver, "
                 "python3-venv, system tools, opens the firewall port, and reboots:"),
            code_block(["sudo bash prepare_vm.sh"]),
            body("After the reboot, SSH back in and verify:"),
            code_block([
                "nvidia-smi                          # GPU should appear",
                "python3 -c 'import ensurepip; print(\"ok\")'  # should print ok",
            ]),
        ]),
    ]))
    story.append(sp(8))

    story.append(KeepTogether([
        step_table(2, "Run the installer", [
            code_block(["cd ~/streampet && ./install.sh"]),
            body("Creates a Python virtualenv, installs packages, downloads Piper TTS and voice model, "
                 "installs Ollama, and pulls llama3.2 (~2 GB). Expected output:"),
            code_block([
                "[✓] pip ready",
                "[✓] venv ready (.venv/)",
                "[✓] Python packages installed",
                "[✓] Piper binary downloaded",
                "[✓] Voice model downloaded",
                "[✓] Ollama installed",
                "[✓] llama3.2 pulled",
                "[!] .env created from .env.example — EDIT IT before starting!",
            ]),
        ]),
    ]))
    story.append(sp(8))

    story.append(KeepTogether([
        step_table(3, "Register your Twitch app and fill in .env", [
            body("Register a developer app at dev.twitch.tv/console (see Section 4 for full details), "
                 "then edit .env with the credentials:"),
            code_block(["nano .env"]),
            body("Set these five values — leave TWITCH_TOKEN blank for now (step 4 fills it in):"),
            code_block([
                "TWITCH_CLIENT_ID=your_client_id_from_dev_console",
                "TWITCH_CLIENT_SECRET=your_client_secret_from_dev_console",
                "TWITCH_USERNAME=your_bot_account_username",
                "TWITCH_CHANNEL=your_stream_channel_name",
            ]),
        ]),
    ]))
    story.append(sp(8))

    story.append(KeepTogether([
        step_table(4, "Generate your Twitch token", [
            body("Run the built-in OAuth helper. It detects SSH automatically and walks you through "
                 "the authorisation flow, then writes TWITCH_TOKEN into .env:"),
            code_block(["python3 get_token.py"]),
            body("See Section 4 and Section 10.2 for detailed instructions including the SSH "
                 "port-forwarding and paste-URL options."),
        ]),
    ]))
    story.append(sp(8))

    story.append(KeepTogether([
        step_table(5, "Add your pet images", [
            body("Drop two PNG files into the static/ folder:"),
            bullet("static/pet_idle.png — your pet with mouth closed"),
            bullet("static/pet_talk.png — your pet with mouth open"),
            body("From your local machine:  scp pet_idle.png pet_talk.png user@vm-ip:~/streampet/static/"),
            body("Placeholder pink rectangles are generated automatically if you skip this step."),
        ]),
    ]))
    story.append(sp(8))

    story.append(KeepTogether([
        step_table(6, "Install as a persistent system service", [
            body("This makes StreamPet start automatically at every boot with no SSH session required:"),
            code_block(["sudo bash setup_service.sh"]),
            body("Or to run manually for testing:"),
            code_block(["./start.sh"]),
        ]),
    ]))
    story.append(sp(8))

    story.append(KeepTogether([
        step_table(7, "Add OBS Browser Source", [
            body("In OBS: Sources → + → Browser Source"),
            bullet("URL: http://<your-vm-LAN-ip>:8765   (not localhost — see Section 9)"),
            bullet("Enable: Control audio via OBS"),
        ]),
    ]))
    story.append(PageBreak())
    return story


def section_twitch():
    story = [h1("4. Twitch Credentials"), hr()]
    story.append(body(
        "StreamPet needs a Twitch account to read chat. We strongly recommend creating a dedicated "
        "bot account (e.g. MyStreamPetBot) so your main account stays separate."
    ))
    story.append(sp(10))

    story.append(callout(
        "twitchapps.com/tmi/ has been discontinued",
        [
            "The third-party TMI token generator no longer works. StreamPet includes a "
            "built-in token helper (get_token.py) that handles the official Twitch OAuth "
            "flow entirely on your local machine — no third-party websites required.",
        ],
        kind="warn"
    ))
    story.append(sp(10))

    story.append(h2("4.1 Create a Bot Account (Recommended)"))
    for t in [
        "Go to https://www.twitch.tv and sign out of your main account.",
        "Create a new Twitch account — e.g. YourChannelPet or StreamPetBot.",
        "This account does not need to stream; it is used only for chat.",
    ]:
        story.append(bullet(t))
    story.append(sp(8))

    story.append(h2("4.2 Register a Twitch Developer Application"))
    story.append(body(
        "Twitch now requires every chat bot to be registered as a developer app. "
        "This is free and takes about two minutes."
    ))
    story.append(sp(6))
    for i, step in enumerate([
        "Log in to https://dev.twitch.tv/console  as your BOT account (not your main).",
        "Click Register Your Application.",
        "Fill in the form:",
        "  Name: StreamPet  (or any name you like)",
        "  OAuth Redirect URL: http://localhost:17563   ← exactly as written",
        "  Category: Chat Bot",
        "Click Create, then click Manage on the app you just created.",
        "Copy the Client ID — paste it into .env as TWITCH_CLIENT_ID=...",
        "Click New Secret, copy it — paste into .env as TWITCH_CLIENT_SECRET=...",
    ], start=1):
        story.append(bullet(f"<b>{i}.</b> {step}" if not step.startswith(" ") else step))
    story.append(sp(10))

    story.append(h2("4.3 Generate the Token with get_token.py"))
    story.append(body(
        "Once Client ID and Client Secret are in .env, run the included helper script. "
        "It uses only Python standard library — no extra packages needed."
    ))
    story.append(code_block(["python3 get_token.py"]))
    story.append(body("The script will:"))
    for t in [
        "Open your browser to the official Twitch OAuth authorisation page.",
        "Ask you to log in as your BOT account and click Authorise.",
        "Catch the redirect on http://localhost:17563 (no internet exposure).",
        "Exchange the code for a User Access Token via the Twitch API.",
        "Write TWITCH_TOKEN=oauth:... directly into your .env file.",
    ]:
        story.append(bullet(t))
    story.append(sp(8))

    story.append(callout(
        "Keep your credentials secret",
        [
            "Never commit .env to Git or share it. The Client Secret and access token "
            "are equivalent to passwords. If compromised, delete the app at "
            "dev.twitch.tv/console and create a new one, then re-run get_token.py.",
        ],
        kind="warn"
    ))
    story.append(sp(10))

    story.append(h2("4.4 Mod the Bot in Your Channel (Recommended)"))
    story.append(body(
        "Modding the bot prevents Twitch rate-limiting its chat messages. "
        "In your channel chat, type:"
    ))
    story.append(code_block(["/mod YourBotUsername"]))
    story.append(sp(10))

    story.append(h2("4.5 .env Values for Twitch"))
    rows = [
        [Paragraph("Variable", ST["table_h"]), Paragraph("Example", ST["table_h"]),
         Paragraph("Description", ST["table_h"])],
        [Paragraph("TWITCH_CLIENT_ID", ST["table_c"]),
         Paragraph("abc123def456...", ST["table_code"]),
         Paragraph("App Client ID from dev.twitch.tv/console", ST["table_c"])],
        [Paragraph("TWITCH_CLIENT_SECRET", ST["table_c"]),
         Paragraph("xyz789...", ST["table_code"]),
         Paragraph("App Client Secret (keep private)", ST["table_c"])],
        [Paragraph("TWITCH_TOKEN", ST["table_c"]),
         Paragraph("oauth:abc123...", ST["table_code"]),
         Paragraph("Written automatically by get_token.py", ST["table_c"])],
        [Paragraph("TWITCH_USERNAME", ST["table_c"]),
         Paragraph("StreamPetBot", ST["table_code"]),
         Paragraph("Bot account Twitch username (lowercase)", ST["table_c"])],
        [Paragraph("TWITCH_CHANNEL", ST["table_c"]),
         Paragraph("yourchannel", ST["table_code"]),
         Paragraph("Your stream channel name (no #, lowercase)", ST["table_c"])],
    ]
    tbl = Table(rows, colWidths=[4.5*cm, 3.5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(PageBreak())
    return story


def section_env():
    story = [h1("5. Environment Configuration (.env)"), hr()]
    story.append(body(
        "All runtime settings live in the .env file in the project root. "
        "Copy .env.example to .env and edit it. The table below documents every available variable."
    ))
    story.append(sp(10))

    groups = [
        ("Twitch", [
            ("TWITCH_CLIENT_ID",     "abc123...",       "App Client ID from dev.twitch.tv/console"),
            ("TWITCH_CLIENT_SECRET", "xyz789...",       "App Client Secret from dev.twitch.tv/console"),
            ("TWITCH_TOKEN",         "oauth:...",       "User Access Token — written by get_token.py"),
            ("TWITCH_USERNAME",      "StreamPetBot",    "Bot Twitch username (lowercase)"),
            ("TWITCH_CHANNEL",       "yourchannel",     "Your channel name, no # sign"),
        ]),
        ("LLM — Ollama", [
            ("OLLAMA_URL",   "http://localhost:11434", "Ollama API base URL"),
            ("OLLAMA_MODEL", "llama3.2",               "Model name (must be pulled via ollama pull)"),
            ("MAX_TOKENS",   "150",                    "Max reply length in tokens (~75 words)"),
        ]),
        ("Pet Personality", [
            ("PET_NAME",        "Pixel",    "Pet's name used in LLM system prompt and chat"),
            ("PET_PERSONALITY", "...",      "Full personality prompt injected into every LLM call"),
        ]),
        ("TTS — Piper", [
            ("PIPER_BINARY", "./piper/piper",              "Path to Piper executable"),
            ("PIPER_MODEL",  "./piper/en_US-amy-medium.onnx", "Path to .onnx voice model"),
        ]),
        ("Server", [
            ("SERVER_HOST", "0.0.0.0", "Bind address (0.0.0.0 = all interfaces)"),
            ("SERVER_PORT", "8765",    "HTTP port for browser source and WebSocket"),
        ]),
        ("Behaviour", [
            ("COOLDOWN_SECONDS", "15", "Per-user cooldown between !ask commands"),
        ]),
    ]

    for group_name, vars_ in groups:
        story.append(h2(group_name))
        rows = [
            [Paragraph("Variable", ST["table_h"]),
             Paragraph("Default", ST["table_h"]),
             Paragraph("Description", ST["table_h"])],
        ]
        for var, default, desc in vars_:
            rows.append([
                Paragraph(var, ST["table_code"]),
                Paragraph(default, ST["table_code"]),
                Paragraph(desc, ST["table_c"]),
            ])
        tbl = Table(rows, colWidths=[5*cm, 4.5*cm, None])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PINK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
            ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(sp(8))

    story.append(PageBreak())
    return story


def section_llm():
    story = [h1("6. LLM Configuration (Ollama)"), hr()]
    story.append(body(
        "StreamPet uses Ollama to run large language models locally. "
        "The RTX 3060 12 GB VRAM is enough for 7B parameter models like llama3.2, "
        "mistral, or gemma2 at full GPU speed."
    ))
    story.append(sp(10))

    story.append(h2("6.1 Checking Ollama"))
    story.append(code_block([
        "ollama list          # see pulled models",
        "ollama ps            # see what is currently loaded",
        "curl http://localhost:11434/api/tags    # confirm API is up",
    ]))
    story.append(sp(8))

    story.append(h2("6.2 Pulling Alternative Models"))
    rows = [
        [Paragraph("Model", ST["table_h"]), Paragraph("VRAM", ST["table_h"]),
         Paragraph("Quality", ST["table_h"]), Paragraph("Pull command", ST["table_h"])],
        [Paragraph("llama3.2 (default)", ST["table_c"]), Paragraph("~4 GB", ST["table_c"]),
         Paragraph("Excellent", ST["table_c"]), Paragraph("ollama pull llama3.2", ST["table_code"])],
        [Paragraph("mistral", ST["table_c"]), Paragraph("~4 GB", ST["table_c"]),
         Paragraph("Very good", ST["table_c"]), Paragraph("ollama pull mistral", ST["table_code"])],
        [Paragraph("gemma2:9b", ST["table_c"]), Paragraph("~6 GB", ST["table_c"]),
         Paragraph("Excellent", ST["table_c"]), Paragraph("ollama pull gemma2:9b", ST["table_code"])],
        [Paragraph("llama3.1:8b", ST["table_c"]), Paragraph("~5 GB", ST["table_c"]),
         Paragraph("Excellent", ST["table_c"]), Paragraph("ollama pull llama3.1:8b", ST["table_code"])],
        [Paragraph("phi3:mini", ST["table_c"]), Paragraph("~2.5 GB", ST["table_c"]),
         Paragraph("Good / fast", ST["table_c"]), Paragraph("ollama pull phi3:mini", ST["table_code"])],
    ]
    tbl = Table(rows, colWidths=[4.5*cm, 2.2*cm, 3*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(8))

    story.append(body("After pulling a new model, update OLLAMA_MODEL in .env and restart."))
    story.append(sp(10))

    story.append(h2("6.3 Customising the Personality Prompt"))
    story.append(body(
        "The system prompt is built in llm.py from the PET_NAME and PET_PERSONALITY env vars. "
        "To change it, edit .env:"
    ))
    story.append(code_block([
        'PET_NAME=Blaze',
        'PET_PERSONALITY=You are a sarcastic but loveable gamer cat. Keep answers under 2 sentences.',
    ]))
    story.append(sp(10))

    story.append(callout(
        "Response Length Tip",
        [
            "Keep MAX_TOKENS between 80–200 for stream use. Very long replies make TTS slow "
            "and viewers lose interest. The default of 150 (~75 words) is a good balance.",
        ],
        kind="info"
    ))
    story.append(PageBreak())
    return story


def section_tts():
    story = [h1("7. TTS Configuration (Piper)"), hr()]
    story.append(body(
        "Piper TTS is a fast, self-hosted neural text-to-speech system. It runs as a standalone "
        "binary and requires no GPU — leaving your RTX 3060 fully available to Ollama. "
        "Audio is generated in real-time (typically under 1 second for short replies)."
    ))
    story.append(sp(10))

    story.append(h2("7.1 Voice Models"))
    story.append(body(
        "Piper voices are distributed as .onnx files paired with a .onnx.json config. "
        "The default voice installed is en_US-amy-medium. To change voices:"
    ))
    story.append(sp(6))
    story.append(body("<b>Step 1</b> — Browse available voices at:"))
    story.append(code_block(["https://huggingface.co/rhasspy/piper-voices"]))
    story.append(body("<b>Step 2</b> — Download the .onnx and .onnx.json files into the piper/ folder:"))
    story.append(code_block([
        "cd ~/streampet/piper",
        "curl -L https://huggingface.co/rhasspy/piper-voices/resolve/main/",
        "     en/en_US/lessac/medium/en_US-lessac-medium.onnx -o en_US-lessac-medium.onnx",
        "curl -L https://huggingface.co/rhasspy/piper-voices/resolve/main/",
        "     en/en_US/lessac/medium/en_US-lessac-medium.onnx.json -o en_US-lessac-medium.onnx.json",
    ]))
    story.append(body("<b>Step 3</b> — Update .env:"))
    story.append(code_block(["PIPER_MODEL=./piper/en_US-lessac-medium.onnx"]))
    story.append(sp(10))

    story.append(h2("7.2 Popular Voice Options"))
    rows = [
        [Paragraph("Voice ID", ST["table_h"]), Paragraph("Gender", ST["table_h"]),
         Paragraph("Quality", ST["table_h"]), Paragraph("Notes", ST["table_h"])],
        [Paragraph("en_US-amy-medium", ST["table_code"]), Paragraph("F", ST["table_c"]),
         Paragraph("Medium", ST["table_c"]), Paragraph("Default — fast, clear", ST["table_c"])],
        [Paragraph("en_US-lessac-medium", ST["table_code"]), Paragraph("M", ST["table_c"]),
         Paragraph("Medium", ST["table_c"]), Paragraph("Natural male voice", ST["table_c"])],
        [Paragraph("en_US-libritts-high", ST["table_code"]), Paragraph("F/M", ST["table_c"]),
         Paragraph("High", ST["table_c"]), Paragraph("Best quality, slightly slower", ST["table_c"])],
        [Paragraph("en_GB-alba-medium", ST["table_code"]), Paragraph("F", ST["table_c"]),
         Paragraph("Medium", ST["table_c"]), Paragraph("British English accent", ST["table_c"])],
    ]
    tbl = Table(rows, colWidths=[6*cm, 1.8*cm, 2.2*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(10))

    story.append(h2("7.3 Testing TTS Manually"))
    story.append(code_block([
        'echo "Hello from StreamPet!" | ./piper/piper \\',
        '  --model ./piper/en_US-amy-medium.onnx \\',
        '  --output_file /tmp/test.wav',
        "",
        "# Play it back",
        "aplay /tmp/test.wav    # or: paplay, mpv, ffplay",
    ]))
    story.append(sp(10))

    story.append(callout(
        "Audio Cleanup",
        [
            "Generated WAV files are automatically deleted after 5 minutes (300 seconds). "
            "This prevents the static/audio/ folder from filling up disk space during long streams. "
            "The cleanup interval is hardcoded in tts.py and can be changed there.",
        ],
        kind="info"
    ))
    story.append(PageBreak())
    return story


def section_artwork():
    story = [h1("8. Pet Artwork"), hr()]
    story.append(body(
        "StreamPet uses two PNG image files to animate the pet. The browser source swaps between "
        "them at 150 ms intervals while TTS audio plays, creating a talking animation."
    ))
    story.append(sp(10))

    story.append(h2("8.1 Required Files"))
    rows = [
        [Paragraph("File", ST["table_h"]), Paragraph("State", ST["table_h"]),
         Paragraph("When used", ST["table_h"])],
        [Paragraph("static/pet_idle.png", ST["table_code"]),
         Paragraph("Mouth closed / default pose", ST["table_c"]),
         Paragraph("All times except when speaking", ST["table_c"])],
        [Paragraph("static/pet_talk.png", ST["table_code"]),
         Paragraph("Mouth open", ST["table_c"]),
         Paragraph("Alternates with idle during TTS playback", ST["table_c"])],
    ]
    tbl = Table(rows, colWidths=[5*cm, 5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(10))

    story.append(h2("8.2 Artwork Recommendations"))
    for tip in [
        "PNG with transparent background works best as an OBS overlay.",
        "Recommended canvas size: 300 x 400 px or 400 x 500 px.",
        "The pet image width is set to 300px in CSS — edit static/style.css line image-rendering to change.",
        "Keep both images the same canvas size so the swap is seamless.",
        "You can use pixel art, illustrated characters, or even a VTuber-style chibi.",
        "Tools: Aseprite (pixel art), GIMP, Krita, or Procreate (export as PNG).",
    ]:
        story.append(bullet(tip))
    story.append(sp(10))

    story.append(h2("8.3 Changing Image Size in OBS"))
    story.append(body(
        "By default the image renders at 300px wide. To override this via OBS Custom CSS "
        "in the Browser Source properties:"
    ))
    story.append(code_block([
        "#pet-img {",
        "  width: 400px;     /* change to your preferred size */",
        "}",
        "#scene {",
        "  width: 500px;     /* scene container width */",
        "  height: 500px;",
        "}",
    ]))
    story.append(sp(10))

    story.append(h2("8.4 Talk Frame Speed"))
    story.append(body(
        "The mouth alternates every 150 ms by default. To change this, edit static/pet.js:"
    ))
    story.append(code_block(["const TALK_FRAME_MS = 150;  // line 17 — change to 100 for faster"]))
    story.append(sp(10))

    story.append(callout(
        "Placeholder Images",
        [
            "run make_placeholders.py to regenerate the solid-colour placeholder PNGs at any time. "
            "These are safe to delete once you have your own artwork in place.",
        ],
        kind="ok"
    ))
    story.append(PageBreak())
    return story


def section_obs():
    story = [h1("9. OBS Setup"), hr()]
    story.append(body(
        "StreamPet displays as a Browser Source in OBS Studio. The browser source both renders "
        "the pet animation and plays the TTS audio through OBS's audio mixer. "
        "Because the Linux VM is headless, OBS runs on your streaming PC and connects "
        "to the VM over your local network — not via localhost."
    ))
    story.append(sp(10))

    story.append(h2("9.1 Find the VM's LAN IP Address"))
    story.append(body("Run this on the VM (over SSH) before setting up OBS:"))
    story.append(code_block([
        "hostname -I | awk '{print $1}'",
        "# example output: 192.168.1.42",
    ]))
    story.append(body(
        "This is the IP address you will use in the OBS Browser Source URL. "
        "For a stable setup, assign a static IP or DHCP reservation to the VM in your router."
    ))
    story.append(sp(10))

    story.append(h2("9.2 Open Port 8765 on the VM Firewall"))
    story.append(body("If the VM has a firewall active (ufw), allow the StreamPet port:"))
    story.append(code_block([
        "sudo ufw allow 8765/tcp",
        "sudo ufw status    # confirm rule is listed",
    ]))
    story.append(body("Verify StreamPet is reachable from your streaming PC:"))
    story.append(code_block(["curl http://<VM-IP>:8765/health"]))
    story.append(sp(10))

    story.append(h2("9.3 Adding the Browser Source in OBS"))
    for i, step in enumerate([
        "In OBS, click the + button in the Sources panel.",
        "Select Browser from the source type list.",
        "Name it StreamPet (or any name you prefer).",
        "In the URL field enter: http://<VM-IP>:8765   (use actual IP, not localhost)",
        "Set Width and Height to match your pet PNG canvas size (e.g. 420 x 420).",
        "Check the box: Control audio via OBS — this is required for TTS to play.",
        "Leave all other settings at their defaults and click OK.",
        "Drag and reposition the source in your scene as needed.",
    ], start=1):
        story.append(bullet(f"<b>{i}.</b> {step}"))
    story.append(sp(10))

    story.append(callout(
        "Use VM IP, not localhost",
        [
            "localhost in the Browser Source URL refers to your streaming PC, not the VM. "
            "The browser source will load a blank page if you use localhost. "
            "Always use the VM's actual LAN IP address, e.g. http://192.168.1.42:8765",
        ],
        kind="warn"
    ))
    story.append(sp(8))

    story.append(callout(
        "Control audio via OBS — Required",
        [
            "Without this checkbox the browser source runs in a sandboxed audio context "
            "that OBS cannot capture. TTS audio will not be heard on stream. "
            "Always enable this option.",
        ],
        kind="warn"
    ))
    story.append(sp(10))

    story.append(h2("9.4 Audio Routing"))
    story.append(body(
        "Once Control audio via OBS is enabled, a new audio track called Browser appears "
        "in the OBS Audio Mixer. You can:"
    ))
    for tip in [
        "Adjust pet volume independently of your mic or desktop audio.",
        "Add filters (e.g. compressor, noise gate) to the pet audio track.",
        "Route pet audio to a specific output track for recording vs. streaming.",
    ]:
        story.append(bullet(tip))
    story.append(sp(10))

    story.append(h2("9.5 Transparent Background"))
    story.append(body(
        "The browser source has a transparent background by default. "
        "This lets the pet float over your scene. Do not add a background colour "
        "in OBS Browser Source settings — leave it at default."
    ))
    story.append(sp(10))

    story.append(h2("9.6 Recommended OBS Scene Setup"))
    rows = [
        [Paragraph("Source", ST["table_h"]), Paragraph("Type", ST["table_h"]),
         Paragraph("Notes", ST["table_h"])],
        [Paragraph("StreamPet", ST["table_c"]), Paragraph("Browser", ST["table_c"]),
         Paragraph("http://192.168.x.x:8765 — Control audio via OBS enabled", ST["table_c"])],
        [Paragraph("Webcam", ST["table_c"]), Paragraph("Video Capture", ST["table_c"]),
         Paragraph("Place behind or beside the pet", ST["table_c"])],
        [Paragraph("Game Capture", ST["table_c"]), Paragraph("Game/Window Capture", ST["table_c"]),
         Paragraph("Bottom layer", ST["table_c"])],
        [Paragraph("Chat Overlay", ST["table_c"]), Paragraph("Browser", ST["table_c"]),
         Paragraph("Optional — shows alongside the pet", ST["table_c"])],
    ]
    tbl = Table(rows, colWidths=[4*cm, 3.5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(PageBreak())
    return story


def section_ssh():
    story = [h1("10. SSH & Headless Operation"), hr()]
    story.append(body(
        "The Linux VM is headless — it has no monitor, keyboard, or desktop environment. "
        "All day-to-day operation is done over SSH from your Windows or Mac machine. "
        "This section covers every situation where the headless environment requires special handling."
    ))
    story.append(sp(10))

    story.append(h2("10.1 What Works Normally Over SSH"))
    rows = [
        [Paragraph("Component", ST["table_h"]), Paragraph("SSH compatible?", ST["table_h"]),
         Paragraph("Notes", ST["table_h"])],
        [Paragraph("install.sh", ST["table_c"]), Paragraph("Yes", ST["table_c"]),
         Paragraph("Runs entirely in the terminal", ST["table_c"])],
        [Paragraph("start.sh / main.py", ST["table_c"]), Paragraph("Yes", ST["table_c"]),
         Paragraph("Terminal process, no display needed", ST["table_c"])],
        [Paragraph("Ollama daemon", ST["table_c"]), Paragraph("Yes", ST["table_c"]),
         Paragraph("Background service, no display needed", ST["table_c"])],
        [Paragraph("Piper TTS", ST["table_c"]), Paragraph("Yes", ST["table_c"]),
         Paragraph("Subprocess, writes WAV to disk", ST["table_c"])],
        [Paragraph("Twitch bot", ST["table_c"]), Paragraph("Yes", ST["table_c"]),
         Paragraph("Network connection to Twitch only", ST["table_c"])],
        [Paragraph("FastAPI server", ST["table_c"]), Paragraph("Yes", ST["table_c"]),
         Paragraph("Binds 0.0.0.0 — reachable from OBS over LAN", ST["table_c"])],
        [Paragraph("get_token.py", ST["table_c"]), Paragraph("Yes — see below", ST["table_c"]),
         Paragraph("Auto-detects SSH; uses paste or tunnel method", ST["table_c"])],
    ]
    tbl = Table(rows, colWidths=[4.5*cm, 3.5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(10))

    story.append(h2("10.2 Getting the Twitch Token Over SSH"))
    story.append(body(
        "get_token.py detects SSH sessions automatically and switches to headless mode. "
        "It offers two options:"
    ))
    story.append(sp(8))

    story.append(h3("Option A — SSH Port Forwarding (Recommended)"))
    story.append(body(
        "Open a second terminal on your LOCAL machine (not the VM) and run:"
    ))
    story.append(code_block([
        "ssh -L 17563:localhost:17563 your-user@192.168.x.x",
        "# Keep this terminal open",
    ]))
    story.append(body(
        "Then run get_token.py on the VM. Copy the URL it prints, open it in your local "
        "browser, and log in as your bot account. Twitch redirects to "
        "http://localhost:17563 — the SSH tunnel forwards that request to the VM. "
        "The token is captured and saved automatically."
    ))
    story.append(sp(8))

    story.append(h3("Option B — Paste the Redirect URL (No Extra Setup)"))
    story.append(body(
        "If you cannot or do not want to use port forwarding:"
    ))
    for i, step in enumerate([
        "Run python3 get_token.py on the VM — copy the auth URL it prints.",
        "Open that URL in any browser on any machine.",
        "Log in as your bot account and click Authorise.",
        "Your browser will try to open http://localhost:17563/?code=... and show an error — this is expected.",
        "Copy the full URL from your browser's address bar (the one showing the error).",
        "Paste it into the get_token.py terminal prompt and press Enter.",
        "The token is extracted, exchanged, and saved to .env automatically.",
    ], start=1):
        story.append(bullet(f"<b>{i}.</b> {step}"))
    story.append(sp(10))

    story.append(h2("10.3 Keeping StreamPet Running After SSH Disconnect"))
    story.append(body(
        "If you start StreamPet in a plain SSH terminal, it will stop when you disconnect. "
        "The recommended approach is the system-level systemd service installed by setup_service.sh."
    ))
    story.append(sp(6))

    story.append(h3("Recommended: system service (starts at every boot, no login needed)"))
    story.append(code_block([
        "sudo bash setup_service.sh",
        "",
        "# Management:",
        "sudo systemctl status streampet",
        "sudo journalctl -u streampet -f   # live logs over SSH",
        "sudo systemctl restart streampet  # after .env changes",
        "sudo systemctl stop streampet",
    ]))
    story.append(body(
        "This is a system-level service (/etc/systemd/system/streampet.service), not a user service. "
        "It starts during boot before any login — no SSH session required."
    ))
    story.append(sp(8))

    story.append(h3("Alternative: tmux (useful during development/testing)"))
    story.append(code_block([
        "tmux new -s streampet    # create a named session",
        "./start.sh               # start inside tmux",
        "# Ctrl+B then D to detach — StreamPet keeps running",
        "",
        "tmux attach -t streampet # reattach later",
    ]))
    story.append(sp(10))

    story.append(callout(
        "System service vs user service — which to use",
        [
            "setup_service.sh installs a system-level service that starts at boot with no login. "
            "A user-level service (systemctl --user) only starts when you SSH in — avoid it for "
            "production. Use tmux only while actively developing or debugging.",
        ],
        kind="info"
    ))
    story.append(PageBreak())
    return story


def section_running():
    story = [h1("11. Running StreamPet"), hr()]

    story.append(body(
        "StreamPet is designed to run as a persistent system service — "
        "it starts automatically at every boot and restarts itself if it crashes, "
        "with no SSH session or manual intervention required."
    ))
    story.append(sp(8))

    story.append(callout(
        "Recommended: always use the system service",
        [
            "The systemd system service is the correct way to run StreamPet in production. "
            "It starts before any user logs in, survives SSH disconnects, and recovers from crashes. "
            "Manual start via start.sh is only for development and testing.",
        ],
        kind="ok"
    ))
    story.append(sp(10))

    story.append(h2("11.1 Install the System Service (Once)"))
    story.append(body(
        "After completing install.sh, get_token.py, and dropping in your pet artwork, "
        "run the service installer script. This requires sudo once only:"
    ))
    story.append(code_block(["sudo bash setup_service.sh"]))
    story.append(body("The script will:"))
    for s_ in [
        "Write /etc/systemd/system/streampet.service (system-level, not user-level).",
        "Enable the service so it starts automatically at every boot.",
        "Start it immediately — StreamPet is live within seconds.",
        "Print the OBS Browser Source URL with the VM's actual LAN IP.",
        "Run a pre-flight check: refuses to install if TWITCH_TOKEN or TWITCH_CHANNEL are still placeholders.",
    ]:
        story.append(bullet(s_))
    story.append(sp(10))

    story.append(callout(
        "System service vs user service — why it matters",
        [
            "A user-level service (systemctl --user) only starts when the user logs in. "
            "On a headless VM this means it never starts unless you SSH in. "
            "A system-level service (/etc/systemd/system/) starts during boot before any "
            "login — which is what we want.",
        ],
        kind="info"
    ))
    story.append(sp(10))

    story.append(h2("11.2 Day-to-Day Service Management"))
    rows = [
        [Paragraph("Task", ST["table_h"]), Paragraph("Command", ST["table_h"])],
        [Paragraph("Check status", ST["table_c"]),
         Paragraph("sudo systemctl status streampet", ST["table_code"])],
        [Paragraph("Follow live logs", ST["table_c"]),
         Paragraph("sudo journalctl -u streampet -f", ST["table_code"])],
        [Paragraph("Restart (e.g. after .env edit)", ST["table_c"]),
         Paragraph("sudo systemctl restart streampet", ST["table_code"])],
        [Paragraph("Stop", ST["table_c"]),
         Paragraph("sudo systemctl stop streampet", ST["table_code"])],
        [Paragraph("Start (if stopped)", ST["table_c"]),
         Paragraph("sudo systemctl start streampet", ST["table_code"])],
        [Paragraph("Disable autostart", ST["table_c"]),
         Paragraph("sudo systemctl disable streampet", ST["table_code"])],
        [Paragraph("Remove service entirely", ST["table_c"]),
         Paragraph("sudo bash remove_service.sh", ST["table_code"])],
    ]
    tbl = Table(rows, colWidths=[5.5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(sp(10))

    story.append(h2("11.3 Updating Configuration"))
    story.append(body(
        "Any time you edit .env (change model, personality, cooldown, etc.), "
        "restart the service to apply the change:"
    ))
    story.append(code_block([
        "nano ~/streampet/.env",
        "sudo systemctl restart streampet",
        "sudo journalctl -u streampet -f    # confirm it started cleanly",
    ]))
    story.append(sp(10))

    story.append(h2("11.4 What the Service Unit Looks Like"))
    story.append(body("The installed unit file at /etc/systemd/system/streampet.service:"))
    story.append(code_block([
        "[Unit]",
        "Description=StreamPet — Self-Hosted Twitch Stream Pet",
        "After=network-online.target ollama.service",
        "Wants=network-online.target ollama.service",
        "",
        "[Service]",
        "Type=simple",
        "User=<your-username>",
        "WorkingDirectory=/home/<your-username>/streampet",
        "EnvironmentFile=/home/<your-username>/streampet/.env",
        "ExecStart=/home/<your-username>/streampet/.venv/bin/python3 main.py",
        "Restart=always",
        "RestartSec=10",
        "StartLimitBurst=5",
        "StandardOutput=journal",
        "",
        "[Install]",
        "WantedBy=multi-user.target",
    ]))
    story.append(sp(10))

    story.append(h2("11.5 Manual Start (Development Only)"))
    story.append(body(
        "If the system service is running, start.sh will detect it and show service status "
        "instead of launching a second instance. To run manually for debugging, "
        "stop the service first:"
    ))
    story.append(code_block([
        "sudo systemctl stop streampet",
        "cd ~/streampet && ./start.sh",
        "",
        "# Re-enable the service when done:",
        "sudo systemctl start streampet",
    ]))
    story.append(sp(10))

    story.append(h2("11.6 Expected Log Output"))
    story.append(code_block([
        "$ sudo journalctl -u streampet -f",
        "",
        "[*] Starting StreamPet",
        "    Pet name  : Pixel",
        "    Channel   : #yourchannel",
        "    LLM model : llama3.2",
        "INFO:     Uvicorn running on http://0.0.0.0:8765",
        "[Bot] Connected as StreamPetBot | Channel: #yourchannel",
        "[WS] Client connected (1 total)",
    ]))
    story.append(PageBreak())
    return story


def section_customisation():
    story = [h1("12. Customisation"), hr()]

    story.append(h2("12.1 Personality and Prompt"))
    story.append(body(
        "The LLM system prompt is assembled in llm.py from your .env values. "
        "To give your pet a distinct voice, edit PET_PERSONALITY in .env. Examples:"
    ))
    story.append(code_block([
        "# Snarky gamer cat",
        'PET_PERSONALITY=You are a sarcastic gamer cat who loves roasting viewers (gently). Keep it under 2 sentences.',
        "",
        "# Wise wizard owl",
        'PET_PERSONALITY=You are an ancient wise owl who speaks in riddles and metaphors. One sentence answers only.',
        "",
        "# Cheerful corgi",
        'PET_PERSONALITY=You are an enthusiastic golden corgi who LOVES everything. Bark once in every reply.',
    ]))
    story.append(sp(10))

    story.append(h2("12.2 Cooldown"))
    story.append(body(
        "COOLDOWN_SECONDS in .env controls how long each viewer must wait between !ask uses. "
        "Set it lower (5–10s) for very active chats, higher (30–60s) for slower ones. "
        "The default is 15 seconds."
    ))
    story.append(sp(10))

    story.append(h2("12.3 Speech Bubble Style"))
    story.append(body("Edit static/style.css to change bubble appearance:"))
    story.append(code_block([
        "#bubble {",
        "  border: 3px solid #f472b6;    /* border colour */",
        "  border-radius: 20px;           /* roundness */",
        "  background: rgba(255,255,255,0.95);",
        "  box-shadow: 0 4px 20px rgba(244,114,182,0.45);",
        "}",
        "#bubble-username { color: #db2777; }   /* username colour */",
        "#bubble-text { font-size: 14px; }      /* text size */",
    ]))
    story.append(sp(10))

    story.append(h2("12.4 Bubble Linger Time"))
    story.append(body(
        "After TTS finishes, the speech bubble stays visible for 4 seconds before fading. "
        "Change this in static/pet.js:"
    ))
    story.append(code_block(["const BUBBLE_LINGER_MS = 4000;  // line 18"]))
    story.append(sp(10))

    story.append(h2("12.5 Adding More Commands"))
    story.append(body(
        "To add new bot commands, edit bot.py and add methods decorated with @commands.command(). Example:"
    ))
    story.append(code_block([
        "@commands.command(name='pet')",
        "async def pet_command(self, ctx: commands.Context):",
        "    await ctx.send(f'*{cfg.PET_NAME} purrs contentedly* uwu')",
    ]))
    story.append(PageBreak())
    return story


def section_troubleshooting():
    story = [h1("13. Troubleshooting"), hr()]

    issues = [
        (
            "Service fails to start / crashes at boot",
            [
                "Check the journal for error details: sudo journalctl -u streampet -xe",
                "Most common cause: TWITCH_TOKEN expired. Re-run python3 get_token.py, then sudo systemctl restart streampet.",
                "Check Ollama is running: sudo systemctl status ollama",
                "Verify .env paths: PIPER_BINARY and PIPER_MODEL must be absolute or relative to your streampet/ directory.",
                "If the venv was deleted, re-run ./install.sh then sudo bash setup_service.sh again.",
            ]
        ),
        (
            "OBS Browser Source shows blank / cannot connect",
            [
                "This usually means localhost was used in the URL instead of the VM's LAN IP.",
                "Fix: right-click the source → Properties → change URL to http://192.168.x.x:8765",
                "Find the VM IP: run  hostname -I | awk '{print $1}'  on the VM over SSH.",
                "Confirm StreamPet is running: curl http://<VM-IP>:8765/health",
                "If curl fails from another machine, open port 8765: sudo ufw allow 8765/tcp",
            ]
        ),
        (
            "get_token.py — browser won't open / no callback",
            [
                "On a headless VM this is expected — the script detects SSH and switches to manual mode.",
                "Option A: open a second terminal on your LOCAL machine and run: ssh -L 17563:localhost:17563 user@<VM-IP>  then visit the printed URL in your browser.",
                "Option B: visit the auth URL in any browser, authorise, then copy the redirect URL from the address bar (even if it shows a connection error) and paste it at the prompt.",
            ]
        ),
        (
            "Bot connects but !ask does nothing",
            [
                "Check that the bot account is joined to the right channel (TWITCH_CHANNEL in .env).",
                "Verify the bot has not been banned or timed out in your channel.",
                "Check the terminal for [LLM] or [TTS] error messages.",
                "Ensure Ollama is running: curl http://localhost:11434/api/tags",
            ]
        ),
        (
            "No audio in OBS",
            [
                "The Browser Source must have Control audio via OBS checked.",
                "Right-click the Browser Source → Properties → tick the checkbox.",
                "Check that OBS Browser audio track is not muted in the Audio Mixer.",
                "Test TTS manually: echo 'test' | ./piper/piper --model ./piper/en_US-amy-medium.onnx --output_file /tmp/t.wav && aplay /tmp/t.wav",
            ]
        ),
        (
            "[TTS] Piper binary not found",
            [
                "Re-run ./install.sh — it will re-download the Piper binary.",
                "Check PIPER_BINARY in .env points to ./piper/piper.",
                "Verify: ls -la ./piper/piper  (should be executable)",
                "Manually fix: chmod +x ./piper/piper",
            ]
        ),
        (
            "[LLM] Cannot connect to Ollama",
            [
                "Start Ollama manually: ollama serve",
                "Check it is listening: curl http://localhost:11434/api/tags",
                "If OLLAMA_URL is changed from default, verify the new address.",
            ]
        ),
        (
            "OBS browser source shows blank / error",
            [
                "Confirm StreamPet is running: curl http://localhost:8765/health",
                "Check SERVER_PORT in .env matches the URL in OBS.",
                "Try refreshing the browser source: right-click → Refresh.",
                "Disable any firewall rules blocking port 8765.",
            ]
        ),
        (
            "Viewer gets cooldown message immediately",
            [
                "COOLDOWN_SECONDS applies per username, not globally.",
                "Cooldowns reset on server restart.",
                "Reduce COOLDOWN_SECONDS in .env if needed.",
            ]
        ),
        (
            "LLM responses are too slow",
            [
                "Ensure Ollama is using the GPU: ollama ps — look for GPU column.",
                "Switch to a smaller model: OLLAMA_MODEL=phi3:mini",
                "Reduce MAX_TOKENS in .env (e.g. 80).",
                "Check GPU driver: nvidia-smi — if not found, install CUDA drivers.",
            ]
        ),
        (
            "TypeError: Bot.__init__() missing 'client_id', 'client_secret', 'bot_id'",
            [
                "This means TwitchIO v3 was installed instead of v2. The APIs are incompatible.",
                "Fix: run  .venv/bin/pip install \"twitchio>=2.10.0,<3.0.0\"",
                "requirements.txt already pins twitchio<3.0.0 — this error only occurs if pip was run manually without the pin.",
                "Verify the version: .venv/bin/pip show twitchio | grep Version  (should show 2.x.x)",
            ]
        ),
        (
            "get_token.py — 'invalid client' error in browser",
            [
                "This means TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET in .env still contain placeholder values.",
                "Edit .env and replace the placeholder strings with your real credentials from dev.twitch.tv/console.",
                "The script checks for common placeholders (e.g. 'your_client_id_here') and will show a clear error if they are detected.",
            ]
        ),
    ]

    for title, steps in issues:
        story.append(KeepTogether([
            h2(title),
            *[bullet(s_) for s_ in steps],
            sp(6),
        ]))

    story.append(PageBreak())
    return story


def section_files():
    story = [h1("14. File Reference"), hr()]
    story.append(body("Every file in the project and its purpose:"))
    story.append(sp(8))

    rows = [
        [Paragraph("File", ST["table_h"]), Paragraph("Purpose", ST["table_h"])],

        [Paragraph("main.py", ST["table_code"]),
         Paragraph("Entry point. Runs FastAPI server and Twitch bot concurrently via asyncio.gather.", ST["table_c"])],
        [Paragraph("server.py", ST["table_code"]),
         Paragraph("FastAPI app: serves browser source (GET /), WebSocket (/ws), audio files, and health check.", ST["table_c"])],
        [Paragraph("bot.py", ST["table_code"]),
         Paragraph("TwitchIO bot. Handles !ask command, per-user cooldown, calls LLM and TTS, broadcasts to WebSocket.", ST["table_c"])],
        [Paragraph("llm.py", ST["table_code"]),
         Paragraph("Async Ollama client. Builds system prompt from config, sends question, returns answer text.", ST["table_c"])],
        [Paragraph("tts.py", ST["table_code"]),
         Paragraph("Piper TTS wrapper. Runs Piper as async subprocess, saves WAV to static/audio/, cleans up old files.", ST["table_c"])],
        [Paragraph("config.py", ST["table_code"]),
         Paragraph("Centralised config. Reads all settings from .env via python-dotenv.", ST["table_c"])],
        [Paragraph(".env", ST["table_code"]),
         Paragraph("Your personal configuration (Twitch credentials, model names, ports). Not committed to Git.", ST["table_c"])],
        [Paragraph(".env.example", ST["table_code"]),
         Paragraph("Template for .env. Safe to commit. Copy to .env and fill in real values.", ST["table_c"])],
        [Paragraph("requirements.txt", ST["table_code"]),
         Paragraph("Python package list: fastapi, uvicorn, twitchio (pinned &lt;3.0), httpx, python-dotenv, aiofiles, websockets.", ST["table_c"])],
        [Paragraph("install.sh", ST["table_code"]),
         Paragraph("One-shot installer: pip, venv, Python deps, Piper binary, voice model, Ollama, llama3.2.", ST["table_c"])],
        [Paragraph("start.sh", ST["table_code"]),
         Paragraph("Daily start script. Activates venv, optionally starts Ollama daemon, runs main.py.", ST["table_c"])],
        [Paragraph("get_token.py", ST["table_code"]),
         Paragraph("Self-contained Twitch OAuth helper. Reads Client ID/Secret from .env, opens browser for Twitch auth, captures the redirect on localhost:17563, and writes TWITCH_TOKEN back to .env. SSH-aware (offers paste or tunnel method). No extra packages needed.", ST["table_c"])],
        [Paragraph("setup_service.sh", ST["table_code"]),
         Paragraph("Installs StreamPet as a persistent system-level systemd service. Run once with sudo after configuration is complete. Pre-flight checks token and channel before installing.", ST["table_c"])],
        [Paragraph("remove_service.sh", ST["table_code"]),
         Paragraph("Stops, disables, and removes the systemd service unit. StreamPet files are left intact.", ST["table_c"])],
        [Paragraph("make_placeholders.py", ST["table_code"]),
         Paragraph("Generates solid-colour placeholder pet_idle.png and pet_talk.png without any dependencies.", ST["table_c"])],
        [Paragraph("static/index.html", ST["table_code"]),
         Paragraph("OBS browser source page. Contains pet &lt;img&gt; and speech bubble &lt;div&gt;.", ST["table_c"])],
        [Paragraph("static/style.css", ST["table_code"]),
         Paragraph("All CSS: bubble styling, pet image sizing, talking glow effect.", ST["table_c"])],
        [Paragraph("static/pet.js", ST["table_code"]),
         Paragraph("WebSocket client: connects to /ws, handles thinking/speak/error events, swaps PNG frames, plays audio.", ST["table_c"])],
        [Paragraph("static/pet_idle.png", ST["table_code"]),
         Paragraph("YOUR artwork — pet with mouth closed. Replace placeholder with your own PNG.", ST["table_c"])],
        [Paragraph("static/pet_talk.png", ST["table_code"]),
         Paragraph("YOUR artwork — pet with mouth open. Alternates with idle during TTS playback.", ST["table_c"])],
        [Paragraph("static/pet_placeholder.svg", ST["table_code"]),
         Paragraph("Fallback shown if pet_idle.png is missing (displayed via onerror in index.html).", ST["table_c"])],
        [Paragraph("static/audio/", ST["table_code"]),
         Paragraph("Generated TTS WAV files. Auto-cleaned after 5 minutes.", ST["table_c"])],
        [Paragraph("piper/piper", ST["table_code"]),
         Paragraph("Piper TTS binary (downloaded by install.sh from GitHub releases).", ST["table_c"])],
        [Paragraph("piper/*.onnx", ST["table_code"]),
         Paragraph("Piper ONNX voice model files. Download additional voices from Hugging Face.", ST["table_c"])],
        [Paragraph("CLAUDE.md", ST["table_code"]),
         Paragraph("Project context file read by Claude Code on folder open. Contains architecture, decisions, and task history.", ST["table_c"])],
    ]

    tbl = Table(rows, colWidths=[5.5*cm, None])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PINK_LITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, PINK_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    return story


# ── Build PDF ──────────────────────────────────────────────────────────────────

def build():
    out = "StreamPet_Setup_Guide.pdf"
    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2.5*cm,
        title="StreamPet Setup Guide",
        author="StreamPet",
        subject="Self-Hosted Twitch Stream Pet — Setup & Configuration",
    )

    story = []
    story += cover_page()
    story += toc_page()
    story += section_overview()
    story += section_prerequisites()
    story += section_installation()
    story += section_twitch()
    story += section_env()
    story += section_llm()
    story += section_tts()
    story += section_artwork()
    story += section_obs()
    story += section_ssh()
    story += section_running()
    story += section_customisation()
    story += section_troubleshooting()
    story += section_files()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"[✓] Created {out}")


if __name__ == "__main__":
    build()
