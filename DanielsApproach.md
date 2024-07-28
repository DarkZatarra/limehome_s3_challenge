## Development Approach and Challenges

### Problems Identified While Developing

- **Need to show all objects**
- **Few files vs a lot of files**
- **Big files vs small files**
- **Identifying the content type**

Each object has metadata, and by default, AWS assigns the `Content-Type` (a system-defined metadata) to a value. For text files, `.txt` files are recognized as `text/plain`.

#### Issues Encountered:

- Renaming a binary file to `binary.txt` and uploading it still recognizes it as `text/plain`, which is incorrect.
- Checking the content type automatically using a Python method to verify if the content is binary or not.
- Executing this method takes a lot of time, so processed files (object key + etag + content type + search string) are saved to a pickle file for later use. This approach is vulnerable to content type changes but provides some help.
- In order to efficiently process only the files which were changed I thought of comparing the bulk content page metadata with the pickle file to generate the list for processing because it will be faster than iterating through each key and checking it against the pickle file.

### Development Steps

#### Dummy Approach (Search in all objects ending with .txt):

1. List all objects
2. Filter objects ending with `.txt`
3. Loop through file contents and search for the string
4. If the string is present, save the object key in a list
5. Print the list

##### Problems:

1. Text files are not only those ending with `.txt`; for example, a file ending with `.json` is also a text file.
2. The `list_objects` only returns 1000 items, so pagination is needed to get them all.

#### A better Approach (Search in all objects with Content-Type: text/plain):

1. List all objects using a paginator
2. Check if the page content returns the metadata with regards to Content-Type (it doesn't)
3. For each key in the page, get metadata
4. If metadata content-type = `text/plain`, search for the string in the object
5. If the string is found, append to the list
6. Return the list

##### Problems:

1. Getting metadata for each object is slow as you need to run `get metadata` for each key (there is no bulk option).
2. Renaming a binary file to `whatever.txt` changes the metadata to `text/plain`, which is incorrect.

#### Complex Approach:

1. List all objects using a paginator
2. Loop through page keys and run a method to check if the file is binary or not (against UTF-8)
3. If it's not binary, search the string
4. If the string is found, add to the list
5. Return the list

##### Problems:

- Extremely slow.

### Best Approach:

1. List all objects using a paginator.
2. For all objects in the page, do a bulk query in the pickle to return only the objects for which the etag (hash - content of the file) was modified. Return the keys which were modified or missing in the pickle.
3. Loop through returned keys and run the method to check if the file is binary or not.
4. Save the outcome in a pickle or anywhere cheap that you can reuse later:
    - Bucket in the name of the pickle file
    - Object key as index
    - Etag as hash
    - File type returned by the method
    - The search substring (as initially the results from the cache was returned despite the search substring being changed)
5. If the file is not binary, search for the string.
6. If the string is found, add to the list.
7. Return the list.
8. I didn't mention unit testing/code coverage - these are possible but I never mocked S3 and I don't focused my time on explaining the concept and make it work on multiple cases

##### Problems:

- Still quite slow for first run against a lot of files or big files but I'm not aware of any possibility of doing it faster using AWS existing calls

### Challenges Not Considered:

- Multipart upload (I did not looked into this but I've seen something in AWS documentation mentioning this and I think it might create problems)
- Ignored files from Glacier/Non-Standard storage.

### Other Ideas:

- In an environment where data is structured and you need to look in S3 buckets, you can use Athena + Glue. This will add partitions (data-based most of the time, but you can define others if needed) and you can search (pretty fast) for anything that you are interested in (as long as you know what you need). This is good for structured text data, but it applies to formats like CSV, JSON, Parquet, and/or compressed versions of these files under GZIP or Snappy format. In the end you will end up having an SQL like database where you can run SQL Queries or use Amazon QuickSight for visual GInsights

### Testing (as mentioned no unit testing or other type of testing but I did some "live" testing)

I used [GrayHatWarfare S3 Buckets](https://buckets.grayhatwarfare.com/) for testing.
