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

## Testing
- migrasi database lalu run semua testing `alembic upgrade head && pytest .`
- run testing secara paralel `pytest -n auto .`
- run semua testing pada folder tertentu `pytest ./{path}/{to}/{folder}`
- run semua testing pada file tertentu `pytest ./{path}/{to}/{folder}/{file}.py`
- run semua testing pada class tertentu `pytest ./{path}/{to}/{folder}/{file}.py::{nama class}`
- run satu testing pada class tertentu `pytest ./{path}/{to}/{folder}/{file}.py::{nama class}::{nama fungsi}`
- run verbose (lihat print) `pytest . -s`
