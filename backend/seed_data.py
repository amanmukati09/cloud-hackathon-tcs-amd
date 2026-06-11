import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import bcrypt
bcrypt.__about__ = bcrypt
from passlib.context import CryptContext

# Import your database components
from models import User, Incident, ChatSession, ChatMessage, EscalationTicket, engine, SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- REALISTIC DEMO DATA POOLS ---
NAMES = ["Alice Chen", "Bob Smith", "Charlie Davis", "Diana Prince", "Evan Wright", "Fiona Gallagher", "George Halpert", "Hannah Abbott", "Ian Malcolm", "Jenny Humphrey"]
DOMAINS = ["tcs.com", "amd.com", "techcorp.io", "devops-ninja.net"]

LOG_SNIPPETS = [
    (
        "[CRITICAL] OutOfMemoryError: Java heap space in worker-node-04\n[INFO] Restarting JVM...",
        "Type: Resource Exhaustion | Severity: CRITICAL",
        "Cause: Memory leak in background indexing job.\nConfidence: 0.95\nEvidence: Heap space dumps over 4 hours.\nFactors: High user traffic.",
        "Immediate: Restart worker-node-04.\nAutomated: Scale up JVM Heap to 4GB.\nEscalate: True\nRecovery: 5 mins\nPrevention: Profile JVM memory allocation."
    ),
    (
        "[ERROR] pg_connect: Connection refused on port 5432\n[FATAL] Database completely unreachable.",
        "Type: Database Outage | Severity: CRITICAL",
        "Cause: PostgreSQL service crashed due to max_connections limit.\nConfidence: 0.88\nEvidence: pg_stat_activity limits hit.\nFactors: Unoptimized connection pooling.",
        "Immediate: Increase max_connections in pg_hba.conf.\nAutomated: Terminate idle connections.\nEscalate: True\nRecovery: 2 mins\nPrevention: Implement PgBouncer."
    ),
    (
        "[WARN] Nginx 502 Bad Gateway upstream server timeout\n[INFO] Retrying connection...",
        "Type: Network Timeout | Severity: HIGH",
        "Cause: Upstream application server (Gunicorn) is frozen.\nConfidence: 0.91\nEvidence: 502 HTTP status codes.\nFactors: CPU spiking on App Server.",
        "Immediate: Restart Gunicorn service.\nAutomated: Route traffic to backup server.\nEscalate: False\nRecovery: 1 min\nPrevention: Add rate limiting."
    ),
    (
        "[ERROR] Uncaught TypeError: Cannot read properties of undefined (reading 'map')",
        "Type: Application Exception | Severity: MEDIUM",
        "Cause: Frontend passing null array to map function.\nConfidence: 0.99\nEvidence: Stack trace line 42 app.js.\nFactors: Missing API data validation.",
        "Immediate: Rollback latest frontend deployment.\nAutomated: None.\nEscalate: False\nRecovery: 10 mins\nPrevention: Add optional chaining (obj?.map)."
    ),
    (
        "[WARN] High latency detected on Redis cache: 450ms ping",
        "Type: Performance Degradation | Severity: LOW",
        "Cause: Redis memory eviction policy triggered constantly.\nConfidence: 0.75\nEvidence: latency spikes correlating with cache misses.\nFactors: Cache size too small.",
        "Immediate: Flush least used cache keys.\nAutomated: Alert if latency > 500ms.\nEscalate: False\nRecovery: N/A\nPrevention: Upgrade Redis node memory."
    )
]

CHAT_SESSIONS = [
    ("How to fix 502 Bad Gateway?", "What usually causes Nginx 502 errors?", "A 502 Bad Gateway means Nginx acting as a proxy received an invalid response from the upstream server (like FastAPI/Gunicorn). Check if your backend app is running, and verify the port bindings match."),
    ("Docker container CrashLoop", "My container keeps restarting. How do I debug?", "Run `docker logs <container_id>` to see the exact crash output. Often this is caused by a missing environment variable or an entrypoint script failing to execute."),
    ("Optimizing DB Queries", "How can I speed up a slow Postgres query?", "Use the `EXPLAIN ANALYZE` command before your SQL query. It will show you exactly where the database is spending time. You likely need to add an Index on the columns you are filtering by.")
]

TICKET_QS = [
    "The AI diagnosis recommended restarting the DB, but I don't have IAM permissions. Can an admin execute this?",
    "Our custom microservice logs aren't being parsed correctly by the Monitor Agent. Can we update the regex?",
    "Can you reset my 2FA? I lost my device.",
    "The remediation plan suggested adding PgBouncer. Is there a company-approved Docker image for this?",
    "Feature Request: Can we export these incident reports to PDF?"
]

def random_date(days_back=30):
    """Generates a random timestamp in the past X days."""
    return datetime.now() - timedelta(days=random.randint(0, days_back), hours=random.randint(0, 23), minutes=random.randint(0, 59))

def seed_database():
    print("🌱 Starting AegisAI Database Seeder...")
    db: Session = SessionLocal()

    try:
        # 1. Create 30 Fake Users
        users = []
        default_hash = pwd_context.hash("Password123!")
        
        for i in range(30):
            name = random.choice(NAMES) + f" {random.randint(1,99)}"
            email = f"{name.replace(' ', '.').lower()}@{random.choice(DOMAINS)}"
            user = User(
                email=email,
                hashed_password=default_hash,
                full_name=name,
                is_admin=False,
                created_at=random_date(40)
            )
            db.add(user)
            users.append(user)
        
        db.commit()
        print(f"✅ Injected 30 Users.")

        # 2. Inject Incidents
        incident_count = 0
        for user in users:
            # Each user gets 2-8 random incidents
            for _ in range(random.randint(2, 8)):
                log, anom, cause, rem = random.choice(LOG_SNIPPETS)
                incident = Incident(
                    user_id=user.id,
                    timestamp=random_date(30),
                    raw_logs=log,
                    status=random.choice(["open", "resolved", "in-progress"]),
                    anomaly_description=anom,
                    root_cause=cause,
                    remediation_action=rem,
                    remediation_status=random.choice(["pending", "completed"])
                )
                db.add(incident)
                incident_count += 1
                
        db.commit()
        print(f"✅ Injected {incident_count} AI Incidents.")

        # 3. Inject Chat Sessions
        chat_count = 0
        for user in users:
            for _ in range(random.randint(1, 3)):
                title, q, a = random.choice(CHAT_SESSIONS)
                session = ChatSession(
                    user_id=user.id,
                    title=title,
                    created_at=random_date(20)
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
                msg1 = ChatMessage(session_id=session.id, role="user", content=q, timestamp=session.created_at)
                msg2 = ChatMessage(session_id=session.id, role="ai", content=a, timestamp=session.created_at + timedelta(minutes=1))
                db.add(msg1)
                db.add(msg2)
                chat_count += 1
                
        db.commit()
        print(f"✅ Injected {chat_count} Chat Sessions.")

        # 4. Inject Support Tickets
        ticket_count = 0
        for user in random.sample(users, 15): # 15 random users submit tickets
            question = random.choice(TICKET_QS)
            status = random.choice(["open", "resolved"])
            answer = "I have escalated this to the DevOps team. Check your email for access logs." if status == "resolved" else None
            
            ticket = EscalationTicket(
                user_id=user.id,
                question=question,
                answer=answer,
                status=status,
                created_at=random_date(10)
            )
            db.add(ticket)
            ticket_count += 1
            
        db.commit()
        print(f"✅ Injected {ticket_count} Escalation Tickets.")
        print("\n🎉 SEEDING COMPLETE! Your Admin Dashboard is now fully populated.")
        print("Test Users Password: 'Password123!'")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()