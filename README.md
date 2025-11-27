# 🚀 Csapattag-menedzsment API

Ez a FastAPI alkalmazás felhasználók (admin, group_leader, member) és csoportok kezelésére szolgál. A backend PostgreSQL-adatbázist használ SQLAlchemy ORM-mel, a bejelentkezéshez BCrypt alapú jelszó-ellenőrzést és JWT alapú session-kezelést (Redis tárolóval) alkalmaz. Az alábbi dokumentáció összefoglalja a működést, a szükséges beállításokat és az összes elérhető végpontot.

---

## ⚙️ Előfeltételek
- 🐍 **Python 3.10+**
- 📦 `pip` és (ajánlott) virtuális környezet
- 🛢️ Elérhető PostgreSQL adatbázis
- 🧠 Redis példány a session tokenekhez

---

## 🛠️ Telepítés & futtatás
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```
A szerver alapértelmezetten a `http://127.0.0.1:8000` címen lesz elérhető. A FastAPI automatikus dokumentációja a `/docs` (Swagger UI) illetve `/redoc` útvonalon érhető el.

---

## 🔐 Kötelező környezeti változók
| Változó | Leírás |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy kompatibilis adatbázis kapcsolat (pl. `postgresql+psycopg2://user:pw@host:5432/db`). |
| `SECRET_KEY` | JWT aláíráshoz használt titok. |
| `ALGORITHM` | JWT algoritmus (pl. `HS256`). |
| `ACCESS_TOKEN_EXPIRE_MIN` | A hozzáférési token lejárati ideje percben (pl. `120`). |
| `REDIS_URL` | Teljes Redis kapcsolat (pl. `redis://:pass@localhost:6379/0`). |

> 💡 A `.env` fájlban célszerű megadni ezeket az értékeket; az alkalmazás automatikusan betölti őket.

---

## 🧱 Adatmodell dióhéjban
- **users**: felhasználói alapadatok, `role ∈ {admin, group_leader, member}`.
- **user_groups**: csoportok, `leader_id` a vezető felhasználó azonosítója.
- **group_members**: kapcsolótábla a tagokhoz.
- (Előkészítve) **skills** és **user_skills** táblák a későbbi bővítésekhez.

---

## 🔑 Hitelesítés és jogosultság
1. **Bejelentkezés (`POST /users/login`)**: e-mail + jelszó alapján JWT token készül.
2. **Token tárolása**: a szerver HTTP-only `access_token` sütiben küldi vissza; párhuzamosan a Redis tárolja a session metaadatokat.
3. **Védett végpontok**: a sütiből kiolvasott token alapján azonosítja a felhasználót. Admin-specifikus végpontok a `require_admin`, míg a csoportvezetői jogot is igénylők a `require_leader_or_admin` dependenciát használják.
4. **Kijelentkezés**: a süti törlésével és a Redis session eltávolításával történik.

> ⚠️ A védett végpontokhoz a böngészőnek/szolgáltatásnak kezelnie kell a sütiket (pl. `fetch` esetén `credentials: "include"`).

---

## 📚 Endpoint katalógus
Az alábbi végpontokhoz a **root** (`/`) és a két router tartozik: `/users/...` és `/groups/...`. A csoport routerben definiált útvonalakra még egyszer ráépül a `prefix="/groups"`, így például a `@router.get("/groups")` végeredményben `GET /groups/groups` lesz. Az itt felsorolt útvonalak tükrözik az aktuális kódot, beleértve az újonnan hozzáadott csoportműveleteket és a kijelentkezést.

### 🏠 Alap végpont
| Metódus & Útvonal | Auth | Leírás | Válasz |
| --- | --- | --- | --- |
| `GET /` | Nem szükséges | Egyszerű egészségügyi ellenőrzés. | `{ "message": "FastAPI is running 🚀" }` |

### 👤 Felhasználói végpontok (`/users/...`)

| # | Metódus & Útvonal | Auth | Bemenet | Válasz |
| - | --- | --- | --- | --- |
| 1 | `GET /users/auth` | 🔒 kötelező | – | Aktuális felhasználói payload: `{ "id": 1, "username": "teszt", "role": "admin" }` |
| 2 | `GET /users/user_details` | 🔒 kötelező | – | Részletes profil (id, név, email, mobil, role) az aktuális userről. |
| 3 | `POST /users/login` | 🔑 nyilvános | `{"email": "user@example.com", "password": "titok"}` | Sikerüzenet és szerep: `{ "message": "sikeres bejelentkezés", "role": "member" }`; HTTP-only `access_token` cookie beállítása 2 órára, Redis session létrehozása. |
| 4 | `POST /users/create_user` | 👑 csak `admin` | `{"email": "uj@example.com", "username": "ujuser", "full_name": "Új Felhasználó", "mobile": "+361234567", "role": "member"}` | Új user létrehozása generált jelszóval: `{ "message": "Sikeresen létrehozott felhasználó", "pass": "GeneráltJelszo123!" }` (a jelszó csak itt érhető el). |
| 5 | `POST /users/logout` | 🔒 kötelező | – | Kijelentkezés a cookie és Redis session törlésével: `{ "message": "Sikeres kijelentkezés" }` |

### 👥 Csoport végpontok (`/groups/...`)

| # | Metódus & Útvonal | Auth | Bemenet | Válasz |
| - | --- | --- | --- | --- |
| 1 | `GET /groups/groups` | 🔒 kötelező | – | Csoportlista szerepkör alapján szűrve: admin → minden; group_leader → csak a saját vezetett; member → csak ahol tag. Válaszlista elemei: `{ "id": 3, "groupName": "Backend Team", "groupDesc": "API fejlesztés", "groupLeader": "Kiss Péter" }`. |
| 2 | `POST /groups/create-group` | 👑 `admin` vagy `group_leader` | `{"group_name": "Mobil Squad", "group_description": "Mobil app fejlesztés"}` | Új csoport létrehozása az aktuális userrel mint vezető: `{ "message": "Sikeres csoport létrehozás" }`. Egyedi `group_name` szükséges. |
| 3 | `POST /groups/add-user-to-group` | 👑 `admin` vagy `group_leader` | `{"user_to_add": 5, "group_to_add": 2}` | Tag hozzárendelése: `{ "message": "Sikeres hozzáadás" }`. Duplikációra nincs védelem, kliensoldali kontroll javasolt. |
| 4 | `DELETE /groups/remove-user-form-group/group/{group_id}/member/{user_id}` | 👑 `admin` vagy `group_leader` | Útvonali paraméterek | Tag eltávolítása: `{ "message": "Sikeresen eltávolítottad a csoportból a felhasználót" }`. A vezető csak saját csoportjából törölhet. |
| 5 | `DELETE /groups/remove-group/{group_id}` | 👑 `admin` vagy `group_leader` | Útvonali paraméter | Csoport törlése (vezető csak a sajátját): siker esetén 200-as válasz; bővíthető egyéni üzenettel. |

---

## 📎 Tippek integrációhoz
- 🔁 **Sütik kezelése**: REST kliensnél (pl. Postman) engedélyezd a cookie követést, különben a védett végpontok 401-et adnak.
- 🧹 **Session tisztítás**: fejlesztői környezetben hasznos a Redis kulcsok időnkénti ürítése (`FLUSHALL`).
- 🧪 **Tesztelés**: a FastAPI automatikusan generálja az OpenAPI sémát; a `/docs` felület segít a gyors próbáknál.

---

## ✅ Összefoglalás
Ez a dokumentum bemutatta a projekt architektúráját, a futtatáshoz szükséges lépéseket, a jogosultsági modellt és az összes jelenlegi végpont bemeneteit/kimeneteit. Jó fejlesztést! 😄
