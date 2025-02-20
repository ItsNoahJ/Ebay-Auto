"""
Main application GUI using Flet.
"""
import flet as ft
from typing import Optional
from pathlib import Path
import os
from src.vision.processor import VisionProcessor
from src.models.database import Database

class MediaProcessorApp:
    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.current_file: Optional[Path] = None
        self.debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
        self.processor = VisionProcessor(debug_output_dir="debug_output")
        self.db = Database()
        
        # UI components
        self.file_picker: Optional[ft.FilePicker] = None
        self.preview_container: Optional[ft.Container] = None
        self.process_button: Optional[ft.ElevatedButton] = None
        self.clear_button: Optional[ft.ElevatedButton] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.status_text: Optional[ft.Text] = None

    def initialize_ui(self, page: ft.Page):
        """Initialize the UI components."""
        self.page = page
        page.title = "Media Processor"
        page.theme_mode = ft.ThemeMode.DARK
        # Set minimum window dimensions that show all content without scrolling
        page.window_width = 1000
        page.window_height = 900
        page.window_min_width = 1000
        page.window_min_height = 900
        page.padding = 20
        page.scroll = "auto"  # Enable scrolling when window is resized smaller
        
        # Initialize file picker first
        self.file_picker = ft.FilePicker(
            on_result=self.on_file_selected
        )
        page.overlay.append(self.file_picker)
        
        # Initialize status components
        self.status_text = ft.Text(
            "Ready",
            color=ft.colors.GREY_400
        )
        
        self.progress_bar = ft.ProgressBar(
            width=400,
            value=0,
            visible=False
        )
        
        # Initialize buttons
        self.process_button = ft.ElevatedButton(
            "Process Image",
            icon=ft.icons.PLAY_ARROW,
            on_click=self.process_image,
            disabled=True
        )
        
        self.clear_button = ft.ElevatedButton(
            "Clear",
            icon=ft.icons.CLEAR,
            on_click=self.clear_all,
            disabled=True
        )
        
        # Initialize preview container
        self.preview_container = ft.Container(
            content=ft.Text("No image selected", color=ft.colors.GREY_400),
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=10,
            padding=20,
            width=960,
            height=500,
            alignment=ft.alignment.center
        )
        
        # Create scroll container for all content
        scroll_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("eBay Media Processor", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Streamline your media listings", size=16, color=ft.colors.GREY_400),
                    ft.Divider(),
                    self._build_input_section(),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            self.progress_bar,
                            self.status_text
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    self._build_preview_section(),
                    ft.Divider(),
                    self._build_actions_section(),
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO
            ),
            expand=True,
            padding=20
        )
        
        page.add(scroll_container)

    def _build_input_section(self) -> ft.Control:
        """Build the file input section."""
        return ft.Column(
            controls=[
                ft.Text("Select Media Image", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Choose File",
                            icon=ft.icons.FILE_UPLOAD,
                            on_click=lambda _: self.file_picker.pick_files(
                                allow_multiple=False,
                                allowed_extensions=["png", "jpg", "jpeg"]
                            )
                        ),
                        ft.Text("or drag and drop image here", color=ft.colors.GREY_400),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=20
                )
            ]
        )

    def _build_preview_section(self) -> ft.Control:
        """Build the image preview section."""
        return ft.Column(
            controls=[
                ft.Text("Preview", size=20, weight=ft.FontWeight.BOLD),
                self.preview_container
            ]
        )

    def _build_actions_section(self) -> ft.Control:
        """Build the actions section."""
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.process_button,
                        self.clear_button
                    ],
                    spacing=20
                )
            ]
        )

    def _update_status(self, message: str, progress: float = None):
        """Update status display."""
        self.status_text.value = message
        
        if progress is not None:
            self.progress_bar.visible = True
            self.progress_bar.value = progress
        else:
            self.progress_bar.visible = False
            
        self.page.update()

    def on_file_selected(self, e: ft.FilePickerResultEvent):
        """Handle file selection result."""
        if e.files and e.files[0] is not None:
            file_path = Path(e.files[0].path)
            self.current_file = file_path
            
            # Enable buttons
            self.process_button.disabled = False
            self.clear_button.disabled = False
            
            # Update preview
            self.preview_container.content = ft.Image(
                src=str(file_path),
                width=940,
                height=480,
                fit=ft.ImageFit.CONTAIN
            )
            
            self._update_status(f"Selected: {file_path.name}")

    def process_image(self, e):
        """Process the selected image."""
        if not self.current_file:
            return
            
        # Update UI
        self.process_button.disabled = True
        self._update_status("Processing image...", 0.2)
        
        try:
            # Process image
            self._update_status("Detecting media type...", 0.4)
            results = self.processor.process_image(str(self.current_file))
            
            # Store results
            self._update_status("Saving results...", 0.8)
            self.db.add_media_item(
                filename=self.current_file.name,
                file_path=str(self.current_file),
                media_type=results["debug_info"]["media_type"]["detected"],
                extracted_data=results["extracted_data"],
                ocr_data={
                    "text": ", ".join([str(v) for v in results["extracted_data"].values()]),
                    "confidence": sum(results["debug_info"]["confidence_scores"].values()) / 
                                len(results["debug_info"]["confidence_scores"])
                },
                debug_info={
                    "images": results["debug_info"]["debug_images"],
                    "barcode_info": results["debug_info"]["barcode_info"],
                    "log": []  # To be implemented
                }
            )
            
            # Update preview with results
            self._update_status("Complete!", 1.0)
            
            # Build results display
            result_controls = [
                ft.Text("Results:", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Media Type: {results['debug_info']['media_type']['detected'].upper()} "
                       f"({results['debug_info']['media_type']['confidence']:.1f}% confidence)"),
                ft.Text(f"Title: {results['extracted_data'].get('title', 'Not found')}"),
                ft.Text(f"Year: {results['extracted_data'].get('year', 'Not found')}"),
                ft.Text(f"Runtime: {results['extracted_data'].get('runtime', 'Not found')}")
            ]
            
            # Add barcode info if found
            if "barcode" in results["extracted_data"]:
                result_controls.append(
                    ft.Text(f"Barcode: {results['extracted_data']['barcode']}")
                )
                if "barcode_metadata" in results["extracted_data"]:
                    metadata = results["extracted_data"]["barcode_metadata"]
                    if metadata.get("title"):
                        result_controls.append(
                            ft.Text(f"Database Title: {metadata['title']}")
                        )
            
            # Add create listing button
            result_controls.append(
                ft.ElevatedButton(
                    "Create eBay Listing",
                    icon=ft.icons.SHOPPING_CART,
                    on_click=lambda _: None  # To be implemented
                )
            )
            
            self.preview_container.content = ft.Column(
                controls=result_controls,
                spacing=10
            )
            
        except Exception as ex:
            self._update_status(f"Error: {str(ex)}")
            self.preview_container.content = ft.Text(
                f"Error: {str(ex)}",
                color=ft.colors.RED_400
            )
        
        finally:
            # Re-enable processing button
            self.process_button.disabled = False
            self.page.update()

    def clear_all(self, e):
        """Clear all selections and results."""
        self.current_file = None
        self.process_button.disabled = True
        self.clear_button.disabled = True
        self.preview_container.content = ft.Text(
            "No image selected",
            color=ft.colors.GREY_400
        )
        self._update_status("Ready")

def main():
    """Start the Flet application."""
    app = MediaProcessorApp()
    ft.app(target=app.initialize_ui)
