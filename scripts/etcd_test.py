import subprocess
import time
import etcd3

def apply_latency(node, latency):
    cmd = f"docker exec {node} tc qdisc add dev eth0 root netem delay {latency}ms"
    subprocess.run(cmd, shell=True, check=True)

def remove_latency(node):
    cmd = f"docker exec {node} tc qdisc del dev eth0 root"
    subprocess.run(cmd, shell=True, check=True)

def run_test(latency):
    print(f"Running test with {latency}ms latency")
    
    # Apply latency to all nodes
    for node in ["etcd1", "etcd2", "etcd3"]:
        apply_latency(node, latency)
    
    # Connect to etcd
    client = etcd3.client(host="localhost", port=2379)
    
    # Perform write operations
    start_time = time.time()
    for i in range(100):
        client.put(f"/test/key{i}", f"value{i}")
    end_time = time.time()
    
    write_time = end_time - start_time
    print(f"Time taken for 100 writes: {write_time:.2f} seconds")
    
    # Perform read operations
    start_time = time.time()
    for i in range(100):
        client.get(f"/test/key{i}")
    end_time = time.time()
    
    read_time = end_time - start_time
    print(f"Time taken for 100 reads: {read_time:.2f} seconds")
    
    # Remove latency from all nodes
    for node in ["etcd1", "etcd2", "etcd3"]:
        remove_latency(node)
    
    return write_time, read_time

def main():
    latencies = [100, 250, 500, 1000]
    results = []
    
    for latency in latencies:
        write_time, read_time = run_test(latency)
        results.append((latency, write_time, read_time))
    
    print("\nResults:")
    print("Latency (ms) | Write Time (s) | Read Time (s)")
    print("-------------|----------------|---------------")
    for latency, write_time, read_time in results:
        print(f"{latency:12d} | {write_time:14.2f} | {read_time:13.2f}")

if __name__ == "__main__":
    main()
