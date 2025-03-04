#!/usr/bin/env python
"""
Comprehensive test runner for the image processing system.
Executes unit tests, integration tests, and benchmarks with proper configurations.
"""
import os
import sys
import time
import locale
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def setup_environment():
    """Set up the test environment with required variables."""
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)
    os.environ["TEST_MODE"] = "1"
    # Ensure consistent encoding
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
    
def run_command(command, **kwargs):
    """Run a command and return its output and error output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            **kwargs
        )
        return result.stdout, result.stderr, result.returncode == 0
    except Exception as e:
        return "", str(e), False

def create_test_report(results, output_dir):
    """Create a detailed test report."""
    report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_dir) / f"test_report_{report_time}.txt"
    
    with open(report_path, "w", encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Image Processing System Test Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for test_type, data in results.items():
            f.write(f"\n{test_type.upper()}\n")
            f.write("-" * len(test_type) + "\n")
            f.write(f"Duration: {data['duration']:.2f} seconds\n")
            f.write(f"Status: {'PASSED' if data['success'] else 'FAILED'}\n")
            if data.get("metrics"):
                f.write("\nPerformance Metrics:\n")
                for metric, value in data["metrics"].items():
                    f.write(f"  {metric}: {value}\n")
            
            # Write both stdout and stderr
            if data.get("stdout"):
                f.write("\nStandard Output:\n")
                f.write(data["stdout"])
            if data.get("stderr"):
                f.write("\nError Output:\n")
                f.write(data["stderr"])
            
            f.write("\n" + "=" * 80 + "\n")
    
    print(f"\nDetailed test report saved to: {report_path}")
    return report_path

def run_test_suite(test_type, coverage=False):
    """Run a specific test suite and return results."""
    print(f"\nRunning {test_type}...")
    start_time = time.time()
    
    command = ["pytest", "-v", "-m", test_type]
    if coverage and test_type == "unit":
        command.append("--cov=src")
    elif not coverage:
        command.append("--no-cov")
        
    stdout, stderr, success = run_command(command)
    
    # Print any error output immediately
    if stderr:
        print("\nTest Output:")
        print("-" * 40)
        print(stderr)
    
    return {
        "success": success,
        "duration": time.time() - start_time,
        "stdout": stdout,
        "stderr": stderr
    }

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("--output-dir", default="test_reports",
                      help="Directory for test reports")
    parser.add_argument("--skip-benchmarks", action="store_true",
                      help="Skip performance benchmark tests")
    parser.add_argument("--coverage", action="store_true",
                      help="Generate coverage report")
    parser.add_argument("--test-type", choices=["unit", "integration", "gui", "benchmark"],
                      help="Run only specific test type")
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up environment
    setup_environment()
    
    results = {}
    test_types = (
        ["unit", "integration", "gui"]
        if not args.test_type
        else [args.test_type]
    )
    
    # Run selected test suites
    for test_type in test_types:
        results[f"{test_type}_tests"] = run_test_suite(
            test_type,
            coverage=args.coverage and test_type == "unit"
        )
    
    # Run benchmarks if not skipped and either no specific type is selected
    # or benchmark type is specifically requested
    if (not args.skip_benchmarks and 
        (not args.test_type or args.test_type == "benchmark")):
        results["benchmarks"] = run_test_suite("benchmark")
    
    # Generate coverage report if requested
    if args.coverage:
        print("\nGenerating coverage report...")
        stdout, stderr, success = run_command([
            "coverage",
            "html",
            "--directory",
            str(output_dir / "coverage")
        ])
        if success:
            print(f"Coverage report generated in {output_dir}/coverage/index.html")
        else:
            print(f"Failed to generate coverage report:\n{stderr}")
    
    # Create and save test report
    report_path = create_test_report(results, output_dir)
    
    # Print summary
    print("\nTest Summary:")
    print("=" * 40)
    all_passed = all(r["success"] for r in results.values())
    for test_type, data in results.items():
        status = "PASSED" if data["success"] else "FAILED"
        print(f"{test_type:20s}: {status:10s} ({data['duration']:.2f}s)")
    
    if not all_passed:
        print("\nSome tests failed. See error output above and check the test report for details.")
        
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
