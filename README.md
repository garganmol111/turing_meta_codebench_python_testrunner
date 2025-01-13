# Meta CodeBench Python Test Runner

The `test_runner.py` script can be used to run tests on multiple files at the same time and generate test summary and coverage report for them.

## Usage

- In a folder, place the following files:
  - `test_runner.py`
  - `test.py` file containing the unit tests written in either `unittest` or `pytest`
  - all script files that contain the class/functions that are to be tested. none of the script files should be named `main.py`
- Install any dependencies using `pip install`
- Run the script using the command:
```sh
$ python test_runner.py
```

On running the test_runner, a test summary and coverage report will be present in both the console output and saved in a file called `test_result.log`
