"""
Main entry point for the Media Processor application.
"""
from src.config import initialize_config
from src.flet_gui.app import main as flet_main

def main():
    """Initialize and start the application."""
    # Initialize configuration
    settings = initialize_config()
    
    # Start the Flet GUI
    flet_main()
