"""
Aissa Bakhil — AI/ML engineering portfolio, built with Flet 1.0.
Dev preview:   python tools/build_blogs.py && flet run --web main.py
Static build:  python tools/build_blogs.py && flet build web
Profile and project data live in the DATA block; publish articles as Markdown files in blogs/.
Full articles are generated as standalone HTML pages under assets/blog/.
"""
import inspect
import re
import sys
from pathlib import Path
import flet as ft

from blog_utils import parse_blog_post, public_post_metadata

# ---------------------------------------------------------------- design
BG, CARD, LINE = "#070B18", "#10182B", "#202B47"
INK, MUTE = "#EEF1FA", "#A4AEC8"
ACC, GOOD = "#70A5FF", "#4CD48C"
ACC_SOFT = ft.Colors.with_opacity(0.16, ACC)
MONO = "monospace"

# ------------------------------------------------------------------ data
NAME = "Aissa Bakhil"
HEADLINE = "Hi, I’m Aissa Bakhil"
ROLE_LINE = "AI / MACHINE LEARNING ENGINEER"
SUB = ("I build machine learning solutions and intelligent applications, "
       "combining AI expertise with strong software engineering principles. "
       "My work spans computer vision, NLP, generative AI, document intelligence, "
       "and end-to-end AI application development.")
ABOUT = ("AI/ML Engineer with an engineering background in Software Engineering "
         "and Mobile Development from ENSA Kénitra. I have hands-on experience "
         "across the AI development lifecycle, from data preparation and model "
         "development to evaluation, API integration, and deployment. My software "
         "engineering background helps me turn machine learning models into "
         "maintainable applications and reliable backend services.")
EMAIL = "bakh2001ssa@gmail.com"
LINKS = {
    "GitHub": "https://github.com/essa0ba1",
    "LinkedIn": "https://www.linkedin.com/in/aissa-bakhil-ba9863199/",
    "Hugging Face": "https://huggingface.co/bakhil-aissa",
    "Kaggle": "https://www.kaggle.com/aissaasasd",
    "Medium": "https://medium.com/@bakh2001ssa",
}
STATS = [
    ("<200 ms", "per-image inference API in production"),
    ("91%", "layout-analysis accuracy (87% mAP50) on CV parsing"),
    ("+35%", "candidate–job ranking vs. a TF-IDF baseline"),
    ("−60%", "manual CV review time after automation"),
]
HF = "https://huggingface.co/spaces/"
PROJECTS = [
    ("Agentic RAG (LiteParse)", "recall@5 82.5% → 90%",
     "Fully local agentic RAG on LangGraph: retrieval, relevance grading, "
     "automatic query rewriting, answers with citations. Hybrid ModernBERT "
     "(ONNX) + BM25 search in Qdrant; runs on CPU via llama.cpp.",
     ["LangGraph", "Qdrant", "ONNX Runtime", "Docker"],
     "https://github.com/essa0ba1/agentic-rag-liteparse", "GitHub"),
    ("DocExtract", "PDF/scan → Markdown & Excel",
     "Document-parsing pipeline: PP-DocLayoutV3 (custom ONNX export, 25 "
     "element classes), TableFormer for table structure, multi-engine OCR "
     "fallback and a vectorized token-to-region matcher.",
     ["ONNX", "OpenVINO", "TableFormer", "Streamlit"],
     HF + "bakhil-aissa/DocXtract", "Live demo"),
    ("SmolLM2 pruned to 97M", "2.3× faster, perplexity within 3%",
     "Metric-based structured pruning removed 29% of parameters; LoRA "
     "fine-tuning recovered accuracy. Targets Raspberry Pi and mobile "
     "edge devices.",
     ["Pruning", "LoRA/PEFT", "Edge AI"],
     HF + "bakhilaissa/SmolLM2_97_M", "Live demo"),
    ("Stable Diffusion v1.5 · INT8", "4× lower CPU latency",
     "Fine-tuned on 50 interior-design images with a custom LoRA, converted "
     "to OpenVINO IR with post-training INT8 quantization — real-time "
     "512×512 on CPU, no visible quality loss.",
     ["OpenVINO", "Optimum-Intel", "Diffusers"],
     HF + "bakhil-aissa/StableDiffusion_3d_interior", "Live demo"),
    ("SANA Sprint 0.6B · INT4", "90s → 23s, 75% smaller",
     "INT4 OpenVINO quantization of the DiT and text encoder for CPU-only "
     "text-to-image. Full benchmark written up on Medium.",
     ["OpenVINO", "INT4", "Diffusion"],
     HF + "bakhil-aissa/sana_0.6b_benckmark", "Live demo"),
    ("Prompt-injection detector API", "<50 ms per request",
     "ModernBERT classifier for adversarial prompt injection, exported to "
     "ONNX and served through FastAPI — ready for LLM-gateway security "
     "layers.",
     ["ModernBERT", "ONNX Runtime", "FastAPI"],
     HF + "bakhil-aissa/prompt-injection-detector", "Live demo"),
]
EXPERIMENTS = [
    ("DFlash", "speculative decoding for LLMs on AVX2-only CPUs"),
    ("OvisOCR2", "ONNX export + INT4 quantization of a multimodal OCR "
                 "model on an i7-5500U laptop"),
    ("MNN quantization", "small VLMs (Qwen3.5-0.8B, GLM-OCR) on CPU"),
    ("Qwen3-TTS 0.6B", "text-to-speech on CPU with MNN"),
]
JOBS = [
    ("AI Engineer — Plant Disease Detection", "XCare",
     "Jan 2025 – Feb 2026 · Rabat, Morocco", [
         "Trained and deployed a YOLOv12 pipeline for multi-species plant "
         "disease classification, enabling real-time crop monitoring.",
         "Built a Streamlit/Gradio dashboard: technicians upload an image "
         "and get an instant diagnosis with confidence scores and "
         "treatment recommendations.",
         "Shipped the inference API with FastAPI + Docker at under 200 ms "
         "per image on standard cloud CPUs."]),
    ("AI Engineer — Intelligent Recruitment Platform", "CapitaleTech",
     "Feb 2024 – Jan 2025 · Morocco", [
         "Designed a resume-parsing pipeline with YOLOv12 layout analysis "
         "(91% accuracy, 87% mAP50), extracting 8+ section types from "
         "unstructured PDFs and scans.",
         "Fine-tuned DistilBERT for semantic candidate–job matching: "
         "relevance ranking up 35% over a TF-IDF baseline (F1 = 0.82).",
         "Built a layout-quality assessment module, cutting manual CV "
         "review time by 60%.",
         "Delivered the full stack: FastAPI ranking backend, Streamlit "
         "recruiter UI, Dockerized for cloud deployment."]),
]
SKILLS = [
    ("Software development", "Python, C/C++, Java, C#, FastAPI, REST, Docker, Git"),
    ("AI & ML", "PyTorch, Transformers, Diffusers, Keras, scikit-learn, OpenCV, Pandas"),
    ("Optimization & deployment", "ONNX, ONNX Runtime, OpenVINO, Optimum-Intel, INT4/INT8 "
                                  "quantization, structured pruning, LoRA/PEFT, distillation"),
    ("NLP & generative AI", "BERT, DistilBERT, ModernBERT, LLMs, LangChain, LlamaIndex, "
                            "RAG, text-to-image (SD, SANA)"),
    ("MLOps & tools", "AWS, GCP, Gradio, Streamlit, Weights & Biases, Label Studio, pytest"),
]
CERTS = [
    ("Reinforcement Learning: Beginner to Expert — Escape Velocity Labs / Udemy, Jan 2025",
     "https://www.udemy.com/certificate/UC-5540ceaf-2f99-4dfd-a9e7-30fc1bfddbc9/"),
    ("Generative AI with Large Language Models — DeepLearning.AI & AWS, Apr 2024",
     "https://coursera.org/share/3c95df93ee88f984917c11d4700dd69d"),
]
NAV = [("HOME", "home"), ("ABOUT", "about"), ("PROJECTS", "projects"),
       ("BLOG", "blogs"), ("EXPERIENCE", "experience"), ("SKILLS", "skills"),
       ("CONTACT", "contact")]
PROJECTS.insert(2, PROJECTS.pop())  # lead with the broadly useful ones

PAGE = None  # set in main(); used by the scroll-to-section handlers


# --------------------------------------------------------------- helpers
def goto(key: str):
    async def handler(e):
        r = PAGE.scroll_to(scroll_key=ft.ScrollKey(key), duration=450)
        if inspect.isawaitable(r):
            await r
    return handler


def opener(url: str):
    """Open a link the way Flet 1.0 itself does: through UrlLauncher."""
    async def handler(e):
        await ft.UrlLauncher().launch_url(url)
    return handler


def txt(s, size=15, color=MUTE, weight=None, **kw):
    return ft.Text(s, size=size, color=color, weight=weight, **kw)


def card(content, **kw):
    return ft.Container(content=content, padding=20, bgcolor=CARD,
                        border=ft.Border.all(width=1, color=LINE),
                        border_radius=ft.BorderRadius.all(12), **kw)


def chip(s):
    return ft.Container(
        content=ft.Text(s, size=12, color=MUTE),
        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
        border=ft.Border.all(width=1, color=LINE),
        border_radius=ft.BorderRadius.all(6))


def link_btn(label, url, primary=False):
    if primary:
        return ft.Button(content=ft.Text(label), on_click=opener(url), bgcolor=ACC, color=BG)
    return ft.OutlinedButton(content=ft.Text(label, color=INK), on_click=opener(url))


def section(key, title, body):
    """Centered, width-capped (percentage based, so it never overflows
    on phones), tagged with a scroll key for the nav."""
    inner = ft.Column([txt(title, 26, INK, ft.FontWeight.W_700),
                       ft.Container(height=16), body])
    return ft.Container(
        key=ft.ScrollKey(key), padding=ft.Padding(left=20, top=48, right=20, bottom=24),
        content=ft.ResponsiveRow(
            [ft.Container(inner, col={"xs": 12, "lg": 10, "xl": 9})],
            alignment=ft.MainAxisAlignment.CENTER))


def bullets(items):
    return ft.Column(
        [ft.Row([txt("•", 14, ACC),
                 txt(b, 14, MUTE, expand=True)],
                spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
         for b in items], spacing=6)


# --------------------------------------------------------------- blog data
BLOGS_DIR = Path(__file__).parent / "blogs"


def load_local_blog_posts() -> list[dict]:
    """Read article summaries from Markdown files during local development."""
    if not BLOGS_DIR.is_dir():
        return []

    posts = []
    for path in BLOGS_DIR.glob("*.md"):
        if path.name.startswith("_"):
            continue
        try:
            parsed = parse_blog_post(path.name, path.read_text(encoding="utf-8"))
            posts.append(public_post_metadata(parsed))
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"Skipping blog post {path.name}: {exc}")

    return sorted(posts, key=lambda post: (post["date"], post["title"].casefold()), reverse=True)


# -------------------------------------------------------------- sections
def hero():
    """Full-width hero tuned for assets/hero.png.

    The background artwork keeps its visual focus on the right; the content
    sits in the darker, open area on the left. If hero.png is absent, the
    gradient fallback still gives the hero a finished appearance.
    """
    # In a static Flet web build, assets are served by the web runtime and are
    # not guaranteed to appear as ordinary files in the browser's Python FS.
    # Reference assets directly instead of testing Path.is_file() at runtime.
    profile = ft.Image(
        src="profile.jpeg",
        fit=ft.BoxFit.COVER,
        width=256,
        height=256,
    )
    avatar = ft.Container(
        content=profile,
        width=256,
        height=256,
        alignment=ft.Alignment.CENTER,
        bgcolor=CARD,
        border=ft.Border.all(width=2, color=ft.Colors.with_opacity(0.8, INK)),
        border_radius=ft.BorderRadius.all(56*3),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )

    intro = ft.Column(
        controls=[
            avatar,
            ft.Container(height=2),
            ft.Text(
                HEADLINE,
                size=40,
                color="#FFFFFF",
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.LEFT,
            ),
            ft.Text(
                ROLE_LINE,
                size=15,
                color=ACC,
                weight=ft.FontWeight.W_700,
                style=ft.TextStyle(letter_spacing=2.2),
                text_align=ft.TextAlign.LEFT,
            ),
            ft.Container(
                content=ft.Text(
                    SUB,
                    size=16,
                    color="#D0D8EC",
                    text_align=ft.TextAlign.LEFT,
                ),
                padding=ft.Padding(top=4, bottom=4),
            ),
            ft.Row(
                controls=[
                    link_btn("Get in touch", f"mailto:{EMAIL}", True),
                    link_btn("Resume", "/resume.pdf"),
                    ft.OutlinedButton(
                        content=ft.Text("View work", color=INK),
                        on_click=goto("projects"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
                spacing=10,
                run_spacing=10,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.START,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=12,
    )

    # The ResponsiveRow caps the text column on wide screens and lets it use
    # the available width on phones, while keeping the image as a background.
    content_layer = ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER_LEFT,
        padding=ft.Padding(left=56, top=36, right=28, bottom=36),
        content=ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=intro,
                    col={"xs": 12, "sm": 11, "md": 8, "lg": 7, "xl": 6},
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            run_spacing=0,
        ),
    )

    layers = [
        ft.Container(
            expand=True,
            bgcolor=BG,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0A1530", BG],
            ),
        )
    ]

    layers.append(
        ft.Image(
            src="hero.png",
            fit=ft.BoxFit.COVER,
            expand=True,
            cache_width=1648,
        )
    )
    # Keep the left text area dark, while leaving the neural artwork bright.
    layers.append(
        ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[
                    ft.Colors.with_opacity(0.98, BG),
                    ft.Colors.with_opacity(0.91, BG),
                    ft.Colors.with_opacity(0.69, BG),
                    ft.Colors.with_opacity(0.10, BG),
                ],
            ),
        )
    )
    # A subtle bottom fade helps the hero blend into the page background.
    layers.append(
        ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    ft.Colors.with_opacity(0.02, BG),
                    ft.Colors.with_opacity(0.00, BG),
                    ft.Colors.with_opacity(0.24, BG),
                ],
            ),
        )
    )

    layers.append(content_layer)

    return ft.Container(
        key=ft.ScrollKey("home"),
        height=660,
        content=ft.Stack(controls=layers, fit=ft.StackFit.EXPAND),
    )


def about():
    stats = ft.ResponsiveRow(
        [card(ft.Column([
            ft.Text(v, size=28, color=GOOD, font_family=MONO, weight=ft.FontWeight.W_600),
            txt(d, 13)], spacing=6), col={"xs": 6, "md": 3}) for v, d in STATS],
        spacing=12, run_spacing=12)
    return section("about", "About me", ft.Column(
        [txt(ABOUT, 17), ft.Container(height=8), stats], spacing=12))


def projects():
    cards = []
    for name, metric, desc, tags, url, label in PROJECTS:
        cards.append(card(ft.Column([
            txt(name, 17, INK, ft.FontWeight.W_600),
            ft.Container(
                content=ft.Text(metric, size=12, color=ACC, font_family=MONO),
                bgcolor=ACC_SOFT, padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                border_radius=ft.BorderRadius.all(6)),
            txt(desc, 14),
            ft.Row([chip(t) for t in tags], wrap=True, spacing=6, run_spacing=6),
            ft.TextButton(content=ft.Text(f"{label} →", color=ACC), on_click=opener(url)),
        ], spacing=10), col={"xs": 12, "md": 6, "xl": 4}))
    extra = card(ft.Column([txt("Also", 16, INK, ft.FontWeight.W_600),
        bullets(["SpeechT5 voice cloning — TTS fine-tuned on 1.5 h of audio",
                 "Freelance document-AI extraction on Fiverr and Upwork",
                 "Kaggle competitions and technical writing on Medium"]),
        ft.TextButton(content=ft.Text("SpeechT5 model →", color=ACC),
                      on_click=opener("https://huggingface.co/bakhil-aissa/speecht5_voice_cloning"))],
        spacing=10))
    return section("projects", "Selected projects", ft.Column([
        ft.ResponsiveRow(cards, spacing=12, run_spacing=12),
        ft.Container(height=4), extra], spacing=12))


def blog_section(blog_panel):
    intro = txt(
        "Technical articles, project write-ups, and lessons learned. "
        "Each article opens as a fast, standalone page generated from Markdown.",
        15,
    )
    archive_link = ft.Row(
        [ft.TextButton(content=ft.Text("Browse all articles  →", color=ACC), url="blog/")],
        alignment=ft.MainAxisAlignment.END,
    )
    return section(
        "blogs", "Writing & notes", ft.Column([intro, blog_panel, archive_link], spacing=14)
    )


def experience():
    jobs = [card(ft.Column([
        txt(f"{role} · {co}", 17, INK, ft.FontWeight.W_600),
        txt(when, 13), bullets(items)], spacing=8)) for role, co, when, items in JOBS]
    return section("experience", "Experience", ft.Column(jobs, spacing=12))


def skills():
    left = card(ft.Column([ft.Column([txt(k, 14, INK, ft.FontWeight.W_600), txt(v, 14)],
                                     spacing=2) for k, v in SKILLS], spacing=12),
                col={"xs": 12, "md": 6})
    right = card(ft.Column([
        txt("Education", 16, INK, ft.FontWeight.W_600),
        txt("ENSA Kénitra, Morocco · Aug 2019 – Sept 2024", 14, INK),
        txt("State Engineering Degree in Software Engineering and Mobile Development", 14),
        ft.Container(height=6),
        txt("Certifications", 16, INK, ft.FontWeight.W_600),
        *[ft.TextButton(content=ft.Text(t, color=ACC, size=14), on_click=opener(u)) for t, u in CERTS],
        ft.Container(height=6),
        txt("Languages", 16, INK, ft.FontWeight.W_600),
        txt("Arabic, French (fluent), English (fluent)", 14)], spacing=6),
        col={"xs": 12, "md": 6})
    return section("skills", "Skills, education & certifications",
                   ft.ResponsiveRow([left, right], spacing=12, run_spacing=12))


def contact():
    btns = [link_btn(EMAIL, f"mailto:{EMAIL}", True), link_btn("Download resume", "/resume.pdf")]
    btns += [link_btn(k, v) for k, v in LINKS.items()]
    return section("contact", "Let’s talk", ft.Column([
        txt("Have an AI product to build, a machine learning problem to solve, "
            "or an opportunity to discuss? Email is the fastest way to reach me.", 16),
        ft.Row(btns, wrap=True, spacing=10, run_spacing=10)], spacing=16))


# ----------------------------------------------------------------- entry
def main(page: ft.Page) -> None:
    global PAGE
    PAGE = page
    page.title = f"{NAME} — AI/ML Engineer"
    page.bgcolor = BG
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ACC)

    # The Flet homepage shows article summaries only. Full articles are
    # generated as standalone static HTML pages under /blog/<slug>/.
    blog_panel = ft.Column(spacing=12)
    posts: list[dict] = []

    def show_blog_list() -> None:
        if not posts:
            blog_panel.controls = [card(ft.Column([
                txt("No articles published yet", 17, INK, ft.FontWeight.W_600),
                txt(
                    "Add a Markdown file to blogs/ and run "
                    "python tools/build_blogs.py before publishing.",
                    14,
                ),
            ], spacing=8))]
            page.update()
            return

        post_cards = []
        for post in posts:
            metadata = []
            if post.get("date"):
                metadata.append(txt(post["date"], 12, ACC, weight=ft.FontWeight.W_600))
            if post.get("reading_time"):
                metadata.append(txt(f"{post['reading_time']} min read", 12, MUTE))
            metadata.extend(chip(tag) for tag in post.get("tags", []))

            post_cards.append(card(ft.Column([
                ft.Row(metadata, wrap=True, spacing=7, run_spacing=7),
                txt(post["title"], 19, INK, ft.FontWeight.W_600),
                txt(post.get("description") or "Open the article to read more.", 14),
                ft.TextButton(
                    content=ft.Text("Read article  →", color=ACC),
                    url=post["url"],
                ),
            ], spacing=9)))

        blog_panel.controls = post_cards
        page.update()

    async def load_static_blog_posts() -> None:
        """Load article summaries; full article HTML is served as static files."""
        nonlocal posts
        try:
            from pyodide.http import pyfetch

            response = await pyfetch("blogs/index.json")
            if not response.ok:
                raise RuntimeError(f"Blog index returned HTTP {response.status}")
            entries = await response.json()
            loaded = []
            for entry in entries if isinstance(entries, list) else []:
                if not isinstance(entry, dict):
                    continue
                slug = str(entry.get("slug", ""))
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", slug):
                    continue
                tags = entry.get("tags", [])
                loaded.append({
                    "slug": slug,
                    "title": str(entry.get("title") or slug.replace("-", " ").title()),
                    "date": str(entry.get("date") or ""),
                    "description": str(entry.get("description") or ""),
                    "tags": [str(tag) for tag in tags if str(tag).strip()] if isinstance(tags, list) else [],
                    "reading_time": max(1, int(entry.get("reading_time") or 1)),
                    "url": f"blog/{slug}/",
                })
            posts = sorted(
                loaded,
                key=lambda post: (post["date"], post["title"].casefold()),
                reverse=True,
            )
            show_blog_list()
        except Exception as exc:
            blog_panel.controls = [card(ft.Column([
                txt("Unable to load article list", 17, INK, ft.FontWeight.W_600),
                txt(f"{type(exc).__name__}: {exc}", 13),
                txt(
                    "Rebuild the blog pages with python tools/build_blogs.py, "
                    "then rebuild the Flet website.",
                    13,
                ),
            ], spacing=8))]
            page.update()

    page.appbar = ft.AppBar(
        bgcolor=BG, toolbar_height=56, automatically_imply_leading=False,
        title=ft.Row([
            ft.Text(NAME, weight=ft.FontWeight.W_700, color=INK),
            ft.Row([ft.TextButton(content=ft.Text(label, color=MUTE, size=12, style=ft.TextStyle(letter_spacing=1.5)),
                                  on_click=goto(key)) for label, key in NAV],
                   scroll=ft.ScrollMode.AUTO, expand=True)], spacing=16))

    body = ft.Column([
        hero(), about(), projects(), blog_section(blog_panel), experience(), skills(), contact(),
        ft.Container(txt(f"© {NAME} · Khénifra, Morocco", 13),
                     padding=32, alignment=ft.Alignment.CENTER),
    ])
    page.add(ft.SelectionArea(content=body) if hasattr(ft, "SelectionArea") else body)

    if sys.platform == "emscripten":
        blog_panel.controls = [txt("Loading articles…", 14)]
        page.run_task(load_static_blog_posts)
    else:
        posts = load_local_blog_posts()
        show_blog_list()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")