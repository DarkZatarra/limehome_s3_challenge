# S3 Substring Search Script

## Overview

This script iterates through all objects in a specified Amazon S3 bucket and searches for a given substring within text files. The script handles various object types, counts different categories of files, and provides detailed summaries and error handling.

## Features

- **Iterate through S3 bucket objects:** List and process objects in the specified S3 bucket.
- **Search for a substring:** Search for a specified substring within text files.
- **Categorize files:** Categorize files as text, binary, folder, non-standard storage class, access denied, content get error, and content assess error.
- **Cache results:** Cache file metadata and reuse it to improve performance on subsequent runs.
- **Detailed summaries:** Provide detailed summaries of the processing, including counts of different file types and errors.
- **Error handling:** Handle and count different types of errors, providing detailed information.

## Requirements

- Python 3.x
- Boto3 library
- Retry library

## Installation

1. Clone the repository or download the script.
2. Install the required libraries using pip:

    ```bash
    pip install boto3 retrying
    ```

## Usage

### Parameters

- **s3_bucket_name:** The name of the S3 bucket to search.
- **substring:** The substring to search for within text files.
- **debug:** (Optional) If set to `True`, provides detailed debug output.

### Example

```python
s3_bucket_name = 'your-s3-bucket-name'
substring = 'your-search-substring'
debug = True
matching_files = find_files_with_substring(s3_bucket_name, substring, debug)
