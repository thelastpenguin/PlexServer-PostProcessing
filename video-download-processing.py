import argparse 
import os 
import subprocess 
import time


parser = argparse.ArgumentParser(description='Running post-processing on media files')
parser.add_argument('download_dir', help="the location of the media files")
parser.add_argument('output_dir', help="the location of the media files")
parser.add_argument('ignore_list', help="list of directories to ignore")
args = parser.parse_args()

print("beginning injestion of new downloads")

script_location = os.path.dirname(__file__)

ignore_list = map(lambda x: x.strip(), args.ignore_list.lower().split(","))

def scan_directory(directory):
    files = []
    for file in os.listdir(directory):
        if file == "." or file == "..": continue 
        if file in ignore_list: continue 
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            yield file_path 
        else:
            yield from scan_directory(file_path)

def run_filebot(inputdir, outputdir):
    env = os.environ.copy()
    env["INPUT"] = inputdir
    env["OUTPUT"] = outputdir
    p = subprocess.Popen(["sh", os.path.join(script_location, "run-filebot.sh")], env=env)
    p.wait()
    return p.returncode

def flood_remove_completed():
    p = subprocess.Popen(["sh", os.path.join(script_location, "flood-remove-completed.sh")])
    p.wait()
    return p.returncode


print("finally, having flood remove all downloads with status completed")
flood_remove_completed()

print("reading directory tree before filebot runs")
files_before = set(scan_directory(args.download_dir))

print("running filebot")
filebot_returncode = run_filebot(args.download_dir, args.output_dir)

if filebot_returncode == 0:
    print("removing files that were here before filebot ran UNLESS THEY ARE IN WHITELIST")
    curtime = time.time()
    for file in scan_directory(args.download_dir):
        file_age = curtime - os.path.getmtime(file) 
        # we don't remove files that are less than an hour old
        # or files that were added before filebot started
        if file in files_before and file_age >= 60 * 60: 
            print("\tremoving %s" % file)
            os.remove(file)
        else:
            print("\tskipping %s, it was not here when filebot started" % file)
else:
    print("WARNING!!! FILEBOT DID NOT EXIT WITH GOOD STATUS. REQUIRES MANUAL INTERVENTION")

def remove_empty_dirs(rootdir):
    count = 0
    for file in os.listdir(rootdir):
        if file == "." or file == "..": continue 
        file_path = os.path.join(rootdir, file)
        if os.path.isdir(file_path):
            count += remove_empty_dirs(file_path)
        else:
            count += 1

    if count == 0 and rootdir != args.download_dir:
        print("\tremoving empty directory %s" % rootdir)
        os.rmdir(rootdir)
    
    return count 

print("removing empty directories in the downloads dir")
remove_empty_dirs(args.download_dir)
# replace with this: find /path/to/uploadcache -type d -empty -delete
