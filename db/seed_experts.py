# seed_experts.py

from config import db
from pymongo.errors import PyMongoError

experts_seed = [
    {
        "name": "Mr. Okoro",
        "phone": "+2347059093412",
        "specialty": "Yam & Cassava",
        "languages": ["English", "Igbo"],
        "available": True
    },
    {
        "name": "Aunty Nkechi",
        "phone": "+2347059093413",
        "specialty": "Poultry",
        "languages": ["Pidgin", "English"],
        "available": True
    }
]

try:
    # Optional: Avoid duplicates if this is re-run
    for expert in experts_seed:
        if not db.experts.find_one({"phone": expert["phone"]}):
            db.experts.insert_one(expert)
            print(f"✅ Expert '{expert['name']} with {expert['phone']}' added.")
        else:
            print(f"⚠️ Expert '{expert['name']} with {expert['phone']}' already exists. Skipping.")

except PyMongoError as e:
    print(f"❌ Error inserting experts into MongoDB: {e}")
