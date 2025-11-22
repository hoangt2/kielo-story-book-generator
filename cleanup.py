import shutil
import os
import argparse

def cleanup(output_dir="output"):
    """Removes the output directory and all its contents."""
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
            print(f"Successfully removed '{output_dir}' and all its contents.")
        except Exception as e:
            print(f"Error removing '{output_dir}': {e}")
    else:
        print(f"Directory '{output_dir}' does not exist.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup output directory")
    parser.add_argument("--dir", default="output", help="Directory to clean up")
    args = parser.parse_args()
    
    cleanup(args.dir)
