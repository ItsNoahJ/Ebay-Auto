#!/usr/bin/env python3
"""
Main entry point module.
"""
import sys
import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="VHS Tape Scanner"
    )
    
    parser.add_argument(
        "--gui",
        help="Launch GUI application",
        action="store_true"
    )
    
    parser.add_argument(
        "--image",
        help="Process single image (CLI mode)",
        type=str
    )
    
    parser.add_argument(
        "--output",
        help="Output directory (CLI mode)",
        type=str
    )
    
    parser.add_argument(
        "--debug",
        help="Enable debug visualization",
        action="store_true"
    )
    
    parser.add_argument(
        "--verbose",
        help="Enable verbose output",
        action="store_true"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.gui:
        # Launch GUI
        from src.main_gui import run
        return run()
        
    elif args.image:
        # Process single image
        from src.cli import process_image
        
        # Create CLI args object
        class CliArgs:
            def __init__(self, args):
                self.image = args.image
                self.output = args.output
                self.debug = args.debug
                self.verbose = args.verbose
                
        return process_image(CliArgs(args))
        
    else:
        print("Please specify --gui or --image")
        return 1

if __name__ == "__main__":
    sys.exit(main())
