# Meta CodeBench Python Test Runner

The `test_runner.py` script can be used to run tests on multiple tasks in bulk, and generate a csv reporet for all tasks

## Environment Setup

- Folder structure should look like:

```bash
root/  
├─ test_runner.py  
├─ py_tasks/  
│  ├─ 123456/  
│  │  ├─ alternate_responses/  
│  │  │  ├─ model1.py  
│  │  │  ├─ incorrect_response.py  
│  │  ├─ base_code.py  
│  │  ├─ metadata.json  
│  │  ├─ solution.py  
│  │  ├─ tests.py  
```

- Install all required packages for running tests on all tasks

## Usage

There are 2 modes of execution:
1. Normal Mode - Only base_code and correct solution are tested
2. Alternate Mode - All files including the ones present in alternate_responses folder are tested

```sh
$ python test_runner.py
$ python test_runner.py -a # alternate mode
$ python test_runner.py --alternate # alternate mode
```

On running the script, a csv file called `test_log.csv` will be created which contains test details for each task

