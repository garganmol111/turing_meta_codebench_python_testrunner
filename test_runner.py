import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

import coverage

CSV_FIELDNAMES = [
    "task_id",
    "task_type",
    "coverage",
    "solution.py",
    "solution.py_summary",
    "base_code.py",
    "base_code.py_summary",
    "incorrect_solution.py",
    "incorrect_solution.py_summary",
    "model1.py",
    "model1.py_summary",
    "model2.py",
    "model2.py_summary",
    "model3.py",
    "model3.py_summary",
    "model4.py",
    "model4.py_summary",
    "model5.py",
    "model5.py_summary",
    "model6.py",
    "model6.py_summary",
    "model7.py",
    "model7.py_summary",
    "model8.py",
    "model8.py_summary",
    "model9.py",
    "model9.py_summary",
    "model10.py",
    "model10.py_summary",
]


class TestRunner:
    def __init__(self, alternate_mode):
        self.root_dir = Path(".")
        self.tasks_dir = self.root_dir / "py_tasks"
        self.temp_folder = self.root_dir / "temp"
        self.temp_folder.mkdir(parents=True, exist_ok=True)
        self.solution_file = self.temp_folder / "solution.py"
        self.test_file = self.temp_folder / "test.py"
        self.metadata_file_name = "metadata.json"
        self.csv_file = self.root_dir / "test_result.csv"
        self.test_timeout = 30

        with open(self.csv_file, "w") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()

        self.summary = {"passed": [], "failed": []}
        self.alternate_mode = alternate_mode
        self.alternate_folder = "alternate_responses"

    def get_numeric_folders(self):
        """Get all folders with numeric names inside the tasks directory"""
        tasks_dir = self.tasks_dir

        # Check if the tasks directory exists
        if not tasks_dir.exists() or not tasks_dir.is_dir():
            print(f"❌ Tasks directory not found at {tasks_dir}")
            return []

        # Return all numeric folders inside the tasks directory
        return [
            folder
            for folder in tasks_dir.iterdir()
            if folder.is_dir() and folder.name.isdigit()
        ]

    def get_python_files(self, folder):
        """Get all Python files in a numeric folder, excluding test.py"""
        return [f for f in folder.glob("*.py") if f.name != "test.py"]

    def copy_file_contents(source_path: Path, destination_path: Path) -> None:
        """
        Copy contents from source file to destination file.
        Creates the destination file if it doesn't exist.
        """
        # Ensure source file exists
        if not source_path.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Create parent directories of destination if they don't exist
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy2(source_path, destination_path)

    def run_tests(self, folder, python_files):

        task_test_file = folder / "test.py"
        shutil.copy2(task_test_file, self.test_file)

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

        task_log = {"task_id": folder.parts[1]}

        with open(folder / self.metadata_file_name, "r") as metadata_file:
            metadata = json.load(metadata_file)
            task_log["task_type"] = metadata["task_type"]

        for file in python_files:
            shutil.copy2(file, self.solution_file)
            try:
                if file.parts[2] == "solution.py":
                    result = subprocess.run(
                        [
                            "coverage",
                            "run",
                            "-m",
                            "pytest",
                            str(self.test_file),
                            "--tb=line",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=self.test_timeout,
                    )

                    coverage_report = subprocess.run(
                        ["coverage", "report", "-m"], capture_output=True, text=True
                    )

                    if result.returncode == 0:
                        cov = coverage.Coverage()
                        cov.load()
                        tested_file = cov.get_data().measured_files()
                        tested_file_path = next(iter(tested_file))

                        analysis = cov.analysis(tested_file_path)
                        executed = analysis[1]  # Lines that were executed
                        missing = analysis[2]
                        total_lines = len(executed) + len(missing)
                        percentage = (
                            (len(executed) / total_lines * 100)
                            if total_lines > 0
                            else 0
                        )

                        task_log["coverage"] = round(percentage, 2)

                else:
                    result = subprocess.run(
                        ["pytest", str(self.test_file), "--tb=line"],
                        capture_output=True,
                        text=True,
                        timeout=self.test_timeout,
                    )
            except subprocess.TimeoutExpired:
                task_log[file.parts[-1]] = "FAIL"
                task_log[f"{file.parts[-1]}_summary"] = "TIMEOUT"
                continue

            task_log[file.parts[-1]] = "PASS" if result.returncode == 0 else "FAIL"
            task_log[f"{file.parts[-1]}_summary"] = result.stdout

        return task_log

    def write_to_csv(self, task_log):
        with open(self.csv_file, "a") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)

            filtered_log = {k: v for k, v in task_log.items() if k in CSV_FIELDNAMES}
            writer.writerow(filtered_log)

    def print_summary(self, task_log):

        print("Correct Solution:", task_log.get("solution.py", "FAIL"))
        print("Base Code:", task_log.get("base_code.py", "FAIL"))
        if self.alternate_mode:
            print("Incorrect solution:", task_log.get("incorrect_solution.py", "FAIL"))
            claude_pass = llama_pass = 0

            for i in range(1, 6):
                if task_log.get(f"model{i}.py", "FAIL") == "PASS":
                    claude_pass += 1

            for i in range(6, 11):
                if task_log.get(f"model{i}.py", "FAIL") == "PASS":
                    llama_pass += 1

            print("CLAUDE Pass Rate:", f"{claude_pass}/5")
            print("LLAMA Pass Rate:", f"{llama_pass}/5")

        print("---------")

    def cleanup(self):

        if self.temp_folder.exists():
            shutil.rmtree(self.temp_folder)

        coverage_files = [".coverage", ".coveragerc"]
        for file in coverage_files:
            if os.path.exists(file):
                os.remove(file)

        cache_dirs = ["__pycache__", ".pytest_cache"]
        for dir_name in cache_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

    def run(self):
        try:
            print("Starting test runner...")
            numeric_folders = self.get_numeric_folders()

            if not numeric_folders:
                print("No numeric folders found!")
                return

            print(f"Found {len(numeric_folders)} numeric folders to test.")

            for folder in numeric_folders:
                print(f"\nProcessing folder: {folder.name}")
                python_files = self.get_python_files(folder)
                if self.alternate_mode:
                    python_files += self.get_python_files(
                        folder / self.alternate_folder
                    )

                if not python_files:
                    print(f"No Python files found in folder {folder.name}!")
                    continue

                print(
                    f"Found {len(python_files)} Python files to test in folder {folder.name}."
                )

                task_log = self.run_tests(folder, python_files)
                self.write_to_csv(task_log)
                self.print_summary(task_log)

        finally:
            self.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run tests on multiple tasks using a single test file"
    )
    parser.add_argument(
        "-a",
        "--alternate",
        action="store_true",
        help="Include alternate responses in each task",
    )
    args = parser.parse_args()

    runner = TestRunner(alternate_mode=args.alternate)
    runner.run()
