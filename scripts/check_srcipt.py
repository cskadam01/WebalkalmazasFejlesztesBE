from database.db import SessionLocal

db = SessionLocal()
res = db.execute("DESCRIBE users;").fetch