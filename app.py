import flet as ft
import os
import shutil
from datetime import datetime
from ocr_processor import search_images, OllamaClient, are_models_loaded
import ollama
import unicodedata
import threading
import time

# Temporary directory for Flet to serve images from
ASSETS_DIR = "assets"
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# --- THEME COLORS (Business Premium) ---
BG_COLOR = "#0F172A"      # Midnight Blue
CARD_COLOR = "#1E293B"    # Slate
ACCENT_COLOR = "#38BDF8"  # Sky Blue
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
TEXT_ACCENT = "#7DD3FC"

def get_snippet(text, query, padding=40):
    """Extract a snippet of text around the first matching word or phrase."""
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    query = unicodedata.normalize('NFC', query)
    
    if not query or not text:
        return text[:100] + "..." if len(text) > 100 else text
    
    import re
    match = re.search(re.escape(query), text, re.IGNORECASE)
    
    if not match:
        words = [w for w in query.split() if len(w) > 1]
        if words:
            pattern = re.compile(f"({'|'.join(re.escape(w) for w in words)})", re.IGNORECASE)
            match = pattern.search(text)
            
    if not match:
        return text[:100] + "..." if len(text) > 100 else text
    
    start = max(0, match.start() - padding)
    end = min(len(text), match.end() + padding)
    
    snippet = text[start:end].replace("\n", " ")
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet

def get_highlighted_control(text, query, size=12, color=TEXT_SECONDARY, detail=False):
    """Return a Text control with spans for highlighting query words and phrases."""
    if not text:
        return ft.Text("", size=size, color=color)
    
    text = unicodedata.normalize('NFC', text)
    query = unicodedata.normalize('NFC', query)
    
    if not query or not text:
        return ft.Text(text, size=size, color=color, italic=not detail)
    
    import re
    highlight_targets = [query]
    if " " in query:
        highlight_targets.extend([w for w in query.split() if len(w) > 1])
    
    highlight_targets = sorted(list(set(highlight_targets)), key=len, reverse=True)
    pattern = re.compile(f"({'|'.join(re.escape(t) for t in highlight_targets)})", re.IGNORECASE)
    
    parts = pattern.split(text)
    spans = []
    
    highlight_style = ft.TextStyle(
        weight="bold", 
        color="#FDE047", # Bright Yellow for highlights
        bgcolor="rgba(253, 224, 71, 0.1)" 
    )
    
    for part in parts:
        is_match = False
        if part and any(part.lower() == target.lower() for target in highlight_targets):
            is_match = True
            
        if is_match:
            spans.append(ft.TextSpan(part, style=highlight_style))
        else:
            spans.append(ft.TextSpan(part))
            
    return ft.Text(
        spans=spans, 
        size=size, 
        color=color, 
        italic=not detail, 
        max_lines=None if detail else 3, 
        overflow=None if detail else "ellipsis"
    )

def main(page: ft.Page):
    page.title = "Screenshot Note Taker"
    page.theme_mode = "dark"
    page.padding = 30
    page.window_width = 1300
    page.window_height = 900
    page.bgcolor = BG_COLOR
    
    # Custom font from Google Fonts
    page.fonts = {
        "Outfit": "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit-VariableFont_wght.ttf"
    }
    page.theme = ft.Theme(font_family="Outfit")

    search_results = ft.GridView(
        expand=1,
        runs_count=5,
        max_extent=320,
        child_aspect_ratio=0.75,
        spacing=25,
        run_spacing=25,
    )

    detail_panel = ft.Container(
        visible=False,
        width=450,
        padding=20,
        bgcolor=CARD_COLOR,
        border_radius=15,
        content=ft.Column(
            scroll="auto",
            spacing=20,
        )
    )
    
    # Status Banner
    loading_banner = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.Icons.WIFI_OFF, color="#EF4444", size=16),
            ft.Text(" Ollama Offline", color="#EF4444", size=12, weight="bold")
        ], alignment="center"),
        bgcolor="rgba(239, 68, 68, 0.1)",
        padding=ft.Padding(12, 6, 12, 6),
        border_radius=20,
        visible=not are_models_loaded(),
    )
    
    def check_ollama():
        while True:
            try:
                is_up = are_models_loaded()
                loading_banner.visible = not is_up
                if is_up:
                    loading_banner.content = ft.Row([
                        ft.Icon(ft.icons.Icons.CHECK_CIRCLE, color="#10B981", size=16),
                        ft.Text(" AI Engine Ready", color="#10B981", size=12)
                    ], alignment="center")
                    loading_banner.bgcolor = "rgba(16, 185, 129, 0.1)"
                else:
                    loading_banner.content = ft.Row([
                        ft.Icon(ft.icons.Icons.WIFI_OFF, color="#EF4444", size=16),
                        ft.Text(" Ollama Offline", color="#EF4444", size=12, weight="bold")
                    ], alignment="center")
                    loading_banner.bgcolor = "rgba(239, 68, 68, 0.1)"
                page.update()
            except:
                pass
            time.sleep(5)

    def close_dialog(e=None):
        """Robustly close any open alert dialog on the page."""
        for ctrl in list(page.overlay):
            if isinstance(ctrl, ft.AlertDialog):
                ctrl.open = False
                page.overlay.remove(ctrl)
        page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            if detail_panel.visible:
                hide_detail()
            close_dialog()
        elif e.key == "Enter":
            close_dialog()

    page.on_keyboard_event = on_keyboard

    def show_toast(message, color=ACCENT_COLOR):
        """Show a temporary notification that disappears on its own."""
        sb = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=color,
            duration=3000,
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def do_search(query):
        if not query:
            return
        
        if not are_models_loaded():
            msg = ft.SnackBar(ft.Text("Ollama is not running. Search is limited."), bgcolor="#EF4444")
            page.overlay.append(msg)
            msg.open = True
            page.update()
        
        query = unicodedata.normalize('NFC', query)
        
        # Simple non-modal loading indicator
        search_progress = ft.ProgressBar(width=400, color=ACCENT_COLOR, bgcolor="rgba(255,255,255,0.1)")
        search_status = ft.Text("Thinking...", size=12, color=TEXT_SECONDARY)
        loading_container = ft.Column([search_status, search_progress], horizontal_alignment="center")
        
        search_results.controls.clear()
        search_results.controls.append(ft.Container(content=loading_container, padding=100, alignment="center"))
        page.update()
        
        try:
            results = search_images(query, mode='hybrid', limit=24)
            search_results.controls.clear()
            
            if not results:
                search_results.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.Icons.SEARCH_OFF, size=50, color=TEXT_SECONDARY),
                            ft.Text("No matching screenshots found.", size=18, color=TEXT_SECONDARY)
                        ], horizontal_alignment="center"),
                        expand=True,
                        padding=100,
                        alignment="center"
                    )
                )
            else:
                show_toast(f"Found {len(results)} relevant activities")
                for res in results:
                    filename = os.path.basename(res['filepath'])
                    asset_path = os.path.join(ASSETS_DIR, filename)
                    if not os.path.exists(asset_path):
                        try:
                            shutil.copy2(res['filepath'], asset_path)
                        except:
                            pass
                    
                    score_val = res.get('score', 0)
                    score_color = "#10B981" if score_val > 0.6 else "#F59E0B" if score_val > 0.4 else TEXT_SECONDARY
                    
                    # Determine which text to show in preview
                    preview_text = res.get('ai_description', '') or res.get('text', '')
                    
                    search_results.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Stack([
                                        ft.Image(
                                            src=f"/{filename}",
                                            fit="cover",
                                            height=180,
                                            width=320,
                                            border_radius=10,
                                        ),
                                        ft.Container(
                                            content=ft.Text(f"{int(score_val*100)}%", size=10, weight="bold", color="white"),
                                            bgcolor=score_color,
                                            padding=ft.Padding(6, 2, 6, 2),
                                            border_radius=5,
                                            top=10,
                                            right=10,
                                            visible=res['type'] == 'semantic'
                                        )
                                    ]),
                                    ft.Text(res['filename'], weight="bold", max_lines=1, overflow="ellipsis", color=TEXT_PRIMARY),
                                    ft.Row([
                                        ft.Icon(ft.icons.Icons.CALENDAR_MONTH, size=12, color=TEXT_SECONDARY),
                                        ft.Text(f"{res['timestamp'].strftime('%b %d, %Y')}", size=12, color=TEXT_SECONDARY),
                                    ], spacing=5),
                                    get_highlighted_control(get_snippet(preview_text, query), query),
                                    ft.Row([
                                        ft.Container(
                                            content=ft.Text(res['type'].upper(), size=8, weight="bold", color="white"), 
                                            bgcolor="#6366F1" if res['type'] == 'semantic' else "#10B981",
                                            padding=ft.Padding(6, 2, 6, 2),
                                            border_radius=4
                                        ),
                                    ])
                                ],
                                spacing=8,
                            ),
                            padding=15,
                            bgcolor=CARD_COLOR,
                            border_radius=12,
                            on_click=lambda _, r=res, q=query: show_detail(r, q),
                            ink=True,
                            animate_scale=ft.Animation(200, "easeOut"),
                            on_hover=lambda e: setattr(e.control, "scale", 1.02 if e.data == "true" else 1.0)
                        )
                    )
        except Exception as e:
            search_results.controls.clear()
            search_results.controls.append(ft.Text(f"Error: {str(e)}", color="#EF4444"))
        
        page.update()

    def show_detail(res, query=""):
        detail_panel.visible = True
        detail_panel.content.controls.clear()
        
        filename = os.path.basename(res['filepath'])
        
        detail_panel.content.controls.extend([
            ft.Row([
                ft.Text("Visual Recall", size=20, weight="bold", color=ACCENT_COLOR),
                ft.IconButton(ft.icons.Icons.CLOSE, on_click=lambda _: hide_detail(), icon_color=TEXT_SECONDARY)
            ], alignment="spaceBetween"),
            ft.Container(
                content=ft.Image(
                    src=f"/{filename}",
                    fit="contain",
                    border_radius=10,
                ),
                border=ft.border.all(1, "rgba(255,255,255,0.1)"),
                border_radius=10
            ),
            ft.Column([
                ft.Text("FILE INFORMATION", size=10, weight="bold", color=TEXT_SECONDARY),
                ft.Text(res['filename'], size=14, weight="bold"),
                ft.Text(res['filepath'], size=11, color=TEXT_SECONDARY),
                ft.Text(res['timestamp'].strftime('%Y-%m-%d %I:%M:%S %p'), size=12),
            ], spacing=5),
            ft.Divider(color="rgba(255,255,255,0.05)"),
            ft.Column([
                ft.Text("AI INSIGHT", size=10, weight="bold", color=ACCENT_COLOR),
                ft.Container(
                    content=ft.Text(res.get('ai_description', 'No AI description available yet.'), size=14, color=TEXT_PRIMARY),
                    padding=15,
                    bgcolor="rgba(255,255,255,0.03)",
                    border_radius=10,
                    border=ft.border.all(1, "rgba(255,255,255,0.05)")
                )
            ], spacing=10),
            ft.Column([
                ft.Text("EXTRACTED TEXT", size=10, weight="bold", color=TEXT_SECONDARY),
                ft.Container(
                    content=ft.Column([
                        get_highlighted_control(res.get('text', ''), query, size=13, color=TEXT_SECONDARY, detail=True)
                    ], scroll="auto"),
                    padding=15,
                    bgcolor="rgba(0,0,0,0.2)",
                    border_radius=10,
                    height=200
                )
            ], spacing=10),
            ft.ElevatedButton(
                "Regenerate Analysis", 
                icon=ft.icons.Icons.AUTO_AWESOME, 
                style=ft.ButtonStyle(
                    color=TEXT_PRIMARY,
                    bgcolor=ACCENT_COLOR,
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=lambda _: regenerate_ai(res)
            )
        ])
        page.update()

    def hide_detail():
        detail_panel.visible = False
        page.update()

    def regenerate_ai(res):
        def task():
            try:
                show_toast("Deep analysis in progress...", ACCENT_COLOR)
                from ocr_processor import generate_image_description, OllamaClient
                
                # 1. Generate new description
                desc, model = generate_image_description(res['filepath'])
                if not desc:
                    raise Exception("Failed to generate description")
                
                # 2. Update Database
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST"),
                    port=os.getenv("POSTGRES_PORT"),
                    dbname=os.getenv("POSTGRES_DB"),
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD")
                )
                cursor = conn.cursor()
                
                # Update image description
                cursor.execute(
                    "UPDATE images SET ai_description = %s, model_name = %s WHERE id = %s",
                    (desc, model, res['id'])
                )
                
                # Update embedding for chunk -1
                client = OllamaClient()
                emb = client.generate_embedding(desc)
                if emb:
                    cursor.execute(
                        "INSERT INTO text_embedding (image_id, embedding, chunk_index) VALUES (%s, %s, -1) "
                        "ON CONFLICT (image_id, chunk_index) DO UPDATE SET embedding = EXCLUDED.embedding",
                        (res['id'], emb)
                    )
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Update local UI data
                res['ai_description'] = desc
                
                # Refresh UI
                show_toast("AI Analysis updated successfully!", "#10B981")
                show_detail(res) # Refresh panel content
                
            except Exception as e:
                show_toast(f"Regeneration failed: {str(e)}", "#EF4444")

        threading.Thread(target=task, daemon=True).start()

    # Chat-inspired Search Box
    search_input = ft.TextField(
        hint_text="Ask me anything about your previous activities...",
        expand=True,
        on_submit=lambda e: do_search(e.control.value),
        border_radius=25,
        bgcolor=CARD_COLOR,
        border_color="rgba(255,255,255,0.1)",
        focused_border_color=ACCENT_COLOR,
        content_padding=ft.Padding(50, 15, 20, 15),
        text_size=16,
    )
    
    search_box_with_icon = ft.Stack([
        search_input,
        ft.Container(
            content=ft.Icon(ft.icons.Icons.CHAT_BUBBLE_OUTLINE, color=TEXT_SECONDARY, size=20),
            left=20,
            top=15,
        )
    ], expand=True)
    
    chat_container = ft.Container(
        content=ft.Row([
            search_box_with_icon,
            ft.IconButton(
                icon=ft.icons.Icons.SEND_ROUNDED,
                icon_color=ACCENT_COLOR,
                icon_size=30,
                on_click=lambda _: do_search(search_input.value)
            )
        ], spacing=10),
        padding=ft.Padding(0, 10, 0, 30)
    )

    header = ft.Row([
        ft.Column([
            ft.Text("Screenshot Note Taker", size=32, weight="bold", color=TEXT_PRIMARY),
            ft.Text("Find anything you've seen before", size=14, color=TEXT_SECONDARY),
        ], spacing=0),
        ft.Container(expand=True),
        loading_banner
    ], alignment="center")

    page.add(
        header,
        ft.Divider(height=40, color="transparent"),
        chat_container,
        ft.Row([
            search_results,
            detail_panel
        ], expand=True, spacing=30)
    )
    
    threading.Thread(target=check_ollama, daemon=True).start()

if __name__ == "__main__":
    ft.run(main, assets_dir=ASSETS_DIR)
