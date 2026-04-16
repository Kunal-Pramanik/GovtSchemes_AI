import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import time

def main():
    print("Loading preprocessed data...")
    df = pd.read_csv('myscheme_cleaned.csv')
    
    # We drop any rows that somehow have an empty combined_text (shouldn't happen)
    df = df.dropna(subset=['combined_text'])
    texts = df['combined_text'].tolist()
    print(f"Loaded {len(texts)} documents for vectorization.")
    
    # Initialize embedding model 
    # 'all-MiniLM-L6-v2' is fast, small and highly effective for general semantic search
    print("Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings... This may take a few minutes.")
    start = time.time()
    # Generate embeddings
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    # Convert nicely to numpy float32 as expected by FAISS
    embeddings = np.array(embeddings).astype('float32')
    print(f"Embeddings generated in {time.time()-start:.2f} seconds. Shape: {embeddings.shape}")
    
    # Create FAISS flat inner product (or L2) index
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    # L2 distance index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index
    faiss.write_index(index, 'data_pipeline/schemes.index')
    
    # Save mapping metadata (the documents themselves) so the backend can retrieve the text
    # We will map FAISS id (0 to len-1) to the actual Scheme data
    meta_data = []
    for idx, row in df.iterrows():
        meta_data.append({
            'id': idx,
            'name': str(row.get('Scheme Name', 'Unknown')),
            'short_title': str(row.get('Short Title', '')),
            'text': str(row['combined_text'])
        })
        
    with open('data_pipeline/schemes_meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
    print("Vectorization complete! Saved 'schemes.index' and 'schemes_meta.json' in 'data_pipeline/'.")

if __name__ == "__main__":
    main()
