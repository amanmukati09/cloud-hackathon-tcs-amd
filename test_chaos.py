import requests
import concurrent.futures
import time
import random

BACKEND_URL = "http://localhost:8000"
NUM_SIMULTANEOUS_REQUESTS = 50

def setup_test_user():
    email = f"chaos_{random.randint(10000, 99999)}@example.com"
    password = "StrongPassword123!"
    requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password, "full_name": "Chaos Tester"})
    res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
    return res.json().get("access_token")

def simulate_random_user_action(request_id):
    """Randomly chooses to either Diagnose a log OR Chat with the AI."""
    token = setup_test_user()
    if not token:
        return False, 0, f"Req {request_id}: Auth Failed", "AUTH"
        
    headers = {"Authorization": f"Bearer {token}"}
    action_type = random.choice(["DIAGNOSE", "CHAT"])
    
    start_time = time.time()
    try:
        if action_type == "DIAGNOSE":
            payload = {"logs": [f"[ERROR] Request {request_id}: System anomaly detected in matrix."]}
            res = requests.post(f"{BACKEND_URL}/diagnose", json=payload, headers=headers)
        else:
            payload = {"message": f"Hello Copilot, can you help user {request_id} fix a server issue?"}
            res = requests.post(f"{BACKEND_URL}/chat/message", json=payload, headers=headers)
            
        end_time = time.time()
        elapsed = round(end_time - start_time, 2)
        
        if res.status_code == 200:
            return True, elapsed, f"Req {request_id} ({action_type}): Success in {elapsed}s", action_type
        else:
            return False, elapsed, f"Req {request_id} ({action_type}): Failed {res.status_code} - {res.text}", action_type
            
    except Exception as e:
        return False, 0, f"Req {request_id} ({action_type}): Crashed with {e}", action_type

def run_chaos_test():
    print(f"🌪️ Starting CHAOS Concurrency Test with {NUM_SIMULTANEOUS_REQUESTS} simultaneous requests...\n")
    
    success_diag, fail_diag = 0, 0
    success_chat, fail_chat = 0, 0
    times = []

    test_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_SIMULTANEOUS_REQUESTS) as executor:
        futures = [executor.submit(simulate_random_user_action, i) for i in range(NUM_SIMULTANEOUS_REQUESTS)]
        
        for future in concurrent.futures.as_completed(futures):
            success, elapsed, msg, action_type = future.result()
            print(msg)
            if success:
                times.append(elapsed)
                if action_type == "DIAGNOSE": success_diag += 1
                else: success_chat += 1
            else:
                if action_type == "DIAGNOSE": fail_diag += 1
                else: fail_chat += 1

    test_end = time.time()
    
    print("\n" + "="*45)
    print("📊 CHAOS TEST RESULTS")
    print("="*45)
    print(f"Total Requests:   {NUM_SIMULTANEOUS_REQUESTS}")
    print(f"✅ Diagnose Success: {success_diag} | ❌ Fails: {fail_diag}")
    print(f"✅ Chat Success:     {success_chat} | ❌ Fails: {fail_chat}")
    print(f"Total Test Time:  {round(test_end - test_start, 2)}s")
    if times:
        print(f"Avg AI Resp Time: {round(sum(times)/len(times), 2)}s")
    print("="*45)

if __name__ == "__main__":
    run_chaos_test()