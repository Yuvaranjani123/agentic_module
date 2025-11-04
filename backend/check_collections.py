"""Quick script to check ChromaDB collections."""
import chromadb
from pathlib import Path

# Check both products
products = ['ActivAssure', 'ActivFit']
project_root = Path(__file__).parent.parent
base_dir = project_root / "media" / "output" / "chroma_db"

print("=" * 60)
print("ChromaDB Collection Status")
print("=" * 60)

for product in products:
    product_dir = base_dir / product
    print(f"\n📦 {product}:")
    print(f"   Path: {product_dir}")
    
    if not product_dir.exists():
        print(f"   ❌ Directory does not exist!")
        continue
    
    try:
        client = chromadb.PersistentClient(path=str(product_dir))
        collection = client.get_collection("insurance_chunks")
        count = collection.count()
        
        if count > 0:
            print(f"   ✅ Collection found with {count} documents")
            
            # Show a sample
            sample = collection.peek(limit=1)
            if sample['documents']:
                print(f"   📄 Sample: {sample['documents'][0][:100]}...")
        else:
            print(f"   ⚠️  Collection exists but is EMPTY (0 documents)")
            print(f"   💡 Run ingestion for {product} to populate it")
            
    except Exception as e:
        print(f"   ❌ Collection not found: {e}")
        print(f"   💡 Run ingestion for {product} to create it")

print("\n" + "=" * 60)
