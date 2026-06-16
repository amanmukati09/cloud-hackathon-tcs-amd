python -c "
import os, time, random
from datetime import datetime
LOG_FILE = 'logs/live_stream.log'
os.makedirs('logs', exist_ok=True)
while True:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    r = random.random()
    if r < 0.6: line = f'[INFO] system: Request processed in {random.randint(10,200)}ms'
    elif r < 0.8: line = f'[ERROR] database: Connection timeout after {random.randint(1000,5000)}ms'
    elif r < 0.95: line = f'[WARNING] nginx: Memory usage {random.randint(80,95)}%'
    else: line = f'[CRITICAL] api-gateway: Service crashed'
    with open(LOG_FILE,'a') as f: f.write(f'{ts} {line}\n'); f.flush()
    time.sleep(0.5)
" 