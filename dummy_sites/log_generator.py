"""
Realistic Log Generator
Simulates a production website with various failure scenarios.
Writes logs to logs/live_stream.log
"""

import sys, os, time, random
from datetime import datetime

LOG_DIR = "logs"
SCENARIO = sys.argv[1] if len(sys.argv) > 1 else "default"
LOG_FILE = os.path.join(LOG_DIR, f"{SCENARIO}_stream.log")

os.makedirs(LOG_DIR, exist_ok=True)


# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

SCENARIOS = [
    "normal",           # 70% normal traffic
    "db_errors",        # 10% database errors
    "memory_leak",      # 5% memory warnings
    "timeout_spike",    # 5% connection timeouts
    "cascading_failure",# 3% multiple services failing
    "recovery"          # 7% system recovery messages
]

COMPONENTS = ["nginx", "api-gateway", "user-service", "payment-service",
              "database", "redis", "auth-service"]

def generate_log_line(scenario=None):
    """Generate a realistic log line based on scenario."""
    if scenario is None:
        scenario = random.choices(
            SCENARIOS,
            weights=[70, 10, 5, 5, 3, 7],
            k=1
        )[0]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    component = random.choice(COMPONENTS)

    if scenario == "normal":
        templates = [
            f"[INFO] {component}: Request processed successfully in {random.randint(10,200)}ms",
            f"[INFO] {component}: Health check passed",
            f"[INFO] {component}: Cache hit ratio {random.randint(80,99)}%",
            f"[DEBUG] {component}: Connection pool size {random.randint(5,20)}",
        ]
    elif scenario == "db_errors":
        templates = [
            f"[ERROR] database: Connection timeout after {random.randint(1000,5000)}ms",
            f"[ERROR] database: Deadlock detected in transaction",
            f"[CRITICAL] database: Connection pool exhausted",
            f"[ERROR] database: Query failed - relation 'orders' does not exist",
        ]
    elif scenario == "memory_leak":
        templates = [
            f"[WARNING] {component}: Memory usage {random.randint(85,95)}%",
            f"[WARNING] {component}: GC overhead limit reached",
            f"[CRITICAL] {component}: Out of memory error - process killed",
        ]
    elif scenario == "timeout_spike":
        templates = [
            f"[ERROR] {component}: Request timeout after {random.randint(30,60)}s",
            f"[ERROR] {component}: Upstream service unavailable",
            f"[WARNING] {component}: Slow query detected ({random.randint(5,30)}s)",
        ]
    elif scenario == "cascading_failure":
        failed_comps = random.sample(COMPONENTS, 3)
        templates = [
            f"[CRITICAL] {failed_comps[0]}: Service crashed",
            f"[ERROR] {failed_comps[1]}: Dependency failure from {failed_comps[0]}",
            f"[ERROR] {failed_comps[2]}: Circuit breaker open for {failed_comps[0]}",
        ]
    else:  # recovery
        templates = [
            f"[INFO] {component}: Service restarted successfully",
            f"[INFO] {component}: Connection pool restored",
            f"[INFO] {component}: Health check passed after recovery",
        ]

    return f"{timestamp} {random.choice(templates)}"

    
def start_generator(duration_seconds=3600, lines_per_second=2):
    print(f"🚀 Generator {SCENARIO} -> {LOG_FILE}")
    end_time = time.time() + duration_seconds
    line_count = 0
    with open(LOG_FILE, "a") as f:
        while time.time() < end_time:
            line = generate_log_line()
            f.write(line + "\n")
            line_count += 1
            f.flush()
            time.sleep(1 / lines_per_second)

if __name__ == "__main__":
    start_generator()