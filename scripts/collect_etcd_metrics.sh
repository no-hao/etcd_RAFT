#!/bin/bash
METRICS_DIR="$HOME/projects/etcd_rust/metrics"
mkdir -p "$METRICS_DIR"

echo "Ready to collect metrics. Start your Jepsen test now."
echo "Example: cd /jepsen/etcd && lein run test --workload register"
echo "Press Enter once your test has started and the cluster is running..."
read

echo "Collecting metrics every 10 seconds. Press Ctrl+C to stop..."

while true; do
  timestamp=$(date +%Y%m%d_%H%M%S)
  for node in {1..5}; do
    # Use a temporary file to check for changes
    temp_file=$(mktemp)
    if docker exec jepsen-control curl -sL http://n${node}:2379/metrics >"$temp_file"; then
      # Only save if file is different or doesn't exist
      if [ ! -f "$METRICS_DIR/etcd_metrics_n${node}_latest.txt" ] || ! cmp -s "$temp_file" "$METRICS_DIR/etcd_metrics_n${node}_latest.txt"; then
        mv "$temp_file" "$METRICS_DIR/etcd_metrics_n${node}_${timestamp}.txt"
        cp "$METRICS_DIR/etcd_metrics_n${node}_${timestamp}.txt" "$METRICS_DIR/etcd_metrics_n${node}_latest.txt"
        echo "New metrics saved for n${node} at ${timestamp}"
      fi
    else
      echo "Failed to collect metrics from n${node}"
    fi
    rm -f "$temp_file"
  done
  sleep 10
done
