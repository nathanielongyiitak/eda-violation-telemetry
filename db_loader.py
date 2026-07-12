import sys
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from log_parser import parse_eda_stream

def get_db_collection(uri="mongodb://localhost:27017/", db_name="eda_verification", coll_name="violations"):
    """Establishes connection to the data store."""
    client = MongoClient(uri)
    db = client[db_name]
    return db[coll_name]

def setup_esr_indices(collection):
    """
    TASK 2: Programmatically build the compound index.
    Apply the Equality -> Sort -> Range (ESR) rule strictly.
    Target Query: 
      - Match specific layer ('err_lay') [Equality]
      - Sort alphabetically by error type ('err_type') [Sort]
      - Filter by high vertex counts ('err_vertices') [Range]
    """
    print("[*] Engineering compound index structures...", file=sys.stderr)
    
    # IMPLEMENT HERE: Define the correct compound index tuple sequence
    index_spec = [("err_lay", 1), ("err_type", 1), ("err_vertices", 1)]
    collection.create_index(index_spec, name="idx_eda_esr_optimization")
    
    pass

def ingest_violations(file_path, collection, batch_size=1000):
    """
    TASK 1: Implement the Micro-Batching Ingestion Loop.
    Consume the parse_eda_stream generator safely.
    """
    buffer = []
    total_inserted = 0
    
    print(f"[*] Beginning ingestion stream for: {file_path}", file=sys.stderr)
    
    # Clean out old data for fresh run metrics
    collection.delete_many({}) 
    
    try:
        # Loop over Quest 1 generator stream
        for record in parse_eda_stream(file_path):
            buffer.append(record)
            if (len(buffer) >= batch_size):
                total_inserted += len(buffer)
                collection.insert_many(buffer)
                buffer = []
        if(buffer):
            total_inserted += len(buffer)
            collection.insert_many(buffer)
            buffer = []
    except BulkWriteError as bwe:
        # Use the .details attribute to look inside
        error_details = bwe.details
        print(f"Number of documents successfully inserted: {error_details['nInserted']}")
        
        for write_error in error_details['writeErrors']:
            print(f"Doc index {write_error['index']} failed with code {write_error['code']}: {write_error['errmsg']}")
    
    # IMPLEMENT HERE: Flush any remaining records lingering in the buffer after stream termination.

    print(f"[+] Ingestion complete. Total records persisted: {total_inserted}", file=sys.stderr)

def profile_query_execution(collection):
    """
    TASK 3: Query Execution Profiling.
    Execute an optimized query tree match and extract the visual statistics.
    """
    print("\n[*] Interrogating query execution plan...", file=sys.stderr)
    
    # Example criteria matching index structure
    query_match = {"err_lay": "51 (VIA2)"}  
    query_sort = [("err_type", 1)]

    # IMPLEMENTATION: Execute the raw explain command against the database
    explain_command = {
        'explain': {
            'find': collection.name, 
            'filter': query_match,
            'sort': dict(query_sort) if query_sort else None
        },
        'verbosity': 'executionStats'
    }

    # Run the command directly 
    execution_profile = collection.database.command(explain_command)

    # Safely print your terminal summary
    print(execution_profile.get("executionStats", {}))


    pass

def main():
    # Setup database pointers
    try:
        collection = get_db_collection()
        
        # 1. Establish index structures before heavy write loops
        setup_esr_indices(collection)
        
        # 2. Run high-throughput batched ingestion
        ingest_violations("./sample.log", collection, batch_size=1000)
        
        # 3. Analyze the query execution plan stage
        profile_query_execution(collection)
        
    except Exception as e:
        print(f"[-] Critical failure in database orchestration layer: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()