from chromadb import Client
client=Client()
memory=client.create_collection(name='evez_memory')
