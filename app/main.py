from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="CI/CD Demo API", version="1.0.0")

# In-memory "database" just for demo purposes
_items: dict[int, "Item"] = {}
_next_id = 1


class Item(BaseModel):
    name: str
    price: float
    in_stock: bool = True


class ItemOut(Item):
    id: int


@app.get("/")
def read_root():
    return {"status": "ok", "service": "cicd-demo"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/items", response_model=list[ItemOut])
def list_items():
    return [ItemOut(id=item_id, **item.model_dump()) for item_id, item in _items.items()]


@app.post("/items", response_model=ItemOut, status_code=201)
def create_item(item: Item):
    global _next_id
    item_id = _next_id
    _items[item_id] = item
    _next_id += 1
    return ItemOut(id=item_id, **item.model_dump())


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int):
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemOut(id=item_id, **item.model_dump())


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    del _items[item_id]
    return None
