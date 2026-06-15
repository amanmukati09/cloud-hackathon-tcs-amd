#!/bin/bash
cd /workspace/shared/aman/incident-router-hackathon
python dummy_sites/log_generator.py &
echo "✅ Log generator started (PID: $!)"
