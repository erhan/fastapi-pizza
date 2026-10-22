# 🍕 fastapi-pizza

> 🇹🇷 Türkçe · [🇬🇧 English below](#-english)

**Bir Dilim FastAPI** (*A Slice of FastAPI*) konuşmasının örnek reposu:
[Python Pizza İstanbul](https://istanbul.python.pizza/), 14 Kasım 2026, StartGate Maslak.
Slaytlar: <https://python-pizza.erhan.dev>

Pizza sipariş alan küçük bir API. FastAPI'nin temellerini tek bir projede gösterir: path / query /
header / body parametreleri, Pydantic ile doğrulama, `Depends`, `async def` ile `def` farkı,
`BackgroundTasks` ve `TestClient` ile test.

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

## Dosya yapısı

Katmanlar [ozgurkon](https://github.com/erhan/ozgurkon) ile aynı: **route → service → crud → model**.

```text
.
├── app
│   ├── main.py              # create_app() + lifespan (tablolar, başlangıç menüsü)
│   ├── api
│   │   ├── deps.py          # Depends: DbSession, sayfalama, şefin API anahtarı
│   │   └── v1/routes        # health, pizzas, orders -> api_router (/api/v1)
│   ├── core                 # ayarlar (pydantic-settings), db, hatalar, middleware
│   ├── schemas              # Pydantic: içeri giren / dışarı çıkan veri
│   ├── models               # SQLAlchemy tabloları
│   ├── crud                 # veritabanı sorguları
│   └── services             # iş kuralları
├── examples                 # konuşmanın yapı taşları (01-05), her biri tek başına çalışır
├── tests                    # pytest + TestClient (bellekte SQLite)
└── pyproject.toml           # uv projesi, ruff ve pytest ayarları
```

## Uç noktalar

Tümü `/api/v1` altında. 🔑 = `X-API-Key` gerekir.

| Metot | Yol | Ne yapar |
| --- | --- | --- |
| GET | `/health` | Fırın sıcak mı? |
| GET | `/pizzas` | Menüye bak (`vegetarian`, `max_price`, `limit`, `offset`) |
| GET | `/pizzas/{pizza_id}` | Tek pizza |
| POST | `/pizzas` 🔑 | Menüye pizza ekle |
| PATCH | `/pizzas/{pizza_id}` 🔑 | Pizzayı değiştir (sadece gönderdiğin alanlar) |
| DELETE | `/pizzas/{pizza_id}` 🔑 | Menüden çıkar (siparişi olan pizza çıkarılamaz: `409`) |
| POST | `/orders` | Sipariş ver |
| GET | `/orders` | Siparişleri listele (`limit`, `offset`) |
| GET | `/orders/{order_id}` | Siparişi takip et |
| PATCH | `/orders/{order_id}` 🔑 | Siparişi ilerlet (`preparing` → `baking` → `on_the_way` → `delivered`) |

## Örnekler

Konuşmadaki her adım için tek dosyalık, çalıştırılabilir bir uygulama:

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
çalıştırır; "bloklayan çağrı tüm restoranı dondurur" iddiasını bile ölçer.

## Deploy

```bash
uv run fastapi run      # production modunda yerel sunucu
uv run fastapi login    # FastAPI Cloud
uv run fastapi deploy
```

Bu örnek küçük tutuldu: Alembic migration, JWT ve PostgreSQL yok. Hepsi için
[ozgurkon](https://github.com/erhan/ozgurkon)'a bak.

Lisans: MIT.

---

# 🇬🇧 English

**A Slice of FastAPI** companion repo: [Python Pizza Istanbul](https://istanbul.python.pizza/),
14 November 2026, StartGate Maslak. Slides: <https://python-pizza.erhan.dev>

A small pizza-ordering API that shows the FastAPI basics in one project: path / query / header /
body parameters, validation with Pydantic, `Depends`, `async def` vs `def`, `BackgroundTasks` and
testing with `TestClient`.

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

## Project structure

Same layers as [ozgurkon](https://github.com/erhan/ozgurkon): **route → service → crud → model**.

```text
.
├── app
│   ├── main.py              # create_app() + lifespan (tables, starter menu)
│   ├── api
│   │   ├── deps.py          # Depends: DbSession, pagination, the chef's API key
│   │   └── v1/routes        # health, pizzas, orders -> api_router (/api/v1)
│   ├── core                 # settings (pydantic-settings), db, errors, middleware
│   ├── schemas              # Pydantic: what goes in and comes out
│   ├── models               # SQLAlchemy tables
│   ├── crud                 # database queries
│   └── services             # business rules
├── examples                 # the talk's building blocks (01-05), each runs on its own
├── tests                    # pytest + TestClient (in-memory SQLite)
└── pyproject.toml           # uv project, ruff and pytest config
```

## Endpoints

All under `/api/v1`. 🔑 = needs `X-API-Key`.

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Is the oven hot? |
| GET | `/pizzas` | Browse the menu (`vegetarian`, `max_price`, `limit`, `offset`) |
| GET | `/pizzas/{pizza_id}` | One pizza |
| POST | `/pizzas` 🔑 | Add a pizza to the menu |
| PATCH | `/pizzas/{pizza_id}` 🔑 | Change a pizza (only the fields you send) |
| DELETE | `/pizzas/{pizza_id}` 🔑 | Take it off the menu (a pizza with orders stays: `409`) |
| POST | `/orders` | Order a pizza |
| GET | `/orders` | List orders (`limit`, `offset`) |
| GET | `/orders/{order_id}` | Follow an order |
| PATCH | `/orders/{order_id}` 🔑 | Move an order along (`preparing` → `baking` → `on_the_way` → `delivered`) |

## Examples

One runnable single-file app for every step of the talk:

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

## Deploy

```bash
uv run fastapi run      # local server in production mode
uv run fastapi login    # FastAPI Cloud
uv run fastapi deploy
```

This example is kept small: no Alembic migrations, no JWT, no PostgreSQL. See
[ozgurkon](https://github.com/erhan/ozgurkon) for all three.

License: MIT.
