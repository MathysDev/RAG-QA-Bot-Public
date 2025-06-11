import requests
import json
from django.shortcuts import render
from django.http import HttpResponse
from .models import RAGQA
from django.contrib.auth.models import User
import threading
# Delay import of FAISS and HuggingFaceEmbeddings until after index view is rendered

# Globals for embeddings and FAISS
embeddings = None
FAISS = None
HuggingFaceEmbeddings = None
db = None  # Placeholder for the FAISS database
langchain_ready = threading.Event()
model = 'gemma3'

def import_langchain_modules_once():
    global embeddings, FAISS, HuggingFaceEmbeddings, db
    from langchain_community.vectorstores import FAISS as _FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings as _HuggingFaceEmbeddings
    embeddings = _HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    FAISS = _FAISS
    HuggingFaceEmbeddings = _HuggingFaceEmbeddings
    db = FAISS.load_local('Documents/faiss_embeddings', embeddings, allow_dangerous_deserialization=True )
    langchain_ready.set()  # Signal that initialization is done
# Start background initialization ONCE at import time
threading.Thread(target=import_langchain_modules_once, daemon=True).start()

ollama_ready = threading.Event()
def initialize_ollama():
    print("now pulling the model from Ollama")
    ollama_api_url = "http://localhost:11434/api/pull"  # Replace with your Ollama API endpoint
    payload = {"model": model}
    response = requests.post(ollama_api_url, json=payload)
    print(response.text)
    if response.status_code == 200:
        print("Model pulled successfully")
        ollama_api_url = "http://localhost:11434/api/generate"  # Replace with your Ollama API endpoint
        response =requests.post(ollama_api_url, json=payload)
    else:
        print(f"Error pulling model: {response.text}")
    ollama_ready.set()  # Signal that Ollama is ready

    

import os
import shutil
import glob
import asyncio



def index(request):
    print("Inside index view")
    get_header_info(request)  # Call get_header_info to extract header information
    messages = []  # Initialize messages as an empty list
    userid = request.headers.get('X-MS-CLIENT-PRINCIPAL-ID',1)  # Get user ID from headers, default to 1 if not present
    if RAGQA.objects.exists():
        
        messages = RAGQA.objects.filter(userid=userid)
    username = request.headers.get('X-MS-CLIENT-PRINCIPAL-NAME', 'Entwickler')
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_unusable_password()
        user.save()
    threading.Thread(target=initialize_ollama, daemon=True).start()  # Start Ollama initialization in a separate thread
    

                              
                                                                                               
                                 
                                                          
                        
   
    return render(request, 'chat_window.html', {'messages': messages, 'userid': userid})
    

def review(request):
    print("Inside review view")
    messages = RAGQA.objects.all()
    if not messages:
        print("No messages found in the database.")
        messages = []
    return render(request, 'review.html', {'messages': messages})

def get_header_info(request):
    print("Inside get_header_info view")
    username = request.headers.get('X-MS-CLIENT-PRINCIPAL-NAME', 'Entwickler')
    userid = request.headers.get('X-MS-CLIENT-PRINCIPAL-ID',1) 
    print(f"Username: {username}, User ID: {userid}")  # Debugging line

def input_box(request):
    print("Inside input_box view")
    messages = []  # Initialize messages as an empty list
    userid = request.headers.get('X-MS-CLIENT-PRINCIPAL-ID',1)  # Get user ID from headers, default to 1 if not present
    if not ollama_ready.is_set():
        threading.Thread(target=initialize_ollama, daemon=True).start()  # Start Ollama initialization in a separate thread
        
    if request.method == 'POST':
        user_input = request.POST.get('user_input')
        user = request.headers.get('X-MS-CLIENT-PRINCIPAL-NAME', 'Entwickler')

        
        print(f"User Input: {user_input}")  # Debugging line
        new_message = RAGQA.objects.create(question=user_input, user=user, userid=userid)
        ollama_ready.wait()
        generate_response(new_message)
        messages = RAGQA.objects.filter(userid=userid)
        return render(request, 'chat_window.html', {'messages': messages, 'userid': userid})
    else:
        if RAGQA.objects.exists():
     
            messages = RAGQA.objects.filter(userid=userid)
        

                                                   
                     
    return render(request, 'chat_window.html', {'messages': messages, 'userid': userid})


def generate_response(question):
    print("Inside generate_response view")
    documents = get_documents(question.question)  # Call get_documents to retrieve relevant documents
    prompt = f"Unterlagen:\n{documents}\n\nQuestion: {question.question}\nAntwort:"
    ollama_api_url = "http://localhost:11434/api/generate"  # Replace with your Ollama API endpoint
    payload = {"prompt": prompt  , "model":model,"system":"Bleibe stets freundlich. Antworte immer in deutscher Sprache anwtwortet. Halte die Antworten stets kurz und präzise. Beantworte die Frage so gut wie möglich unter Berücksichtigung der bereitgestellten Unterlagen. Wenn du keine relevanten Informationen findest, antworte mit 'Keine relevanten Unterlagen gefunden.'","temperature":0.1,"top_p":0.95,"top_k":40,"max_tokens":1000,"stream":False}
    response = requests.post(ollama_api_url, json=payload)
 
    
    if response.status_code == 200:
        response_text = response.content.decode('utf-8')  # Decode response as UTF-8
        response_lines = response_text.strip().split('\n')
        responses = [json.loads(line)["response"] for line in response_lines]
        answer = "".join(responses)

    else:
        answer = "Error generating response"
        print(f"Error: {response.text}")
    print(f"Generated Answer: {answer}")  # Debugging line
    RAGQA.objects.filter(id=question.id).update(answer=answer,documents=documents)

def clear_chat(request):
    print("Inside clear_chat view")
    
    RAGQA.objects.filter(userid=request.headers.get('X-MS-CLIENT-PRINCIPAL-ID',1)).delete()
    return index(request)



def get_documents(question):
    print("Inside get_documents view")
    # This function should implement the logic to retrieve relevant documents based on the question
    if not os.path.exists('Documents/faiss_embeddings'):
        print("FAISS embeddings directory does not exist.")
        if os.path.exists('Muster_Documents'):
            print("Muster_Documents directory exists, copying files to Documents_TXT.")
            os.makedirs('Documents', exist_ok=True)
            for root, dirs, files in os.walk('Muster_Documents'):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, 'Muster_Documents')
                    dest_path = os.path.join('Documents', rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy(src_path, dest_path)
            
        return ["Keine relevanten Unterlagen gefunden."]
    else:
        langchain_ready.wait()

        results = db.similarity_search(question, k=3 )  # Adjust k as needed
    if results:
        return [doc.page_content for doc in results]
    else:
        print("Keine relevanten Unterlagen gefunden.")
        return ["Keine relevanten Unterlagen gefunden."]