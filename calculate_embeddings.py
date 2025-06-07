import numpy as np
import os
from sentence_transformers import SentenceTransformer
text = np.array([])
model = SentenceTransformer("intfloat/multilingual-e5-large") #  We could use different models here
for filename in os.listdir('Documents_TXT/'):
    with open(os.path.join('Documents_TXT/',filename),"r") as file:
        for line in file:
            text = np.append(text,{'text':line,'filename':filename})

from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    FAISS
except NameError:
    from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from tqdm import tqdm  # For progress bar

# Function to encode a batch of sentences along with their indices
def encode_batch(batch):
    indices, sentences = zip(*batch)
    embeddings = model.encode(sentences)
    return list(zip(indices, embeddings))

# The sentences to encode
sentences = [(i, textlines['text']) for i, textlines in enumerate(text)]  # List of (index, sentence) tuples

# Batch processing
batch_size = 20  # Adjust based on your memory and model capacity
sentence_embeddings = []

# Use ThreadPoolExecutor to parallelize the batch processing
with ThreadPoolExecutor() as executor:
    futures = []
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        futures.append(executor.submit(encode_batch, batch))
    
    for future in tqdm(as_completed(futures), total=len(futures)):
        batch_embeddings = future.result()
        sentence_embeddings.extend(batch_embeddings)

# Add embeddings to the text array
for index, embedding in sentence_embeddings:
    text[index]['embedding'] = embedding

# Now the text array has embeddings added to each entry

np.save('Documents/text.npy', text) #save the text array to a file

# Load the text array with embeddings
text = np.load('Documents/text.npy', allow_pickle=True)

# Extract embeddings and convert to float32 numpy array
embeddings = np.stack([entry['embedding'] for entry in text]).astype('float32')

txt_loader = DirectoryLoader('Documents_TXT', glob = "**/*.txt", recursive= True)

documents = txt_loader.load()

# Vectorstore: https://python.langchain.com/en/latest/modules/indexes/vectorstores.html
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)
# Use FAISS.from_documents with the model's encode function as the embedding function
db = FAISS.from_documents(
    chunks,
    embedding=lambda docs: np.array(model.encode([doc.page_content for doc in docs]))
)
db.save_local("Documents/faiss_embeddings")