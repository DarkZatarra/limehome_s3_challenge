import argparse
import boto3
import botocore
import time
import pickle
import os

CACHE_FILE_TEMPLATE = 'file_metadata_cache_{}.pkl'
BATCH_SIZE = 1000  # Define the size of each batch

def check_aws_credentials():
    try:
        boto3.client('sts').get_caller_identity()
        return True
    except botocore.exceptions.NoCredentialsError:
        print("AWS credentials are not set.")
        return False
    except botocore.exceptions.PartialCredentialsError:
        print("Incomplete AWS credentials.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def load_cache(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            cache = pickle.load(f)
            # Ensure the cache structure is correct
            if 'files' not in cache or 'search_string' not in cache:
                print("Cache file structure is invalid. Please delete the cache file and re-run the script.")
                exit(1)
            return cache
    return {'files': {}, 'search_string': ''}

def save_cache(file_name, cache):
    with open(file_name, 'wb') as f:
        pickle.dump(cache, f)

def get_file_content(s3, s3_bucket_name, file_key):
    file_obj = s3.get_object(Bucket=s3_bucket_name, Key=file_key)
    return file_obj['Body'].read()

def is_text_file(file_content):
    try:
        file_content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def process_file(s3, s3_bucket_name, file_key, substring, debug, content_get_error_files, content_assess_error_files):
    start_time = time.time()

    try:
        get_content_start_time = time.time()
        content = get_file_content(s3, s3_bucket_name, file_key)
        get_content_time = time.time() - get_content_start_time
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        if error_code == 'AccessDenied':
            if debug:
                print(f"Access denied for object: {file_key}")
            return None, 'access-denied'
        else:
            print(f"Failed to read object {file_key}: {error_code} - {error_message}")
            content_get_error_files.append(file_key)
            return None, 'content-get-error'
    except Exception as e:
        print(f"An unexpected error occurred while getting content for object {file_key}: {e}")
        content_get_error_files.append(file_key)
        return None, 'content-get-error'

    if (file_key.endswith('/') or file_key.endswith('$folder$')) and content == b'':
        file_type = 'folder'
        return None, file_type

    try:
        content_type_start_time = time.time()
        if is_text_file(content):
            file_type = 'text'
        else:
            file_type = 'binary'
        content_type_time = time.time() - content_type_start_time
    except Exception as e:
        print(f"An error occurred while assessing content type for object {file_key}: {e}")
        content_assess_error_files.append(file_key)
        return None, 'content-assess-error'

    if debug:
        print(f"Assessed content type for {file_key} as {file_type} in {content_type_time + get_content_time:.2f} seconds")

    if file_type == 'text':
        try:
            content = content.decode('utf-8')
            if substring in content:
                processing_time = time.time() - start_time
                if debug:
                    print(f"Processed object {file_key} in {processing_time:.2f} seconds")
                return file_key, 'text'
        except UnicodeDecodeError:
            content_assess_error_files.append(file_key)
            return None, 'content-assess-error'
        except Exception as e:
            print(f"An error occurred while processing text content for object {file_key}: {e}")
            content_assess_error_files.append(file_key)
            return None, 'content-assess-error'

    return None, file_type

def process_batch(s3, s3_bucket_name, batch_keys, etags, substring, cache, batch_number, debug):
    binary_count_cache = 0
    binary_count_non_cache = 0
    text_count_cache = 0
    text_count_non_cache = 0
    matched_text_cache = 0
    matched_text_non_cache = 0
    access_denied_count_cache = 0
    access_denied_count_non_cache = 0
    non_standard_storage_class_count_cache = 0
    non_standard_storage_class_count_non_cache = 0
    folder_count_cache = 0
    folder_count_non_cache = 0
    content_get_error_count_cache = 0
    content_get_error_count_non_cache = 0
    content_assess_error_count_cache = 0
    content_assess_error_count_non_cache = 0
    matching_files = []
    access_denied_files = []
    non_standard_storage_class_files = []
    folder_files = []
    content_get_error_files = []
    content_assess_error_files = []
    changed_keys = []

    batch_size = len(batch_keys)
    progress_checkpoints = [int(batch_size * 0.25), int(batch_size * 0.50), int(batch_size * 0.75), batch_size]
    progress_counter = 0

    print(f"========== Starting Batch {batch_number} ==========")

    for idx, file_key in enumerate(batch_keys):
        etag = etags[file_key]
        if file_key not in cache['files'] or cache['files'][file_key]['etag'] != etag:
            result, file_type = process_file(s3, s3_bucket_name, file_key, substring, debug, content_get_error_files, content_assess_error_files)
            if file_key in cache['files'] and cache['files'][file_key]['etag'] != etag:
                changed_keys.append(file_key)
            cache['files'][file_key] = {'etag': etag, 'file_type': file_type, 'contains_substring': bool(result)}
            if file_type == 'binary':
                binary_count_non_cache += 1
            elif file_type == 'text':
                text_count_non_cache += 1
                if result:
                    matched_text_non_cache += 1
            elif file_type == 'access-denied':
                access_denied_count_non_cache += 1
                access_denied_files.append(file_key)
            elif file_type == 'non-standard-storage-class':
                non_standard_storage_class_count_non_cache += 1
                non_standard_storage_class_files.append(file_key)
            elif file_type == 'folder':
                folder_count_non_cache += 1
                folder_files.append(file_key)
            elif file_type == 'content-get-error':
                content_get_error_count_non_cache += 1
            elif file_type == 'content-assess-error':
                content_assess_error_count_non_cache += 1
            if result:
                matching_files.append(result)
        else:
            cached_data = cache['files'][file_key]
            if cached_data['file_type'] == 'binary':
                binary_count_cache += 1
            elif cached_data['file_type'] == 'text':
                text_count_cache += 1
                if cached_data['contains_substring']:
                    matched_text_cache += 1
                    matching_files.append(file_key)
            elif cached_data['file_type'] == 'access-denied':
                access_denied_count_cache += 1
                access_denied_files.append(file_key)
            elif cached_data['file_type'] == 'non-standard-storage-class':
                non_standard_storage_class_count_cache += 1
                non_standard_storage_class_files.append(file_key)
            elif cached_data['file_type'] == 'folder':
                folder_count_cache += 1
                folder_files.append(file_key)
            elif cached_data['file_type'] == 'content-get-error':
                content_get_error_count_cache += 1
            elif cached_data['file_type'] == 'content-assess-error':
                content_assess_error_count_cache += 1

        progress_counter += 1
        if progress_counter in progress_checkpoints:
            print(f"Batch {batch_number} progress: {round((progress_counter / batch_size) * 100)}%")

    print(f"\nBatch {batch_number} processed:")
    print(f"- Text objects: {text_count_cache + text_count_non_cache} (Cache: {text_count_cache}, Non-cache: {text_count_non_cache})")
    print(f"- Binary objects: {binary_count_cache + binary_count_non_cache} (Cache: {binary_count_cache}, Non-cache: {binary_count_non_cache})")
    print(f"- Access denied paths: {access_denied_count_cache + access_denied_count_non_cache} (Cache: {access_denied_count_cache}, Non-cache: {access_denied_count_non_cache})")
    print(f"- Non-standard storage class objects: {non_standard_storage_class_count_cache + non_standard_storage_class_count_non_cache} (Cache: {non_standard_storage_class_count_cache}, Non-cache: {non_standard_storage_class_count_non_cache})")
    print(f"- Folder objects: {folder_count_cache + folder_count_non_cache} (Cache: {folder_count_cache}, Non-cache: {folder_count_non_cache})")
    print(f"- Content get errors: {content_get_error_count_cache + content_get_error_count_non_cache} (Cache: {content_get_error_count_cache}, Non-cache: {content_get_error_count_non_cache})")
    print(f"- Content assess errors: {content_assess_error_count_cache + content_assess_error_count_non_cache} (Cache: {content_assess_error_count_cache}, Non-cache: {content_assess_error_count_non_cache})")
    print(f"- Matched objects: {matched_text_cache + matched_text_non_cache} (Cache: {matched_text_cache}, Non-cache: {matched_text_non_cache})")
    print(f"- Changed keys: {changed_keys}")

    print(f"========== Finished Batch {batch_number} ==========")

    return (binary_count_cache, binary_count_non_cache, text_count_cache, text_count_non_cache,
            matched_text_cache, matched_text_non_cache, access_denied_count_cache, access_denied_count_non_cache,
            non_standard_storage_class_count_cache, non_standard_storage_class_count_non_cache,
            folder_count_cache, folder_count_non_cache, content_get_error_count_cache, content_get_error_count_non_cache,
            content_assess_error_count_cache, content_assess_error_count_non_cache, matching_files, access_denied_files,
            non_standard_storage_class_files, folder_files, content_get_error_files, content_assess_error_files, changed_keys)

def find_files_with_substring(s3_bucket_name, substring, debug=False):
    if not s3_bucket_name:
        print("Bucket name is not set.")
        return []
    
    if not check_aws_credentials():
        return []

    s3 = boto3.client('s3')
    matching_files = []
    access_denied_files = []
    non_standard_storage_class_files = []
    folder_files = []
    content_get_error_files = []
    content_assess_error_files = []

    cache_file = CACHE_FILE_TEMPLATE.format(s3_bucket_name)
    cache = load_cache(cache_file)

    # Invalidate cache if search string has changed
    if cache['search_string'] != substring:
        cache = {'files': {}, 'search_string': substring}

    total_files = 0
    total_binary_cache = 0
    total_binary_non_cache = 0
    total_text_cache = 0
    total_text_non_cache = 0
    total_matched_text_cache = 0
    total_matched_text_non_cache = 0
    total_access_denied_cache = 0
    total_access_denied_non_cache = 0
    total_non_standard_storage_class_cache = 0
    total_non_standard_storage_class_non_cache = 0
    total_folder_cache = 0
    total_folder_non_cache = 0
    total_content_get_error_cache = 0
    total_content_get_error_non_cache = 0
    total_content_assess_error_cache = 0
    total_content_assess_error_non_cache = 0

    try:
        paginator = s3.get_paginator('list_objects_v2')
        batch_counter = 0

        # Paginate through all objects in the bucket
        for page in paginator.paginate(Bucket=s3_bucket_name):
            file_keys = [obj['Key'] for obj in page.get('Contents', []) if obj.get('StorageClass') in [None, 'STANDARD']]
            etags = {obj['Key']: obj['ETag'] for obj in page.get('Contents', [])}
            non_standard_keys = [obj['Key'] for obj in page.get('Contents', []) if obj.get('StorageClass') not in [None, 'STANDARD']]
            total_non_standard_storage_class_non_cache += len(non_standard_keys)
            total_files += len(file_keys) + len(non_standard_keys)

            for batch_start in range(0, len(file_keys), BATCH_SIZE):
                batch_counter += 1
                batch_keys = file_keys[batch_start:batch_start + BATCH_SIZE]

                (binary_count_cache, binary_count_non_cache, text_count_cache, text_count_non_cache,
                 matched_text_cache, matched_text_non_cache, access_denied_count_cache, access_denied_count_non_cache,
                 non_standard_storage_class_count_cache, non_standard_storage_class_count_non_cache,
                 folder_count_cache, folder_count_non_cache, content_get_error_count_cache, content_get_error_count_non_cache,
                 content_assess_error_count_cache, content_assess_error_count_non_cache, batch_matching_files,
                 batch_access_denied_files, batch_non_standard_storage_class_files, batch_folder_files,
                 batch_content_get_error_files, batch_content_assess_error_files, changed_keys) = process_batch(
                    s3, s3_bucket_name, batch_keys, etags, substring, cache, batch_counter, debug)
                
                matching_files.extend(batch_matching_files)
                access_denied_files.extend(batch_access_denied_files)
                non_standard_storage_class_files.extend(batch_non_standard_storage_class_files)
                folder_files.extend(batch_folder_files)
                content_get_error_files.extend(batch_content_get_error_files)
                content_assess_error_files.extend(batch_content_assess_error_files)
                total_binary_cache += binary_count_cache
                total_binary_non_cache += binary_count_non_cache
                total_text_cache += text_count_cache
                total_text_non_cache += text_count_non_cache
                total_matched_text_cache += matched_text_cache
                total_matched_text_non_cache += matched_text_non_cache
                total_access_denied_cache += access_denied_count_cache
                total_access_denied_non_cache += access_denied_count_non_cache
                total_non_standard_storage_class_cache += non_standard_storage_class_count_cache
                total_non_standard_storage_class_non_cache += non_standard_storage_class_count_non_cache
                total_folder_cache += folder_count_cache
                total_folder_non_cache += folder_count_non_cache
                total_content_get_error_cache += content_get_error_count_cache
                total_content_get_error_non_cache += content_get_error_count_non_cache
                total_content_assess_error_cache += content_assess_error_count_cache
                total_content_assess_error_non_cache += content_assess_error_count_non_cache

            # Save updated cache after processing each batch
            save_cache(cache_file, cache)

    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        if error_code == 'AccessDenied':
            print(f"Access denied for bucket: {s3_bucket_name}")
        elif error_code == 'NoSuchBucket':
            print(f"The specified bucket does not exist: {s3_bucket_name}")
        else:
            print(f"Failed to list objects in bucket {s3_bucket_name}: {error_code} - {error_message}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    if total_files > 0:
        total_binary = total_binary_cache + total_binary_non_cache
        total_text = total_text_cache + total_text_non_cache
        total_matched_text = total_matched_text_cache + total_matched_text_non_cache
        total_access_denied = total_access_denied_cache + total_access_denied_non_cache
        total_non_standard_storage_class = total_non_standard_storage_class_cache + total_non_standard_storage_class_non_cache
        total_folder = total_folder_cache + total_folder_non_cache
        total_content_get_errors = total_content_get_error_cache + total_content_get_error_non_cache
        total_content_assess_errors = total_content_assess_error_cache + total_content_assess_error_non_cache

        print("\n========== Summary ==========")
        print(f"Total objects in the bucket: {total_files}")
        print(f"Total access denied paths: {total_access_denied}")
        print(f"Total non-standard storage class objects: {total_non_standard_storage_class}")
        print(f"Total binary objects: {total_binary}")
        print(f"Total text objects: {total_text}")
        print(f"Total folder objects: {total_folder}")
        print(f"Total content get errors: {total_content_get_errors}")
        print(f"Total content assess errors: {total_content_assess_errors}")
        print(f"Total matched text objects: {total_matched_text}")

        if debug and access_denied_files:
            print("\nAccess denied paths:")
            for path in access_denied_files:
                print(path)

        if debug and non_standard_storage_class_files:
            print("\nNon-standard storage class objects:")
            for path in non_standard_storage_class_files:
                print(path)

        if debug and folder_files:
            print("\nFolder objects:")
            for path in folder_files:
                print(path)

        if debug and content_get_error_files:
            print("\nContent get error objects:")
            for path in content_get_error_files:
                print(path)

        if debug and content_assess_error_files:
            print("\nContent assess error objects:")
            for path in content_assess_error_files:
                print(path)

        if matching_files:
            print(f"\nObjects keys containing the substring '{substring}':")
            for file in matching_files:
                print(file)
        else:
            print("\nNo objects identified with the specified string.")
        print("========== End of Summary ==========")

    return matching_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for a substring in text files within an S3 bucket.')
    parser.add_argument('s3_bucket_name', type=str, help='The name of the S3 bucket.')
    parser.add_argument('substring', type=str, help='The substring to search for.')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for detailed output.')

    args = parser.parse_args()

    find_files_with_substring(args.s3_bucket_name, args.substring, args.debug)
