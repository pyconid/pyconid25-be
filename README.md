# pyconid25-be
BE for PyCon ID 2025 website

## Requirements
- python 3.12
- postgresql 14

## Installation
- buat python virtual environtment `python -m venv env`
- aktifkan python virtual environtment `source env/bin/activate`
- install depedency ke virtual environtment `pip install -r requirements.txt`
- copy file .env.example menjadi .env `cp .env.example .env` lalu isi berdasarkan konfigurasi postgresql
- migrasi tabel menggunakan alembic `alembic upgrade head`
- jalankan aplikasi `uvicorn main:app --reload`
- buka openapi doc di http://localhost:8000/docs

## Code Format
`ruff format`

## Static Analysis
`ruff check`

## Testing
- migrasi database lalu run semua testing `alembic upgrade head && pytest .`
- run testing secara paralel `pytest -n auto .`
- run semua testing pada folder tertentu `pytest ./{path}/{to}/{folder}`
- run semua testing pada file tertentu `pytest ./{path}/{to}/{folder}/{file}.py`
- run semua testing pada class tertentu `pytest ./{path}/{to}/{folder}/{file}.py::{nama class}`
- run satu testing pada class tertentu `pytest ./{path}/{to}/{folder}/{file}.py::{nama class}::{nama fungsi}`
- run verbose (lihat print) `pytest . -s`

## Kontribusi
untuk tata cara kontribusi bisa dilihat di [CONTRIBUTING.md](./CONTRIBUTING.md) dan diharapkan kontributor memematuhi [Code of Conduct](./CODE%20OF%20CONDUCT.md) yang berlaku.

## Common issues
### 1. Permission Denied For Schema Public Ketika Menjalankan Alembic
Jika ada muncul kesalahan seperti ini ketika menjalankan alembic untuk pertama kalinya,
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.InsufficientPrivilege) permission denied for schema public
LINE 2: CREATE TABLE public.alembic_version (
                     ^
[SQL: 
CREATE TABLE public.alembic_version (
        version_num VARCHAR(32) NOT NULL, 
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
)
```

solusinya adalah memberikan permission ke pada user yang bersangkutan ke schema public.

Berikan akses usage dan create schema public ke user.
```
GRANT USAGE ON SCHEMA public TO user;
GRANT CREATE ON SCHEMA public TO user;
```

Cara ini juga dapat dicoba:
```
GRANT ALL ON SCHEMA public TO user;
```

Login sebagai user-nya, lalu uji coba:
```
SELECT has_schema_privilege('public', 'CREATE');`
```

Luarannya: `t` (true) jika sudah benar. Setelah ini dapat menjalankan alembic kembali.