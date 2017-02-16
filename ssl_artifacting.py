#! /usr/bin/env python3
import argparse
import concurrent.futures
import datetime
import glob
import os
import shutil
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as etree

def create_db(hosts, ssl_app, ssl_app_path, output_directory, db):
    """
    Crates the inital database and populates it with the neccesary information
    to resume from.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # Create table for host information
    cursor.execute("create table hosts(host text, status text, start datetime, stop datetime)")
    # Create table for scan settings
    cursor.execute("create table scaninfo(app text, app_path text, output_directory text)")
    # Update scan settings table wit the information needed to resume the scan if it is killed.
    cursor.execute("insert into scaninfo values (?, ?, ?)", (ssl_app, ssl_app_path, output_directory))
    for host in hosts:
        # Adding hosts to the host table
        cursor.execute("insert into hosts(host, status) values (?, 'Not Started')", (host, ))
    conn.commit()
    cursor.close()
    conn.close()

def resume_scan(db):
    """
    Reads the information from a previously started scan database to continue from.
    """
    hosts = []
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("select host from hosts where status != 'Completed'")
    # Reads all hosts that are not completed and appends them to a list to return to the main function.
    for host in cursor.fetchall():
        hosts.append(host[0])
    cursor.execute("select * from scaninfo")
    scaninfo = cursor.fetchone()
    cursor.close()
    conn.commit()
    # returns ssl_app, ssl_app_path, output_directory, and hosts
    return [scaninfo[0], scaninfo[1], scaninfo[2], hosts]

def create_dir(directory):
    """
    This function is used to check if a directory and doesnt exist and if it
    doesnt create it.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def find_program(program, directory="/"):
    """
    This function will check the PATH environment for a program and then scan
    the filesystem for a mtach that is executable.
    """
    if shutil.which(program):
        return shutil.which(program)
    for root, dirs, files in os.walk(directory):
        # Check if the file is found
        if program in files:
            # Building the full path
            program_path = os.path.join(root, program)
            # Check if the file at the full path is executable
            if os.access(program_path, os.X_OK):
                return program_path
    print("Could not find {0}".format(program))
    quit()

def build_scan_list(file_list, file_format):
    """
    This function will build the list of host:port combinations from a std file,
    nessus or nmap files.
    """
    all_hosts = []

    if file_format == "nessus":
        # If the type is nessus iterate though the files present.
        for file in file_list:
            tree = etree.parse(file)
            for host in tree.findall('.//ReportHost'):
                for item in host:
                    # For each host go though the various plugins, if the plugin id is 56984 which is SSL/TLS service found append the host:port to a list and continue going though the nessus file.
                    if item.get('pluginID') == "56984":
                        hostinfo = host.get('name') + ":" + item.get('port')
                        all_hosts.append(hostinfo)
    elif file_format == "nmap":
        # Types of services that have ssl to look for in the nmap xml file.
        # Running nmap with -sV gives better reliablity for this.
        ssl_services=["https", "ssl", "ms-wbt-server"]
        # If the type is nmap iterate though the files present.
        for file in file_list:
            tree = tree.parse(file)
            for host in tree.findall('.//host'):
                for port in host.findall('.//port'):
                    # If the port is open and the service matches one of the
                    # ssl_services append the host:port to a list and continue
                    # going though the nmap file
                    if port.find('state').get('state') == "open":
                        if any(service in port.find('service').get('name') for service in  ssl_services):
                            hostinfo = host.find('.//address').get("addr") + ":" + port.get('portid')
                            all_hosts.append(hostinfo)
    elif file_format == "list":
        # If the type is list iterate though the files present and them to the list.
        # Expected list format is IP:PORT
        for file in file_list:
            all_hosts = all_hosts + [line.strip() for line in open(file, 'r')]

    # This takes the list and then removes duplicates that may have entered from processing multiple files.
    unique_hosts = list(set(all_hosts))
    return unique_hosts

def run_sslscan(sslscan_path, host, db, directory):
    """
    This function is used to call sslcan with the appropriate parameters
    for logging to xml and std output.
    It also handlings the updating of the sqlite3 file for the status and timestamps.
    """
    conn = sqlite3.connect(db)
    print ("Starting scan against {0} at {1}".format(host, str(datetime.datetime.now())))
    cursor = conn.cursor()
    # Update DB to show when scanning was started and that it is in progess
    cursor.execute("update hosts set start = current_timestamp, status = 'In Progress' where host = ?", (host,))
    conn.commit()
    host_output = host.replace(":","_")
    p = subprocess.Popen(([sslscan_path, "--no-failed", "--xml=" + directory + "/xml/" + host_output + ".xml", host]), stdout=subprocess.PIPE)
    try:
        # Not using a timeout here since sslscan handles this automatically
        (output, err) = p.communicate()
    except subprocess.TimeoutExpired:
        # This is not even used here but I have it in incase you are using a older version od sslscan and need to set it.
        # Kill the running process since we assume it timed out
        p.kill()
        # Update DB to show when scanning stopped and that it timed out
        cursor.execute("update hosts set stop = current_timestamp, status = 'Timeout' where host = ?", (host,))
        conn.commit()
    else:
        # Update DB to show when scanning stopped and that it was completed
        cursor.execute("update hosts set stop = current_timestamp, status = 'Completed' where host = ?", (host,))
        conn.commit()
    print ("Scan against {0} stopped at {1}".format(host, str(datetime.datetime.now())))
    output_file = directory + "/" + host_output
    f = open( output_file, 'w' )
    f.write( stroutput.decode("utf-8") )
    f.close()
    cursor.close()
    conn.close()

def run_testssl(testssl_path, host, db, directory):
    """
    This function is used to call testssl.sh with the appropriate parameters for
    logging to raw, csv and json.
    It also handlings the updating of the sqlite3 file for the status and timestamps.
    """
    conn = sqlite3.connect(db)
    # Update DB to show when scanning was started and that it is in progess
    print ("Starting scan against {0} at {1}".format(host, str(datetime.datetime.now())))
    cursor = conn.cursor()
    cursor.execute("update hosts set start = current_timestamp, status = 'In Progress' where host = ?", (host,))
    conn.commit()
    host_output = host.replace(":","_")
    p = subprocess.Popen(([testssl_path, "--warnings", "off", "--csvfile", directory + "/csv/" + host_output + ".csv", "--jsonfile",  directory + "/json/" + host_output + ".json", "--logfile",  directory + "/" + host_output, host]), stdout=subprocess.PIPE)
    try:
        # Using a timeout here since testssl hangs in some weird situations this is likely occur in lists and nmap
        (output, err) = p.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        # Kill the running process since we assume it timed out
        p.kill()
        # Update DB to show when scanning stopped and that it timed out
        cursor.execute("update hosts set stop = current_timestamp, status = 'Timeout' where host = ?", (host,))
        conn.commit()
    else:
        # Update DB to show when scanning stopped and that it was completed
        cursor.execute("update hosts set stop = current_timestamp, status = 'Completed' where host = ?", (host,))
        conn.commit()
    print ("Scan against {0} stopped at {1}".format(host, str(datetime.datetime.now())))
    cursor.close()
    conn.close()

if __name__ == "__main__":
    cmdparser = argparse.ArgumentParser(prog="ssl_artifacting.py", usage="""

    Usage: python3 %(prog)s [options]

    Options:
        -t              The type of files being processed by the script (nessus*, nmap, list)
        -i              The file(s) for input, can be a single file or files using a wildcard(/home/user/Downloads/*.nessus)
        -r              Resume SSL artifacting from previous database
        -o              Output directory
        --program       The ssl scanner that you are using (sslscan*, testssl.sh)
        --path          The full plath to the ssl program you wish to run (optional: makes it go faster if you supply it)
        --threads       The number of concurrent threads to use at once (default: 10)(maximum: 0)
    """.format(), formatter_class=argparse.RawTextHelpFormatter)
    cmdparser.add_argument("-t", "--type", default="nessus", help="Target host", choices=["nessus", "nmap", "list"])
    # Used nargs here cause some shells auto expand wildcards supplied so needed
    # a way to handle them. This will generate a list so that no other mangling
    # to the format is needed.
    cmdparser.add_argument("-i", "--input", default="",  nargs='*', help="The file(s) for input, can be a single file or files using a wildcard(/home/user/Downloads/*.nessus")
    cmdparser.add_argument("-r", "--resume", default="", help="SSL Artifacting Database to resume from")
    cmdparser.add_argument("-o", "--output", default="", help="Output directory")
    cmdparser.add_argument("--program", default="sslscan", help="The ssl scanner you are using", choices=["sslscan", "testssl.sh"])
    cmdparser.add_argument("--path", default="", help="The full path to the ssl program you wish to run")
    cmdparser.add_argument("--threads", default=10, type=int, help="The number of concurrent threads to use at once (default: 10)(maximum: 0)")

    cmdargs = cmdparser.parse_args()
    # I couldnt think of a clean way to do this better since it needs atleast 3 parameters and if you left one out it wasnt printing usage
    if len(sys.argv) < 3:
        cmdparser.print_usage()
        print('\n')
        exit()

    files = []
    if cmdargs.resume == "":
        # Build host list from files
        print("Beginning to build host list")
        # If you use wildcard masks in the input parameter and the system doesnt
        # automatically expand them the glob will handle it other wise just set
        # the list of files from the input.
        if "*" in cmdargs.input:
            files = glob.glob(cmdargs.input[0])
        else:
            files = cmdargs.input
        # Generate the list of hosts that will be scanned from the files
        hosts = build_scan_list(files, cmdargs.type)
        ssl_app = cmdargs.program
        if cmdargs.path == "":
            print("Looking for {0} this can take some time".format(ssl_app))
            ssl_app_path = find_program(cmdargs.program)
        else:
            # Can be either the full path, the parent directory or if it is in the path.
            # Check that if is not a directory and is executable set it other use run find_program in that directory.
            if not os.path.isdir(cmdargs.path) and os.access(cmdargs.path, os.X_OK):
                ssl_app_path = cmdargs.path
            else:
                print("Testing that {0} is present at the path provided".format(ssl_app))
                ssl_app_path = find_program(cmdargs.program, cmdargs.path)

        if cmdargs.output == "":
            # Generate the full os path for the output directory so that when resumed it can be resumed from anywhere in the file system.
            output_directory = os.getcwd() + "/ssl_artifacts_" + datetime.datetime.now().strftime('%s')
            print("Going to be using {0} found at {1}".format(ssl_app, ssl_app_path))
            print("Saving results in {0}".format(output_directory))
            create_dir(output_directory)
        else:
            # When the directory is supplied resolve the absolute path so you can resume from anywhere.
            output_directory = os.path.abspath(cmdargs.output)
            create_dir(output_directory)
            print("Saving results in {0}".format(output_directory))
        db = output_directory + "/ssl_artifacting.db"
        print("Saving creating database at {0}".format(db))
        create_db(hosts, ssl_app, ssl_app_path, output_directory, db)
    else:
        # Set the database and pull the appropriate information from it so we can restart our scan.
        db = cmdargs.resume
        ssl_app,ssl_app_path,output_directory,hosts = resume_scan(db)


    print("Beginning to artifact ssl hosts")
    with concurrent.futures.ThreadPoolExecutor(max_workers=cmdargs.threads) as executor:
        # Build the right directories and call the right ssl launcher function depending on what the user wants
        if ssl_app == "sslscan":
            create_dir(output_directory + "/xml")
            future_to_artifact = {executor.submit(run_sslscan, ssl_app_path, host, db, output_directory): host for host in hosts}
        elif ssl_app == "testssl.sh":
            create_dir(output_directory + "/csv")
            create_dir(output_directory + "/json")
            future_to_artifact = {executor.submit(run_testssl, ssl_app_path, host, db, output_directory): host for host in hosts}

        try:
            # This is in the try block so that i can catch the KeyboardInterrupt and clean up cleanly.
            for future in concurrent.futures.as_completed(future_to_artifact):
                host = future_to_artifact[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print('{0} generated an exception: {1}'.format(host, exc))
        except KeyboardInterrupt:
            # This is the handler for when a scan is running and you need to kill all running and queued threads
            print("The scan has been terminated to resume you can run python3 {0} --resume {1}".format(os.path.realpath(__file__), db))
            executor._threads.clear()
            concurrent.futures.thread._threads_queues.clear()
