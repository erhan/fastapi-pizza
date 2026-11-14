# 🍕 fastapi-pizza

> 🇹🇷 Türkçe · [🇬🇧 English below](#-english)

**Bir Dilim FastAPI** (*A Slice of FastAPI*) konuşmasının örnek reposu:
[Python Pizza İstanbul](https://istanbul.python.pizza/), 14 Kasım 2026, StartGate Maslak
(programdaki adıyla *From Zero to Production with FastAPI*).
Slaytlar: <https://python-pizza.erhan.dev> ·
Canlı API: <https://fastapi-pizza.fastapicloud.dev/docs>

Pizza sipariş alan küçük bir API. FastAPI'nin temellerini tek bir projede gösterir: path / query /
header / body parametreleri, Pydantic ile doğrulama, `Depends`, `async def` ile `def` farkı,
`BackgroundTasks` ve `TestClient` ile test. Üstüne üretime giden yolun parçaları: JWT ile müşteri
girişi, PostgreSQL desteği ve Alembic migration'ları.

> 🍍 Ananas bu menüde yok. Eklemeyi dene: `422` ile geri döner.

## Çalıştırma

```bash
uv sync
cp .env.example .env
uv run fastapi dev
```

Sonra <http://127.0.0.1:8000/docs> adresini aç. Tablolar ve başlangıç menüsü ilk açılışta kendiliğinden
oluşur (SQLite, `pizza.db`; silersen sıfırlanır).

Menüyü değiştirmek ve siparişi ilerletmek "şef" işidir: **Authorize** düğmesine bas ve `X-API-Key`
olarak `.env` içindeki `API_KEY` değerini gir (varsayılan demo anahtarı `demo-chef-key`, yayına
almadan önce değiştir).

```bash
# menüye bak
curl http://127.0.0.1:8000/api/v1/pizzas

# sipariş ver
curl -X POST http://127.0.0.1:8000/api/v1/orders \
  -H 'Content-Type: application/json' \
  -d '{"pizza_id": 1, "customer_name": "Ayşe", "quantity": 2}'

# ananas testi 🍍
curl -X POST http://127.0.0.1:8000/api/v1/pizzas \
  -H 'X-API-Key: demo-chef-key' -H 'Content-Type: application/json' \
  -d '{"name": "Hawaii", "price": 200, "toppings": ["mozzarella", "ananas"]}'
```

Müşteriler hesap açıp giriş yapabilir (JWT). Giriş yapmış müşterinin siparişleri hesabına işlenir:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "ayse@example.com", "password": "margherita-4ever", "full_name": "Ayşe"}'

# giriş: OAuth2 parola formu, kullanıcı adı alanına e-posta yazılır
curl -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -d 'username=ayse@example.com&password=margherita-4ever'

# dönen access_token ile
curl http://127.0.0.1:8000/api/v1/users/me/orders -H 'Authorization: Bearer <access_token>'
```

`/docs` sayfasında **Authorize** düğmesi aynı işi yapar: kullanıcı adına e-postanı yaz.

## PostgreSQL ve migration'lar

Varsayılan veritabanı SQLite'tır, kurulum istemez. PostgreSQL için:

```bash
docker compose up -d              # yerelde PostgreSQL 17
# .env içinde:
#   DATABASE_URL=postgresql://pizza:pizza@localhost:5432/pizza
#   CREATE_TABLES_ON_STARTUP=false
uv run alembic upgrade head       # tabloları migration'larla kur
uv run fastapi dev
```

Modeli değiştirince yeni migration: `uv run alembic revision --autogenerate -m "ne değişti"`.
`postgres://` ve `postgresql://` adresleri kendiliğinden psycopg 3 sürücüsüne çevrilir.

## Dosya yapısı

Katmanlar [ozgurkon](https://github.com/erhan/ozgurkon) ile aynı: **route → service → crud → model**.

```text
.
├── app
│   ├── main.py              # create_app() + lifespan (tablolar, başlangıç menüsü)
│   ├── api
│   │   ├── deps.py          # Depends: DbSession, sayfalama, şefin anahtarı, giriş yapan müşteri
│   │   └── v1/routes        # health, pizzas, orders, auth, users -> api_router (/api/v1)
│   ├── core                 # ayarlar (pydantic-settings), db, güvenlik (parola + JWT), hatalar
│   ├── schemas              # Pydantic: içeri giren / dışarı çıkan veri
│   ├── models               # SQLAlchemy tabloları
│   ├── crud                 # veritabanı sorguları
│   └── services             # iş kuralları
├── alembic                  # veritabanı migration'ları
├── examples                 # konuşmanın yapı taşları (01-05), her biri tek başına çalışır
├── tests                    # pytest + TestClient (bellekte SQLite)
├── docker-compose.yml       # yerel PostgreSQL
└── pyproject.toml           # uv projesi, ruff ve pytest ayarları
```

## Uç noktalar

Tümü `/api/v1` altında. 🔑 = `X-API-Key` (şefin anahtarı) gerekir. 👤 = giriş (Bearer token) gerekir.

| Metot | Yol | Ne yapar |
| --- | --- | --- |
| GET | `/health` | Fırın sıcak mı? |
| GET | `/pizzas` | Menüye bak (`vegetarian`, `max_price`, `limit`, `offset`) |
| GET | `/pizzas/{pizza_id}` | Tek pizza |
| POST | `/pizzas` 🔑 | Menüye pizza ekle |
| PATCH | `/pizzas/{pizza_id}` 🔑 | Pizzayı değiştir (sadece gönderdiğin alanlar) |
| DELETE | `/pizzas/{pizza_id}` 🔑 | Menüden çıkar (siparişi olan pizza çıkarılamaz: `409`) |
| POST | `/orders` | Sipariş ver (giriş yaptıysan hesabına işlenir) |
| GET | `/orders` | Siparişleri listele (`limit`, `offset`) |
| GET | `/orders/{order_id}` | Siparişi takip et |
| PATCH | `/orders/{order_id}` 🔑 | Siparişi ilerlet (`preparing` → `baking` → `on_the_way` → `delivered`) |
| POST | `/auth/register` | Hesap aç |
| POST | `/auth/token` | Giriş yap, access token al (OAuth2 parola formu) |
| GET | `/users/me` 👤 | Ben kimim? |
| GET | `/users/me/orders` 👤 | Siparişlerim (`limit`, `offset`) |

## Örnekler

Konuşmadaki her adım için tek dosyalık, çalıştırılabilir bir uygulama (`05_async.py` bonus: slaytlarda yok):

| Dosya | Konu | Çalıştır |
| --- | --- | --- |
| `01_hello.py` | Merhaba dünya, en sade pizza | `uv run fastapi dev examples/01_hello.py` |
| `02_params.py` | Dört peynirli: path, query, header, body | `uv run fastapi dev examples/02_params.py` |
| `03_models.py` | Pydantic ve ananas testi | `uv run fastapi dev examples/03_models.py` |
| `04_depends.py` | `Depends`: sayfalama ve şefin anahtarı | `uv run fastapi dev examples/04_depends.py` |
| `05_async.py` | Tek garson, çok masa: `async def` ve `def` | `uv run fastapi dev examples/05_async.py` |

## Test ve lint

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Testler bellekte SQLite kullanır, `pizza.db` dosyasına dokunmaz. `tests/test_examples.py` her örneği
çalıştırır; "bloklayan çağrı tüm restoranı dondurur" iddiasını bile ölçer. `tests/test_migrations.py`
elle yazılan migration'ların modellerle birebir örtüştüğünü denetler.

## Deploy

```bash
uv run fastapi run      # production modunda yerel sunucu
uv run fastapi login    # FastAPI Cloud
uv run fastapi deploy
```

Yayına alırken `API_KEY` (şefin anahtarı) ve `SECRET_KEY` (JWT imzası) değerlerini ortam değişkeni
olarak ver. Verilmezse her süreç kendine rastgele bir anahtar üretir: uygulama hiçbir zaman bu
README'deki demo anahtarıyla yayına çıkmaz.

```bash
# değer komut geçmişine düşmesin diye stdin'den okunur
openssl rand -base64 48 | uv run fastapi cloud env set SECRET_KEY --secret --value-stdin
openssl rand -base64 24 | uv run fastapi cloud env set API_KEY --secret --value-stdin
```

Bu repo tam olarak böyle yayında: <https://fastapi-pizza.fastapicloud.dev/docs>. Canlı demo
SQLite ile çalışır (`DATABASE_URL=sqlite+aiosqlite:////tmp/pizza.db`). FastAPI Cloud boşta kalan
uygulamayı sıfıra ölçekler ve dosya sistemi kalıcı değildir; yeni açılan her kopya menüyü baştan
kurar, hesaplar ve siparişler ise gider. Demo için yeterli. Kalıcı veri için `DATABASE_URL`
olarak bir PostgreSQL adresi ver (FastAPI Cloud'un Neon entegrasyonu bu değişkeni kendisi ekler)
ve tabloları Alembic ile kur.

Lisans: MIT.

---

# 🇬🇧 English

**A Slice of FastAPI** companion repo: [Python Pizza Istanbul](https://istanbul.python.pizza/),
14 November 2026, StartGate Maslak (on the programme as *From Zero to Production with FastAPI*).
Slides: <https://python-pizza.erhan.dev> ·
Live API: <https://fastapi-pizza.fastapicloud.dev/docs>

A small pizza-ordering API that shows the FastAPI basics in one project: path / query / header /
body parameters, validation with Pydantic, `Depends`, `async def` vs `def`, `BackgroundTasks` and
testing with `TestClient`. On top of that, the pieces on the way to production: customer login with
JWT, PostgreSQL support and Alembic migrations.

> 🍍 There is no pineapple on this menu. Try adding it: you get a `422`.

## Run it

```bash
uv sync
cp .env.example .env
uv run fastapi dev
```

Then open <http://127.0.0.1:8000/docs>. The tables and a starter menu are created on first start
(SQLite, `pizza.db`; delete the file to reset).

Changing the menu and moving orders along is the chef's job: press **Authorize** and enter the
`API_KEY` from your `.env` as `X-API-Key` (the demo key is `demo-chef-key`: change it before you
deploy).

```bash
# browse the menu
curl http://127.0.0.1:8000/api/v1/pizzas

# order a pizza
curl -X POST http://127.0.0.1:8000/api/v1/orders \
  -H 'Content-Type: application/json' \
  -d '{"pizza_id": 1, "customer_name": "Ayşe", "quantity": 2}'

# the pineapple test 🍍
curl -X POST http://127.0.0.1:8000/api/v1/pizzas \
  -H 'X-API-Key: demo-chef-key' -H 'Content-Type: application/json' \
  -d '{"name": "Hawaii", "price": 200, "toppings": ["mozzarella", "ananas"]}'
```

Customers can create an account and log in (JWT). Orders placed while logged in are kept on the account:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "ayse@example.com", "password": "margherita-4ever", "full_name": "Ayşe"}'

# log in: an OAuth2 password form, the e-mail goes in the username field
curl -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -d 'username=ayse@example.com&password=margherita-4ever'

# with the access_token you got back
curl http://127.0.0.1:8000/api/v1/users/me/orders -H 'Authorization: Bearer <access_token>'
```

The **Authorize** button on `/docs` does the same: type your e-mail as the username.

## PostgreSQL and migrations

The default database is SQLite, which needs no setup. For PostgreSQL:

```bash
docker compose up -d              # a local PostgreSQL 17
# in .env:
#   DATABASE_URL=postgresql://pizza:pizza@localhost:5432/pizza
#   CREATE_TABLES_ON_STARTUP=false
uv run alembic upgrade head       # build the tables from the migrations
uv run fastapi dev
```

After changing a model, write the next migration: `uv run alembic revision --autogenerate -m "what changed"`.
`postgres://` and `postgresql://` URLs are switched to the psycopg 3 driver automatically.

## Project structure

Same layers as [ozgurkon](https://github.com/erhan/ozgurkon): **route → service → crud → model**.

```text
.
├── app
│   ├── main.py              # create_app() + lifespan (tables, starter menu)
│   ├── api
│   │   ├── deps.py          # Depends: DbSession, pagination, the chef's key, the logged-in customer
│   │   └── v1/routes        # health, pizzas, orders, auth, users -> api_router (/api/v1)
│   ├── core                 # settings (pydantic-settings), db, security (passwords + JWT), errors
│   ├── schemas              # Pydantic: what goes in and comes out
│   ├── models               # SQLAlchemy tables
│   ├── crud                 # database queries
│   └── services             # business rules
├── alembic                  # database migrations
├── examples                 # the talk's building blocks (01-05), each runs on its own
├── tests                    # pytest + TestClient (in-memory SQLite)
├── docker-compose.yml       # a local PostgreSQL
└── pyproject.toml           # uv project, ruff and pytest config
```

## Endpoints

All under `/api/v1`. 🔑 = needs `X-API-Key` (the chef's key). 👤 = needs a login (Bearer token).

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Is the oven hot? |
| GET | `/pizzas` | Browse the menu (`vegetarian`, `max_price`, `limit`, `offset`) |
| GET | `/pizzas/{pizza_id}` | One pizza |
| POST | `/pizzas` 🔑 | Add a pizza to the menu |
| PATCH | `/pizzas/{pizza_id}` 🔑 | Change a pizza (only the fields you send) |
| DELETE | `/pizzas/{pizza_id}` 🔑 | Take it off the menu (a pizza with orders stays: `409`) |
| POST | `/orders` | Order a pizza (kept on your account when you are logged in) |
| GET | `/orders` | List orders (`limit`, `offset`) |
| GET | `/orders/{order_id}` | Follow an order |
| PATCH | `/orders/{order_id}` 🔑 | Move an order along (`preparing` → `baking` → `on_the_way` → `delivered`) |
| POST | `/auth/register` | Create an account |
| POST | `/auth/token` | Log in and get an access token (OAuth2 password form) |
| GET | `/users/me` 👤 | Who am I? |
| GET | `/users/me/orders` 👤 | My orders (`limit`, `offset`) |

## Examples

One runnable single-file app for every step of the talk (`05_async.py` is a bonus: it is not on the slides):

| File | Topic | Run |
| --- | --- | --- |
| `01_hello.py` | Hello world, the plainest pizza | `uv run fastapi dev examples/01_hello.py` |
| `02_params.py` | Four cheeses: path, query, header, body | `uv run fastapi dev examples/02_params.py` |
| `03_models.py` | Pydantic and the pineapple test | `uv run fastapi dev examples/03_models.py` |
| `04_depends.py` | `Depends`: pagination and the chef's key | `uv run fastapi dev examples/04_depends.py` |
| `05_async.py` | One waiter, many tables: `async def` vs `def` | `uv run fastapi dev examples/05_async.py` |

## Tests and lint

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests use an in-memory SQLite database and never touch `pizza.db`. `tests/test_examples.py` runs every
example and even measures the "a blocking call freezes the whole restaurant" claim.
`tests/test_migrations.py` checks that the hand-written migrations build exactly what the models describe.

## Deploy

```bash
uv run fastapi run      # local server in production mode
uv run fastapi login    # FastAPI Cloud
uv run fastapi deploy
```

When you deploy, pass `API_KEY` (the chef's key) and `SECRET_KEY` (signs the JWTs) as environment
variables. Without them every process makes up a random key of its own: the app never goes live on
the demo key printed in this README.

```bash
# read from stdin, so the value stays out of your shell history
openssl rand -base64 48 | uv run fastapi cloud env set SECRET_KEY --secret --value-stdin
openssl rand -base64 24 | uv run fastapi cloud env set API_KEY --secret --value-stdin
```

This repo is live exactly like that: <https://fastapi-pizza.fastapicloud.dev/docs>. The live demo
runs on SQLite (`DATABASE_URL=sqlite+aiosqlite:////tmp/pizza.db`). FastAPI Cloud scales an idle app
to zero and its file system is not persistent, so every new replica seeds the menu again while
accounts and orders are gone. Fine for a demo. For data that stays, point `DATABASE_URL` at
PostgreSQL (FastAPI Cloud's Neon integration adds that variable for you) and create the tables with
Alembic.

License: MIT.
