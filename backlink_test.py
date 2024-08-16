import asyncio
from typing import Optional

from beanie import BackLink, Document, Link, init_beanie
from beanie.odm.utils.encoder import Encoder
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field


class Person(Document):
    name: str
    age: int
    cars: list[Link["Car"]] = Field(default_factory=list)


class Car(Document):
    manufacturer: str
    price: float
    owner: Optional[BackLink[Person]] = Field(default=None, original_field="cars")


async def init():
    client = AsyncIOMotorClient(
        "mongodb://localhost:27017",
    )

    await init_beanie(database=client.test_db, document_models=[Person, Car])

    p1 = Person(
        name="John",
        age=25,
    )
    await p1.insert()

    c1 = Car(manufacturer="Toyota", price=10000, owner=p1)
    c2 = Car(manufacturer="BMW", price=20000, owner=p1)
    await c1.insert()
    await c2.insert()

    p1.cars.append(c1)
    p1.cars.append(c2)

    await p1.save()
    # The above code runs fine
    # but if I now want to get all the cars owned by John
    # I will get the BackLink encoding error
    person = await Person.find_one(Person.name == "John")
    print(person) # id=ObjectId('66863479f05c88b61f3c221f') revision_id=None name='John' age=25 cars=[<beanie.odm.fields.Link object at 0x7f2f38f21250>, <beanie.odm.fields.Link object at 0x7f2f38d6add0>]
    # cars are linked to person

    one_car = await Car.find(Car.manufacturer == "Toyota").to_list()
    print(one_car) # [Car(id=ObjectId('66863479f05c88b61f3c2220'), revision_id=None, manufacturer='Toyota', price=10000.0, owner=<beanie.odm.fields.BackLink object at 0x7f2f38e1f910>)]
    # it shows Toyota car has owner
    x = one_car[0].owner
    print(one_car[0].owner)
    
    # But when use person to find all those cars, returns an empty list.
    cars = await Car.find(Car.owner == person).to_list()
    print(cars) # [] (Empty list)

    cars = await Car.find(Car.owner.id == person.id, fetch_links=True).to_list()
    # loop over the cars and print them one by one
    for car in cars:
        # loop over the attributes of the car and print them
        for attr in car.__dict__.keys():
            print(attr, ":", getattr(car, attr))
        print()

    """
    Output:
    id : 66befc4f539eb035f205487c
    revision_id : None
    manufacturer : Toyota
    price : 10000.0
    owner : id=ObjectId('66befc4f539eb035f205487b') revision_id=None name='John' age=25 cars=[Car(id=ObjectId('66befc4f539eb035f205487c'), revision_id=None, manufacturer='Toyota', price=10000.0, owner=Person(id=ObjectId('66befc4f539eb035f205487b'), revision_id=None, name='John', age=25, cars=[<beanie.odm.fields.Link object at 0x00000252E14562A0>, <beanie.odm.fields.Link object at 0x00000252E14553A0>])), Car(id=ObjectId('66befc4f539eb035f205487d'), revision_id=None, manufacturer='BMW', price=20000.0, owner=Person(id=ObjectId('66befc4f539eb035f205487b'), revision_id=None, name='John', age=25, cars=[<beanie.odm.fields.Link object at 0x00000252E1455F70>, <beanie.odm.fields.Link object at 0x00000252E14552B0>]))]  

    id : 66befc4f539eb035f205487d
    revision_id : None
    manufacturer : BMW
    price : 20000.0
    owner : id=ObjectId('66befc4f539eb035f205487b') revision_id=None name='John' age=25 cars=[Car(id=ObjectId('66befc4f539eb035f205487c'), revision_id=None, manufacturer='Toyota', price=10000.0, owner=Person(id=ObjectId('66befc4f539eb035f205487b'), revision_id=None, name='John', age=25, cars=[<beanie.odm.fields.Link object at 0x00000252E1454C80>, <beanie.odm.fields.Link object at 0x00000252E1455FA0>])), Car(id=ObjectId('66befc4f539eb035f205487d'), revision_id=None, manufacturer='BMW', price=20000.0, owner=Person(id=ObjectId('66befc4f539eb035f205487b'), revision_id=None, name='John', age=25, cars=[<beanie.odm.fields.Link object at 0x00000252E1454E60>, <beanie.odm.fields.Link object at 0x00000252E14551C0>]))]     
    """

asyncio.run(init())