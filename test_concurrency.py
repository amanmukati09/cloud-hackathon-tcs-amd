import requests
import concurrent.futures
import time
import random

BACKEND_URL = "http://localhost:8000"
NUM_SIMULTANEOUS_REQUESTS = 50  # Number of concurrent users to simulate

def setup_test_user():
    """Registers and logs in a test user to get a JWT token."""
    email = f"loadtest_{random.randint(1000, 9999)}@example.com"
    password = "StrongPassword123!"
    
    print(f"[*] Registering test user: {email}")
    requests.post(f"{BACKEND_URL}/auth/register", json={
        "email": email, "password": password, "full_name": "Load Tester"
    })
    
    res = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": email, "password": password
    })
    return res.json().get("access_token")

def simulate_user_request(request_id, token):
    """Simulates a user hitting the heavy AI /diagnose endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "logs": [
            f"[ERROR] Request {request_id}: Simulated application crash",
            "[WARNING] High memory usage detected"
        ]
    }
    
    start_time = time.time()
    try:
        # Firing the heavy AI route
        response = requests.post(f"{BACKEND_URL}/diagnose", json=payload, headers=headers)
        end_time = time.time()
        
        elapsed = round(end_time - start_time, 2)
        if response.status_code == 200:
            return True, elapsed, f"Req {request_id}: Success in {elapsed}s"
        else:
            return False, elapsed, f"Req {request_id}: Failed with {response.status_code} - {response.text}"
    except Exception as e:
        return False, 0, f"Req {request_id}: Crashed with {e}"

def run_load_test():
    print(f"🚀 Starting Concurrency Test with {NUM_SIMULTANEOUS_REQUESTS} simultaneous requests...\n")
    
    token = setup_test_user()
    if not token:
        print("❌ Failed to get auth token. Is the backend running?")
        return

    success_count = 0
    failure_count = 0
    times = []

    # Fire all 50 requests at the EXACT same time
    test_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_SIMULTANEOUS_REQUESTS) as executor:
        # Submit all tasks to the thread pool
        futures = [executor.submit(simulate_user_request, i, token) for i in range(NUM_SIMULTANEOUS_REQUESTS)]
        
        # As they complete, process the results
        for future in concurrent.futures.as_completed(futures):
            success, elapsed, msg = future.result()
            if success:
                success_count += 1
                times.append(elapsed)
            else:
                failure_count += 1
            print(msg)

    test_end = time.time()
    
    # --- Print Analytics ---
    print("\n" + "="*40)
    print("📊 LOAD TEST RESULTS")
    print("="*40)
    print(f"Total Requests:   {NUM_SIMULTANEOUS_REQUESTS}")
    print(f"Successful:       {success_count} ✅")
    print(f"Failed:           {failure_count} ❌")
    print(f"Total Test Time:  {round(test_end - test_start, 2)}s")
    if times:
        print(f"Avg AI Resp Time: {round(sum(times)/len(times), 2)}s")
        print(f"Max AI Resp Time: {round(max(times), 2)}s")
    print("="*40)
    
    if failure_count == 0:
        print("\n🏆 SYSTEM IS BULLETPROOF! SQLite WAL and Threadpooling are working perfectly.")
    else:
        print("\n⚠️ WARNING: Concurrency failures detected. Check the backend terminal for 'database is locked' or timeout errors.")

if __name__ == "__main__":
    run_load_test()