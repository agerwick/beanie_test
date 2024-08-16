import asyncio
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Union, List, Dict, Optional, Annotated, TYPE_CHECKING
from beanie import Document, Indexed, init_beanie, before_event, Insert, Replace, Update, Save, SaveChanges, Delete, ValidateOnSave, UpdateResponse
from datetime import datetime

class TimeStamped(BaseModel):
    inserted_at: Optional[datetime] = None
    replaced_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    saved_at: Optional[datetime] = None
    saved_changes_at: Optional[datetime] = None
    validated_on_save_at: Optional[datetime] = None

    @before_event([Insert])
    async def set_inserted_at(self):
        self.inserted_at = datetime.now()

    @before_event([Replace])
    async def set_replaced_at(self):
        self.replaced_at = datetime.now()

    @before_event([Update])
    async def set_updated_at(self):
        self.updated_at = datetime.now()

    @before_event([Save])
    async def set_saved_at(self):
        self.saved_at = datetime.now()

    @before_event([SaveChanges])
    async def set_saved_changes_at(self):
        self.saved_changes_at = datetime.now()

    @before_event([ValidateOnSave])
    async def set_validated_on_save_at(self):
        self.validated_on_save_at = datetime.now()


class Category(BaseModel):
    name: str
    description: str


class Product(Document, TimeStamped):
    name: Indexed(str)
    description: Optional[str] = None
    price: Indexed(float)
    category: Category

    @classmethod
    async def delete_many(cls, *args):
        # find all documents that match the query and loop over them to delete them one by one
        async for doc in cls.find(*args):
            await doc.delete()

def secs_after(dt1, dt2):
    if dt1 is None or dt2 is None:
        return ""
    else:
        return f" -- {(dt1 - dt2).total_seconds()}s after insert"
    
def print_product(product):
    print(f"Product: {product.name} - Price: {product.price}")
    print(f"Insert: {product.inserted_at}")
    print(f"Replace: {product.replaced_at} {secs_after(product.replaced_at, product.inserted_at)}")
    print(f"Update: {product.updated_at} {secs_after(product.updated_at, product.inserted_at)}")
    print(f"Save: {product.saved_at} {secs_after(product.saved_at, product.inserted_at)}")
    print(f"SaveChanges: {product.saved_changes_at} {secs_after(product.saved_changes_at, product.inserted_at)}")
    print(f"ValidateOnSave: {product.validated_on_save_at} {secs_after(product.validated_on_save_at, product.inserted_at)}")
    print()


async def example():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.db_name, document_models=[Product])

    # Delete any existing documents with the name "Gold bar" or "Tony's" before we start
    await Product.delete_many(Product.name=="Gold bar")
    await Product.delete_many(Product.name=="Tony's")

    chocolate = Category(name="Chocolate", description="A preparation of roasted and ground cacao seeds.")
    product = Product(name="Tony's", price=5.95, category=chocolate)

    await product.insert()
    print("BEFORE UPDATE:")
    print_product(product)
    # Product: Tony's - Price: 5.95
    # Insert: 2024-08-16 13:10:49.901865
    # Replace: None
    # Update: None
    # Save: None
    # SaveChanges: None
    # ValidateOnSave: 2024-08-16 13:10:49.901865  -- 0.0s after insert
    await asyncio.sleep(0.2) # wait for a while

    # Update the product
    await product.set({Product.name:"Gold bar"})
    print("AFTER SETTING NAME:")
    print_product(product)
    # Product: Gold bar - Price: 5.95
    # Insert: 2024-08-16 13:10:49.901000
    # Replace: None
    # Update: None
    # Save: None
    # SaveChanges: None
    # ValidateOnSave: 2024-08-16 13:10:49.901000  -- 0.0s after insert
    await asyncio.sleep(0.2) # wait for a while

    # fetch the product again (is this necessary?)
    await product.save()
    print("AFTER SAVE:")
    print_product(product)
    # Product: Gold bar - Price: 5.95
    # Insert: 2024-08-16 13:10:49.901000
    # Replace: None
    # Update: None
    # Save: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    # SaveChanges: None
    # ValidateOnSave: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    await asyncio.sleep(0.2) # wait for a while

    # increase price
    await product.inc({Product.price: 1}) 
    print("AFTER INCREMENTING PRICE:")
    print_product(product)
    # Product: Gold bar - Price: 5.95
    # Insert: 2024-08-16 13:10:49.901000
    # Replace: None
    # Update: None
    # Save: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    # SaveChanges: None
    # ValidateOnSave: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    await asyncio.sleep(0.2) # wait for a while

    # update price
    await product.update({"$set": {Product.price: 3.33}})
    print("AFTER UPDATING PRICE:")
    print_product(product)
    # Product: Gold bar - Price: 3.33
    # Insert: 2024-08-16 13:10:49.901000
    # Replace: None
    # Update: None
    # Save: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    # SaveChanges: None
    # ValidateOnSave: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    await asyncio.sleep(0.2) # wait for a while

    # replace the product
    product_dict = product.model_dump()
    product_dict["price"] = 9.99
    product = Product(**product_dict)
    await product.replace()
    print("AFTER REPLACING PRODUCT:")
    print_product(product)
    # Product: Gold bar - Price: 9.99
    # Insert: 2024-08-16 13:10:49.901000
    # Replace: 2024-08-16 13:10:50.980980  -- 1.07998s after insert
    # Update: None
    # Save: 2024-08-16 13:10:50.330000  -- 0.429s after insert
    # SaveChanges: None
    # ValidateOnSave: 2024-08-16 13:10:50.981688  -- 1.080688s after insert
    await asyncio.sleep(0.2) # wait for a while

if __name__ == "__main__":
    asyncio.run(example())
