import etcd3
import time
import subprocess
import sys
import statistics
import json

def setup_tc(node):
    """Ensure tc is properly set up on the node"""
    cmds = [
        f"docker exec {node} tc qdisc del dev eth0 root 2>/dev/null || true",
        f"docker exec {node} tc qdisc add dev eth0 root handle 1: prio",
        f"docker exec {node} tc qdisc add dev eth0 parent 1:3 handle 30: netem"
    ]
    for cmd in cmds:
        subprocess.run(cmd, shell=True, check=False)

def apply_latency(node, latency):
    print(f"Applying {latency}ms latency to {node}...")
    try:
        # First ensure tc is set up
        setup_tc(node)
        
        # Apply the latency
        cmd = f"docker exec {node} tc qdisc change dev eth0 parent 1:3 handle 30: netem delay {latency}ms"
        subprocess.run(cmd, shell=True, check=True)
        return True
    except Exception as e:
        print(f"Error applying latency to {node}: {e}")
        return False

def get_leader_info():
    """Get current leader information"""
    cmd = "docker exec etcd1 etcdctl endpoint status --cluster -w json"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            endpoints = json.loads(result.stdout)
            for endpoint in endpoints:
                if isinstance(endpoint, dict) and 'Status' in endpoint:
                    if endpoint['Status']['leader'] == endpoint['Status']['header']['member_id']:
                        return endpoint['Endpoint'].split(':')[0]
        return None
    except Exception as e:
        print(f"Error getting leader info: {e}")
        return None

def get_raft_metrics(node):
    """Get RAFT metrics using etcdctl"""
    cmd = f"docker exec {node} etcdctl endpoint metrics"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        metrics = {}
        for line in result.stdout.split('\n'):
            if line.startswith('etcd_server_proposals_committed_total'):
                metrics['proposals_committed'] = float(line.split()[1])
            elif line.startswith('etcd_server_proposals_applied_total'):
                metrics['proposals_applied'] = float(line.split()[1])
            elif line.startswith('etcd_server_leader_changes_seen_total'):
                metrics['leader_changes'] = float(line.split()[1])
        return metrics
    except Exception as e:
        print(f"Error getting RAFT metrics: {e}")
        return None

def test_raft_consensus(nodes, latency):
    """Test RAFT consensus under specific latency"""
    results = {
        'consensus_time': [],
        'leader_changes': 0,
        'proposals_committed': 0,
        'proposals_applied': 0
    }
    
    # Get initial metrics
    initial_metrics = {}
    for node in nodes:
        metrics = get_raft_metrics(node)
        if metrics:
            initial_metrics[node] = metrics
    
    # Apply latency
    for node in nodes:
        if not apply_latency(node, latency):
            return None
    
    # Test consensus operations
    client = etcd3.client(host="localhost", port=2379)
    for i in range(5):
        start_time = time.time()
        try:
            key = f"test_key_{time.time()}"
            client.put(key, "test_value")
            results['consensus_time'].append(time.time() - start_time)
        except Exception as e:
            print(f"Consensus operation failed: {e}")
        time.sleep(1)
    
    # Get final metrics
    final_metrics = {}
    for node in nodes:
        metrics = get_raft_metrics(node)
        if metrics:
            final_metrics[node] = metrics
            
    # Calculate metric differences
    for node in nodes:
        if node in initial_metrics and node in final_metrics:
            results['proposals_committed'] += (
                final_metrics[node]['proposals_committed'] - 
                initial_metrics[node]['proposals_committed']
            )
            results['proposals_applied'] += (
                final_metrics[node]['proposals_applied'] - 
                initial_metrics[node]['proposals_applied']
            )
            results['leader_changes'] += (
                final_metrics[node]['leader_changes'] - 
                initial_metrics[node]['leader_changes']
            )
    
    # Calculate averages
    if results['consensus_time']:
        results['avg_consensus_time'] = statistics.mean(results['consensus_time'])
    
    return results

def main():
    print("Starting ETCD RAFT consensus test...")
    nodes = ["etcd1", "etcd2", "etcd3", "etcd4", "etcd5"]
    
    try:
        latencies = [0, 50, 100, 200]
        results = []
        
        for latency in latencies:
            print(f"\nTesting with {latency}ms latency")
            test_results = test_raft_consensus(nodes, latency)
            if test_results:
                results.append((latency, test_results))
                print(f"Results for {latency}ms latency:")
                print(f"Average consensus time: {test_results['avg_consensus_time']:.3f}s")
                print(f"Proposals committed: {test_results['proposals_committed']}")
                print(f"Proposals applied: {test_results['proposals_applied']}")
                print(f"Leader changes: {test_results['leader_changes']}")
    
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        # Cleanup
        for node in nodes:
            subprocess.run(f"docker exec {node} tc qdisc del dev eth0 root 2>/dev/null || true", 
                         shell=True, check=False)

if __name__ == "__main__":
    main()
