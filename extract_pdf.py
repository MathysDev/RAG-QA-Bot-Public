#Prepares the directories for the PDF and TXT files
import os
import pip
drivepath = './'

pdf_directory = drivepath+'Muster_Documents/'
txt_directory = drivepath+'Documents_TXT/'

# Create the directories if they do not exist
os.makedirs(pdf_directory, exist_ok=True)
os.makedirs(txt_directory, exist_ok=True)


import os
import pdfreader
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

import time



# Initialize a variable to store text from the current PDF
text = np.array([])

# Function to process a single PDF file
def process_pdf(filename):
    local_text = []
    if filename.endswith('.pdf'):
        # Open the PDF file
        with open(os.path.join(pdf_directory, filename), 'rb') as pdf_file:
            # Create a PDF reader object
            pdf_reader = pdfreader.SimplePDFViewer(pdf_file)
            doc = pdfreader.PDFDocument(pdf_file)
            
            # Iterate through all the pages and extract text
            all_pages = [p for p in doc.pages()]
            pdf_title = pdf_reader.metadata.get('Title', '')

            for i in range(len(all_pages)):   #iterate through all pages
                pdf_reader.navigate(i + 1)
                pdf_reader.render()
                page_text = ''
                with open(os.path.join(txt_directory, f"{filename}-{i}.txt"), "w") as f: #save text to txt file
                    for line in pdf_reader.canvas.strings:
                        try:
                            f.write(line)
                            page_text += line
                            if '.' in line and page_text[-4:] != 'Mio.': #if line ends with a dot, it is the end of a sentence and a new line is started
                                f.write('\n')
                                local_text.append({'text': str(page_text), 'filename': filename, 'page': i + 1, 'Titel': pdf_title})
                                page_text = ''
                        except Exception as e:
                            print(f"Error processing line in {filename} page {i}: {e}")
                    f.close()
    return local_text



# Define the number of CPUs to use
num_cpus = os.cpu_count()  # or set a specific number, e.g., num_cpus = 4

# Use ThreadPoolExecutor to parallelize the processing of PDF files
with ThreadPoolExecutor(max_workers=num_cpus) as executor:
    # Submit the PDF processing tasks
    futures = [executor.submit(process_pdf, filename) for filename in os.listdir(pdf_directory)]

    
    for future in as_completed(futures):
        text = np.append(text, future.result())
    


# text now contains the text of all PDFs in the directory
# more preprocessing can be done here, e.g. removing stopwords, stemming, etc.