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

    `pip install boto3`

## Usage

### Parameters

It would be better to have a fastapi endpoint returning a json, but that was not in scope, so I stayed lazy with regards to this.

- **s3_bucket_name:** The name of the S3 bucket to search.
- **substring:** The substring to search for within text files.
- **debug:** (Optional) If set to `True`, provides detailed debug output.

### Running the Script

1. Ensure that your AWS credentials are configured.
2. Run the script with the required parameters.

- **s3_bucket_name:** The name of the S3 bucket to search.
- **substring:** The substring to search for within text files.
- **debug:** (Optional) If set to `True`, provides detailed debug output.

### Example

```bash
python3 s3_string_search_v1.py <s3_bucket_name> <substring> [--debug]
```

`<s3_bucket_name>`: Replace with the name of your S3 bucket.
`<substring>`: Replace with the substring you want to search for.
`[--debug]`: Optional flag to enable debug mode for detailed output.

### Example Usage

To search for the substring "example" in the bucket "my-bucket" with debug mode enabled:

```
python3 s3_string_search_v1.py my-bucket example --debug
```

To run the script without debug mode:

```
python3 s3_string_search_v1.py my-bucket example
```

### Output

The script provides detailed batch and summary outputs, including:

- **Text objects**
- **Binary objects**
- **Folder objects**
- **Access denied paths**
- **Non-standard storage class objects**
- **Content get errors**
- **Content assess errors**
- **Matched text objects**
- **Changed keys**

### How this was developed
In order to understand what my approach was, please check [my approach](https://github.com/DarkZatarra/limehome_s3_challenge/DanielsApproach.MD)
