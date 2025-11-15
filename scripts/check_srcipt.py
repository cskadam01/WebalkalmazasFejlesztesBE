# SQL lekérdezések Pythonból (SQLAlchemy alapokon)

# Kapcsolódás az adatbázishoz:
# az engine objektum kezeli a kapcsolatot a MySQL / PostgreSQL stb. felé.

# Lekérdezés futtatása:
# a text() függvénnyel írsz nyers SQL-t, amit a conn.execute() hajt végre.

# Eredmények bejárása:
# a for row in result: ciklussal végig tudsz menni a visszakapott sorokon.

# Módosító műveleteknél (INSERT, UPDATE, DELETE):
# mindig conn.commit() kell a végén, hogy mentse a változást.

# Paraméterezett lekérdezés:
# a :param szintaxissal biztonságosan adhatsz át változókat (pl. :id, :email).

# Példa:
# from sqlalchemy import text
# from database.db import engine

# with engine.connect() as conn:
#     result = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": 1})
#     for row in result:
#         print(row)

from sqlalchemy import text
from database.db import engine

with engine.connect() as conn:
    result = conn.execute(text("SHOW CREATE TABLE user_groups;"))

for i in result:
    print(i)
