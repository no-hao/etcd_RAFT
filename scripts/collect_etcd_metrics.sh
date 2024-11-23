#!/bin/bash

# Directory where metrics files will be stored - created if it doesn't exist
METRICS_DIR="$HOME/projects/etcd_rust/metrics"
mkdir -p "$METRICS_DIR"

# Initial user prompt to coordinate with test start
echo "Ready to collect metrics. Start your Jepsen test now."
echo "Example: cd /jepsen/etcd && lein run test --workload register"
echo "Press Enter once your test has started and the cluster is running..."
read

echo "Collecting metrics every 10 seconds. Will auto-stop after 5 consecutive failures..."

# Initialize failure tracking counters
consecutive_failures=0 # Tracks how many times in a row ALL nodes failed
MAX_FAILURES=3         # Number of consecutive complete failures before exit
# Complete failure means all 5 nodes failed in one round

# Main collection loop
while true; do
  # Create timestamp for this collection round
  timestamp=$(date +%Y%m%d_%H%M%S)
  # Track how many nodes failed in this specific round
  failure_this_round=0

  # Iterate through each etcd node
  for node in {1..5}; do
    # Create temporary file for comparison
    temp_file=$(mktemp)

    # Attempt to collect metrics from current node
    # -s makes curl silent (no progress meter)
    # -L follows redirects if any
    if docker exec jepsen-control curl -sL http://n${node}:2379/metrics >"$temp_file"; then
      # Check if this is first collection OR if metrics have changed
      # cmp -s returns 0 if files are identical
      if [ ! -f "$METRICS_DIR/etcd_metrics_n${node}_latest.txt" ] || ! cmp -s "$temp_file" "$METRICS_DIR/etcd_metrics_n${node}_latest.txt"; then
        # Save new metrics with timestamp and update 'latest' copy
        mv "$temp_file" "$METRICS_DIR/etcd_metrics_n${node}_${timestamp}.txt"
        cp "$METRICS_DIR/etcd_metrics_n${node}_${timestamp}.txt" "$METRICS_DIR/etcd_metrics_n${node}_latest.txt"
        echo "New metrics saved for n${node} at ${timestamp}"
      fi
    else
      # If curl fails, increment failure counter for this round
      echo "Failed to collect metrics from n${node}"
      failure_this_round=$((failure_this_round + 1))
    fi
    # Clean up temporary file whether we used it or not
    rm -f "$temp_file"
  done

  # After checking all nodes, evaluate failure state
  # If all 5 nodes failed in this round
  if [ $failure_this_round -eq 5 ]; then
    consecutive_failures=$((consecutive_failures + 1))
    echo "All nodes failed. Consecutive failure count: $consecutive_failures"
    # If we've hit our failure threshold, assume test is complete
    if [ $consecutive_failures -ge $MAX_FAILURES ]; then
      echo "Maximum consecutive failures reached. Assuming test is complete. Exiting..."
      exit 0
    fi
  else
    # If even one node succeeded, reset the consecutive failure counter
    consecutive_failures=0
  fi

  # Wait before next collection round
  sleep 10
done
