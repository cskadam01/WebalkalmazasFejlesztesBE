# 🚀 Csapattag‑menedzsment API

Ez a projekt egy FastAPI alapú backend, amely felhasználók, csoportok és skillek kezelésére szolgál. A szolgáltatás PostgreSQL adatbázist, SQLAlchemy ORM-et és Redis alapú session‑tárolást használ, a hitelesítés JWT tokennel és HTTP‑only sütikkel történik.

## Tartalomjegyzék
1. [Fő funkciók](#fő-funkciók)
2. [Követelmények](#követelmények)
3. [Telepítés és futtatás](#telepítés-és-futtatás)
4. [Környezeti változók](#környezeti-változók)
5. [Adatmodell áttekintés](#adatmodell-áttekintés)
6. [Hitelesítés és jogosultságok](#hitelesítés-és-jogosultságok)
7. [API referencia](#api-referencia)
   - [Alap végpont](#alap-végpont)
   - [Felhasználói végpontok](#felhasználói-végpontok-users)
   - [Csoport végpontok](#csoport-végpontok-groups)
   - [Skill végpontok](#skill-végpontok-skills)
8. [Fejlesztési tippek](#fejlesztési-tippek)

---

## Fő funkciók
- Felhasználók (admin, group_leader, member) kezelése, belépés/jelszó ellenőrzés és tokenes session.
- Csoportok létrehozása, tagfelvétel és törlés szerepkörök alapján szűrve.
- Skillek felvitele, felhasználókhoz rendelése és szintmódosítás adminisztrátorok számára.
- Redis alapú session‑validáció: a sütiben kapott JWT‑t a Redisben tárolt sessionnel vetjük össze.

## Követelmények
- 🐍 **Python 3.10+**
- 🐘 Elérhető **PostgreSQL** példány
- 🎯 **Redis** elérés a session tokenekhez
- 📦 `pip` és ajánlott **virtuális környezet**

A Python csomagfüggőségek a `requirements.txt` fájlban találhatók; telepítésükhöz lásd a telepítési lépéseket.

## Telepítés és futtatás
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Környezeti változók beállítása (lásd lejjebb)
uvicorn app:app --reload
```
Alapértelmezetten a szerver a `http://127.0.0.1:8000` címen fut. A dokumentáció elérhető a `/docs` (Swagger UI) és `/redoc` útvonalakon.

### Adatbázis migrációk
Ha Alembicet használsz, állítsd be a `DATABASE_URL` változót, majd futtasd:
```bash
alembic upgrade head
```

## Környezeti változók
A projekt `.env` fájlból is beolvassa a beállításokat.

| Változó | Leírás | Példa |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy kompatibilis adatbázis kapcsolat | `postgresql+psycopg2://user:pw@localhost:5432/db` |
| `SECRET_KEY` | JWT aláírás titka | `super-secret-key` |
| `ALGORITHM` | JWT algoritmus | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MIN` | Token lejárati idő percben | `120` |
| `REDIS_URL` | Redis kapcsolat | `redis://:pass@localhost:6379/0` |

## Adatmodell áttekintés
- **users**: felhasználók, `role ∈ {admin, group_leader, member}` (jelszó, e-mail, mobil, specializáció).
- **user_groups**: csoportok, `leader_id` hivatkozik a vezetőre.
- **group_members**: kapcsolótábla a csoporttagságokhoz.
- **skills** és **user_skills**: skillek és felhasználóhoz rendelt szintek.

## Hitelesítés és jogosultságok
1. **Bejelentkezés (`POST /users/login`)** – e-mail/jelszó alapján JWT készül.
2. **Token tárolása** – HTTP‑only `access_token` süti, párhuzamosan Redis session bejegyzéssel.
3. **Védett végpontok** – a sütiből kiolvasott JWT + Redis session egyezés alapján azonosítja a felhasználót.
4. **Jogosultsági ellenőrzés** – admin végpontok `require_admin`, vezetői vagy admin jogosultságot igénylők `require_leader_or_admin` dependenciát használnak.
5. **Kijelentkezés** – session törlése Redisből és a süti eltávolítása (`POST /users/logout`).

> A védett végpontokhoz a kliensnek kezelnie kell a sütiket (pl. `fetch` esetén `credentials: "include"`).

## API referencia
Az alábbi táblázatok a tényleges útvonalakat és válaszpéldákat mutatják. Minden útvonal a FastAPI alkalmazásban definiált router prefixszel együtt értendő (pl. a `/users` prefix + `/login` → `POST /users/login`).

### Alap végpont
| Metódus | Útvonal | Auth | Leírás | Példa válasz |
| --- | --- | --- | --- | --- |
| GET | `/` | Nem | Egyszerű health check. | `{ "message": "FastAPI is running 🚀" }` |

### Felhasználói végpontok (`/users`)
| Metódus | Útvonal | Auth | Bemenet | Válasz |
| --- | --- | --- | --- | --- |
| GET | `/auth` | Kötelező | – | Aktuális felhasználói payload (id, username, role). |
| GET | `/user-details` | Kötelező | – | Részletes profil: id, név, email, mobil, szerepkör, specializáció, csoportok listája. |
| POST | `/login` | Nyilvános | `{ "email": "user@example.com", "password": "titok" }` | `{ "message": "sikeres bejelentkezés", "role": "member" }` + `access_token` süti beállítása. |
| GET | `/all-users` | Admin vagy group_leader | – | Lista minden felhasználóról: `[{"fullName": "Teszt Elek", "speciality": "Backend"}, ...]`. |
| GET | `/get-user/{userID}` | Kötelező | Útvonali paraméter | Adott user adatai (username, fullname, role, specialty, csoportok, skills). 404 ha nincs. |
| POST | `/create-user` | Admin | `{ "email": "uj@example.com", "username": "ujuser", "full_name": "Új Felhasználó", "mobile": "+361234567", "specialty": "Backend", "role": "member" }` | `{ "message": "Sikeresen létrehozott felhasználó", "pass": "GeneráltJelszo123" }` – a jelszó csak a válaszban jelenik meg. |
| POST | `/logout` | Kötelező | – | `{ "message": "Sikeres kijelentkezés" }` + Redis session és süti törlése. |

### Csoport végpontok (`/groups`)
| Metódus | Útvonal | Auth | Bemenet | Válasz |
| --- | --- | --- | --- | --- |
| GET | `/groups` | Kötelező | – | Csoportlista szerepkör alapján szűrve (admin: mindent lát; leader: saját vezetett; member: ahol tag). Lista elemei: `{ "id": 1, "groupName": "Backend Team", "groupDesc": "API fejlesztés", "groupLeader": "Kiss Péter" }`. |
| GET | `/group/{group_id}` | Kötelező | Útvonali paraméter | Részletek egy csoportról a jogosultsági szabályok szerint: `{ "groupID": 2, "groupName": "Mobil Squad", "groupLeader": "Józsa Anna", "groupMembers": [{"member_id": 5, "member_name": "jane"}], "groupDesc": "Mobil app fejlesztés", "memberCount": 2 }`. 403/404 ha nem elérhető. |
| POST | `/create-group` | Admin vagy group_leader | `{ "group_name": "Mobil Squad", "group_description": "Mobil app fejlesztés" }` | `{ "message": "Sikeres csoport létrehozás" }`. A létrehozó automatikusan tag lesz. |
| POST | `/add-user-to-group` | Admin vagy group_leader | `{ "user_to_add": 5, "group_to_add": 2 }` | `{ "message": "Sikeres hozzáadás" }`. |
| DELETE | `/remove-user-form-group/group/{group_id}/member/{user_id}` | Admin vagy group_leader | Útvonali paraméterek | `{ "message": "Sikeresen eltávolítottad a csoportból a felhasználót" }`. Leader csak a saját csoportjából törölhet. |
| DELETE | `/remove-group/{group_id}` | Admin vagy group_leader | Útvonali paraméter | Siker esetén 200 és a csoport törlődik. 404 ha nem létezik. |

### Skill végpontok (`/skills`)
| Metódus | Útvonal | Auth | Bemenet | Válasz |
| --- | --- | --- | --- | --- |
| POST | `/new-skill` | Admin | `{ "skill_name": "Python" }` | Üzenet az új skill létrehozásáról. |
| POST | `/add-skill-to-user/{userID}/skill/{skillID}` | Admin | Útvonali paraméterek + `{ "skill_level": 3 }` | `{ "Sikeresen hozzáadtad a skill-t a felhasználóhoz" }`. |
| PUT | `/change-level/{userID}/skills/{skillID}` | Admin | Útvonali paraméterek + `{ "skill_level": 4 }` | Üzenet a szint frissítéséről, vagy 404 ha a párosítás nem létezik. |
| GET | `/get-all-skills` | Admin | – | Összes skill listája: `[{ "skillId": 1, "skillName": "Python" }, ...]`. 404 ha nincs adat. |
| DELETE | `/remove-skill/{skillID}/user/{userID}` | Admin | Útvonali paraméterek | Üzenet a skill eltávolításáról a felhasználótól; 404 ha nincs párosítás. |
| GET | `/get-users-skill/{userID}` | Auth kötelező | Útvonali paraméter | Adott felhasználó skillei: `[{ "skillId": 2, "skillName": "Docker", "skillLevel": 3 }]`; üres lista, ha nincs skill. |

## Fejlesztési tippek
- **Sütik kezelése:** REST kliensben engedélyezd a cookie kezelést, különben a védett végpontok 401-et adnak.
- **Session tisztítás:** fejlesztés alatt hasznos lehet a Redis kiürítése (`FLUSHALL`).
- **OpenAPI:** a `/docs` felület a validációs szabályokat és payloadokat is jelzi, gyors próbákhoz használd.

Jó fejlesztést! 🎉
