import etcd3
import time
import subprocess
import sys

def apply_latency(node, latency):
    print(f"Applying {latency}ms latency to {node}...")
    cmd = f"docker exec {node} tc qdisc add dev eth0 root netem delay {latency}ms"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Latency applied successfully to {node}")
    except subprocess.CalledProcessError as e:
        print(f"Error applying latency to {node}: {e}")
        sys.exit(1)

def remove_latency(node):
    print(f"Removing latency from {node}...")
    cmd = f"docker exec {node} tc qdisc del dev eth0 root"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Latency removed successfully from {node}")
    except subprocess.CalledProcessError as e:
        print(f"Error removing latency from {node}: {e}")

def run_test(client, latency):
    print(f"\nRunning test with {latency}ms latency")
    for node in ["etcd1", "etcd2", "etcd3", "etcd4", "etcd5"]:
        apply_latency(node, latency)
    
    # Write test
    print("Starting write test...")
    start_time = time.time()
    for i in range(100):
        try:
            client.put(f"/test/key{i}", f"value{i}")
            if i % 10 == 0:
                print(f"Completed {i} writes")
        except Exception as e:
            print(f"Error during write operation: {e}")
    write_time = time.time() - start_time
    print(f"Write test completed in {write_time:.2f} seconds")
    
    # Read test
    print("Starting read test...")
    start_time = time.time()
    for i in range(100):
        try:
            client.get(f"/test/key{i}")
            if i % 10 == 0:
                print(f"Completed {i} reads")
        except Exception as e:
            print(f"Error during read operation: {e}")
    read_time = time.time() - start_time
    print(f"Read test completed in {read_time:.2f} seconds")
    
    for node in ["etcd1", "etcd2", "etcd3", "etcd4", "etcd5"]:
        remove_latency(node)
    return write_time, read_time

def main():
    print("Connecting to ETCD...")
    try:
        client = etcd3.client(host="localhost", port=2379)
        print("Connected successfully")
    except Exception as e:
        print(f"Error connecting to ETCD: {e}")
        sys.exit(1)

    latencies = [0, 50, 100, 200, 500]
    results = []
    
    for latency in latencies:
        write_time, read_time = run_test(client, latency)
        results.append((latency, write_time, read_time))
    
    print("\nResults:")
    print("Latency (ms) | Write Time (s) | Read Time (s)")
    print("-------------|----------------|---------------")
    for latency, write_time, read_time in results:
        print(f"{latency:12d} | {write_time:14.2f} | {read_time:13.2f}")

if __name__ == "__main__":
    main()
