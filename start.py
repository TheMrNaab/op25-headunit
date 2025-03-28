import subprocess, atexit, os, signal, socket

def free_port(port=8000):
    try:
        pids = subprocess.check_output(["lsof", "-ti", ":" + str(port)]).decode().split()
        for pid in pids:
            print(f"Killing process {pid} on port {port}")
            os.kill(int(pid), signal.SIGTERM)
    except subprocess.CalledProcessError:
        pass

def get_all_host_addresses(port=8000):
    # This returns all IP addresses associated with the hostname
    addresses = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), port, proto=socket.IPPROTO_TCP):
            addresses.add(info[4][0])
    except Exception as e:
        print("Error retrieving addresses:", e)
    return addresses

free_port(8000)
static_proc = subprocess.Popen([
    "python3", "-m", "http.server", "8000", "--directory", "/opt/op25-project/html"
])
