from pymongo import MongoClient
from urllib.parse import quote_plus

username = "SCMX_PERT_LITE"
password = quote_plus("Scmx123")

url = (
    f"mongodb+srv://{username}:{password}"
    f"@users.qarlknd.mongodb.net/"
)

client = MongoClient(url)

print(client.list_database_names())