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
Az alábbi végpontokhoz a **root** (`/`) és a két router tartozik: `/users/...` és `/groups/...`. A csoport routerben definiált útvonalakra még egyszer ráépül a `prefix="/groups"`, így például a `@router.get("/groups")` végeredményben `GET /groups/groups` lesz.

### 🏠 Alap végpont
| Metódus & Útvonal | Auth | Leírás | Válasz |
| --- | --- | --- | --- |
| `GET /` | Nem szükséges | Egyszerű egészségügyi ellenőrzés. | `{ "message": "FastAPI is running 🚀" }` |

### 👤 Felhasználói végpontok (`/users/...`)

#### 1. `GET /users/auth`
- 🔒 **Auth**: kötelező.
- 📤 **Válasz**: az aktuális felhasználói payload (`id`, `username`, `role`).

#### 2. `GET /users/user_details`
- 🔒 **Auth**: kötelező.
- 📥 **Lekérdezés**: nincs extra paraméter.
- 📤 **Válasz**:
  ```json
  {
    "id": 1,
    "full_name": "Teszt Elek",
    "email": "teszt@example.com",
    "username": "teszt",
    "mobile": "+36...",
    "role": "admin"
  }
  ```

#### 3. `POST /users/login`
- 🔑 **Auth**: nyilvános.
- 📥 **Törzs**:
  ```json
  {
    "email": "user@example.com",
    "password": "titok"
  }
  ```
- 📤 **Válasz**: `{ "message": "sikeres bejelentkezés", "role": "member" }`
- 🍪 **Megjegyzés**: HTTP-only `access_token` sütit állít be (2 óra lejárat), a Redis-ben `session:{user_id}` kulcson tárolja a tokent.

#### 4. `POST /users/create_user`
- 👑 **Auth**: kizárólag `admin`.
- 📥 **Törzs**:
  ```json
  {
    "email": "uj@example.com",
    "username": "ujuser",
    "full_name": "Új Felhasználó",
    "mobile": "+361234567",
    "role": "member"
  }
  ```
- 🧠 **Validáció**: e-mail és felhasználónév egyediségét ellenőrzi.
- 📤 **Válasz**: `{ "message": "Sikeresen létrehozott felhasználó", "pass": "GeneráltJelszo123!" }`
  - A jelszó a válaszban jelenik meg először; célszerű azonnal továbbítani a felhasználónak.

#### 5. `POST /users/logout`
- 🔒 **Auth**: kötelező.
- 🧹 **Működés**: törli a sütit és a Redis sessiont.
- 📤 **Válasz**: `{ "message": "Sikeres kijelentkezés" }`

### 👥 Csoport végpontok (`/groups/...`)

#### 1. `GET /groups/groups`
- 🔒 **Auth**: kötelező.
- 🧭 **Szűrés**:
  - `admin`: minden csoport.
  - `group_leader`: csak az általa vezetett csoportok.
  - `member`: azok, ahol tag.
- 📤 **Válasz** (lista):
  ```json
  [
    {
      "id": 3,
      "groupName": "Backend Team",
      "groupDesc": "API fejlesztés",
      "groupLeader": "Kiss Péter"
    }
  ]
  ```

#### 2. `POST /groups/create-group`
- 👑 **Auth**: `admin` vagy `group_leader`.
- 📥 **Törzs**:
  ```json
  {
    "group_name": "Mobil Squad",
    "group_description": "Mobil app fejlesztés"
  }
  ```
- 🧠 **Megjegyzés**: a névnek egyedinek kell lennie; a vezető automatikusan az aktuális felhasználó.
- 📤 **Válasz**: `{ "message": "Sikeres csoport létrehozás" }`

#### 3. `POST /groups/add-user-to-group`
- 👑 **Auth**: `admin` vagy `group_leader`.
- 📥 **Törzs**:
  ```json
  {
    "user_to_add": 5,
    "group_to_add": 2
  }
  ```
- 📤 **Válasz**: `{ "message": "Sikeres hozzáadás" }`
- ⚠️ **Megjegyzés**: nincs beépített duplikáció ellenőrzés; érdemes ügyelni rá kliens oldalon.

#### 4. `DELETE /groups/remove-user-form-group/group/{group_id}/member/{user_id}`
- 👑 **Auth**: `admin` vagy `group_leader`.
- 🧩 **Logika**: a csoportvezető csak a saját csoportjából törölhet tagot, admin bármelyikből.
- 📤 **Válasz**: `{ "message": "Sikeresen eltávolítottad a csoportból a felhasználót" }`

#### 5. `DELETE /groups/remove-group/{group_id}`
- 👑 **Auth**: `admin` vagy `group_leader` (a vezető a saját csoportját tudja törölni).
- 📤 **Válasz**: üres törzs 200-as státusszal; szükség esetén bővíthető sikerüzenettel.

---

## 📎 Tippek integrációhoz
- 🔁 **Sütik kezelése**: REST kliensnél (pl. Postman) engedélyezd a cookie követést, különben a védett végpontok 401-et adnak.
- 🧹 **Session tisztítás**: fejlesztői környezetben hasznos a Redis kulcsok időnkénti ürítése (`FLUSHALL`).
- 🧪 **Tesztelés**: a FastAPI automatikusan generálja az OpenAPI sémát; a `/docs` felület segít a gyors próbáknál.

---

## ✅ Összefoglalás
Ez a dokumentum bemutatta a projekt architektúráját, a futtatáshoz szükséges lépéseket, a jogosultsági modellt és az összes jelenlegi végpont bemeneteit/kimeneteit. Jó fejlesztést! 😄
