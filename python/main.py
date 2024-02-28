import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException,UploadFile
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

app = FastAPI()
logger = logging.getLogger("uvicorn")

# ロガーのログレベルをDEBUGに設定
logger.setLevel(logging.DEBUG)
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
import json

# JSONファイルのパス
json_file_path = "items.json"

def read_items_from_json():
    try:
        with open(json_file_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return {"items": []}

def write_items_to_json(items):
    with open(json_file_path, "w") as json_file:
        json.dump(items, json_file, indent=4)

# 画像を保存するディレクトリのパスを設定する
images_path = Path(__file__).resolve().parent / "images"
images_path.mkdir(exist_ok=True)  # ディレクトリがなければ作成


def save_image(image_file: UploadFile = Form(...)):
    data = image_file.file.read()
    hash_sha256 = pathlib.sha256(data).hexdigest()
    file_name = f"{hash_sha256}.jpg"
    file_path = images / file_name
    with open(file_path, "wb") as f:
        f.write(data)
    return file_name


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...)):
    logger.info(f"Receive item: {name}, category: {category}")
    items_data = read_items_from_json()
    items_data["items"].append({"name": name, "category": category})
    write_items_to_json(items_data)
    return {"message": f"item received: {name}"}

@app.get("/items")
def get_items():
    return read_items_from_json()

@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"
    return FileResponse(image)

# JSONファイルから商品データを読み込む関数
def load_items() -> List[Dict]:
    with open("items.json", "r") as file:
        data = json.load(file)
    return data["items"]

@app.get("/items/{item_id}")
def read_item(item_id: str):
    items = load_items()
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}

import sqlite3

# JSONファイルからデータを読み込む
with open('items.json', 'r') as f:
    items_data = json.load(f)

# SQLite3データベースに接続する
conn = sqlite3.connect('db/mercari.sqlite3')
cursor = conn.cursor()

# itemsテーブルを作成する
cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    category TEXT,
                    image_name TEXT
                )''')

# 読み込んだデータをデータベースに挿入する
for item in items_data:
    cursor.execute('''INSERT INTO items (name, category, image_name)
VALUES (?, ?, ?)''', (item['name'], item['category'], item['image_name']))

# 変更をコミットする
conn.commit()

# 接続を閉じる
conn.close()