import os
import hashlib
import json 


def hash_file(file_path):
    """
    Calculates the SHA-256 hash of a file's contents.
    Returns the hexadecimal digest of the hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks of 16 bytes
            for byte_block in iter(lambda: f.read(16), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error hashing file {file_path}: {e}")
        return None
def traverse_directory(directory_path):
    """
    Navigates to the specified directory and computes the hash for each file.
    Returns a dictionary mapping file paths to their corresponding hash values.
    """
    hashes = {}
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return hashes
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            full_path = os.path.join(root, file)
            normalized_path = os.path.abspath(full_path).replace("\\", "/")
            file_hash = hash_file(normalized_path)
            if file_hash:
                hashes[normalized_path] = file_hash
    return hashes
def generate_table(directory_path, json_filename="hash_table.json"):
    """
    Generates a hash table for all files in the specified directory and saves it as a JSON file.
    Returns a message indicating the completion of the hash table generation.
    """
    print(f"Traversing and hashing files in: {directory_path}...")
    computed_hashes = traverse_directory(directory_path)
    
    if not computed_hashes:
        print("No files found or unable to traverse the directory.")
        return
    
    # Structure the data as a list of {"filepath": ..., "hash": ...}
    hash_table = []
    for path, hash_value in computed_hashes.items():
        hash_table.append({"filepath": path, "hash": hash_value})
        print(f"File: {path}, Hash: {hash_value}")
    
    try:
        with open(json_filename, "w") as json_file:
            json.dump(hash_table, json_file, indent=4)
        print(f"Hash table generated and saved to {json_filename}.")
    except Exception as e:
        print(f"Error writing to JSON file {json_filename}: {e}")

def validate_hash(json_filename="hash_table.json"):
    """
    Validates the hashes of files against the stored hash table.
    Returns a message indicating whether each file's hash is valid or invalid.
    """
    try:
        with open(json_filename, "r") as json_file:
            stored_hashes = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: Hash table file '{json_filename}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Hash table file '{json_filename}' is not a valid JSON.")
        return
    
    for entry in stored_hashes:
        filepath = entry["filepath"]
        stored_hash = entry["hash"]
        
        if not os.path.exists(filepath):
            print(f"{filepath} has been deleted.")
            continue
        
        current_hash = hash_file(filepath)
        if current_hash == stored_hash:
            print(f"{filepath} hash is valid.")
        else:
            print(f"{filepath} hash is invalid.")
def main():
    """
    Main function to handle user input and call appropriate functions for generating or validating hash tables.
    """
    while True:
        print("\nSelect an option:")
        print("1. Generate a new hash table")
        print("2. Verify hashes")
        print("3. Exit")
        
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            directory_path = input("Enter the directory path to hash files: ").strip()
            generate_table(directory_path)
        elif choice == "2":
            validate_hash()
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select either 1, 2, or 3.")
main()