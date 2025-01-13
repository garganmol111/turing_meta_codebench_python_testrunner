import os
import shutil
import subprocess
from pathlib import Path


class TestRunner:
    def __init__(self):
        self.root_dir = Path(".")
        self.main_file = self.root_dir / "main.py"
        self.test_file = self.root_dir / "test.py"
        self.log_file = self.root_dir / f"test_result.log"
        with open(self.log_file, "w"):
            pass

    def get_python_files(self):
        """Get all Python files except test.py and test_runner.py"""
        return [
            f
            for f in self.root_dir.glob("*.py")
            if f.name not in ["test.py", "test_runner.py", "main.py"]
        ]

    def copy_file_content(self, source_file):
        """Copy content from source file to main.py"""
        shutil.copy2(source_file, self.main_file)

    def run_tests(self, source_file):
        """Run pytest with coverage for the current main.py"""
        # Create .coveragerc file to omit test.py
        with open(".coveragerc", "w") as f:
            f.write(
                """[run]
omit = test.py
            
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError"""
            )

        # Run pytest with coverage
        result = subprocess.run(
            [
                "coverage",
                "run",
                "-m",
                "pytest",
                "-v",
                "test.py",
            ],  # Removed -v for summary
            capture_output=True,
            text=True,
        )

        # Read and modify coverage report
        coverage_report = subprocess.run(
            ["coverage", "report", "-m"], capture_output=True, text=True
        )

        # Replace 'main.py' with original filename in coverage report
        modified_coverage = coverage_report.stdout.replace("main.py", source_file.name)

        # Extract just the summary part from pytest output
        summary = ""
        for line in result.stdout.split("\n"):
            if "short test summary info" in line:
                # Found the start of summary
                summary = "=== Test Summary ===\n"
                continue
            if summary and line.strip():
                if "in" in line and "s ===" in line:  # This is the timing line
                    summary += line + "\n"
                    break
                summary += line + "\n"

        return {
            "file": source_file.name,
            "tests_passed": result.returncode == 0,
            "test_output": summary if summary else "No test summary available.",
            "coverage_report": modified_coverage,
        }

    def log_results(self, results):
        """Log test results and coverage report to file"""
        with open(self.log_file, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Test Results for: {results['file']}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Tests {'PASSED' if results['tests_passed'] else 'FAILED'}\n\n")
            f.write("Coverage Report:\n")
            f.write(results["coverage_report"])
            f.write("\nTest Output Summary:\n")
            f.write(results["test_output"])
            f.write("\n")

    def print_results(self, results):
        """Print results to console"""
        print(f"\nResults for: {results['file']}")
        print(f"Tests {'PASSED' if results['tests_passed'] else 'FAILED'}")
        print("\nCoverage Report:")
        print(results["coverage_report"])
        print("-" * 80)

    def cleanup(self):
        """Remove all temporary files"""
        # Remove main.py
        if self.main_file.exists():
            self.main_file.unlink()

        # Remove coverage files
        coverage_files = [".coverage", ".coveragerc"]
        for file in coverage_files:
            if os.path.exists(file):
                os.remove(file)

        # Remove any pytest cache directories
        cache_dirs = ["__pycache__", ".pytest_cache"]
        for dir_name in cache_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

    def run(self):
        """Main execution method"""
        try:
            print("Starting test runner...")
            python_files = self.get_python_files()

            if not python_files:
                print("No Python files found to test!")
                return

            print(f"Found {len(python_files)} Python files to test.")

            for file in python_files:
                print(f"\nTesting {file.name}...")
                self.copy_file_content(file)
                results = self.run_tests(file)
                self.print_results(results)
                self.log_results(results)

            print(f"\nTest execution completed. Results saved to {self.log_file}")

        finally:
            self.cleanup()


if __name__ == "__main__":
    runner = TestRunner()
    runner.run()
