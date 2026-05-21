import kuzu
import os
import shutil

# 1. Define the database directory
DB_PATH = '../generated_files/instance_db'

# Optional: Clean up existing database for a fresh run
if os.path.exists(DB_PATH):
    print(f"Removing existing database at {DB_PATH}...")
    shutil.rmtree(DB_PATH)

# 2. Initialize the database and connection
print(f"Initializing Kuzu database at {DB_PATH}...")
db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

# 3. Define the schema creation queries
schema_queries = [
    # ==========================================
    # NODE TABLES (ENTITIES)
    # ==========================================
    """
    CREATE NODE TABLE Person (
        personId STRING,
        firstName STRING,
        lastName STRING,
        dob DATE,
        taxId STRING,
        nationality STRING,
        pepStatus BOOLEAN,
        kycStatus STRING,
        riskScore DOUBLE,
        PRIMARY KEY (personId)
    )
    """,
    """
    CREATE NODE TABLE Company (
        companyId STRING,
        name STRING,
        regNumber STRING,
        incorporationDate DATE,
        industryCode STRING,
        kycStatus STRING,
        riskScore DOUBLE,
        PRIMARY KEY (companyId)
    )
    """,
    """
    CREATE NODE TABLE Account (
        accountId STRING,
        accountType STRING,
        balance DOUBLE,
        currency STRING,
        status STRING,
        openedDate DATE,
        branchCode STRING,
        PRIMARY KEY (accountId)
    )
    """,
    """
    CREATE NODE TABLE Transaction (
        txId STRING,
        amount DOUBLE,
        baseCurrencyAmount DOUBLE,
        timestamp TIMESTAMP,
        txType STRING,
        channel STRING,
        status STRING,
        PRIMARY KEY (txId)
    )
    """,
    """
    CREATE NODE TABLE Address (
        addressId STRING,
        street STRING,
        city STRING,
        state STRING,
        zipCode STRING,
        country STRING,
        PRIMARY KEY (addressId)
    )
    """,
    """
    CREATE NODE TABLE Device (
        deviceId STRING,
        deviceType STRING,
        os STRING,
        ipAddress STRING,
        macAddress STRING,
        isp STRING,
        PRIMARY KEY (deviceId)
    )
    """,
    """
    CREATE NODE TABLE Document (
        docId STRING,
        docType STRING,
        issuedCountry STRING,
        expiryDate DATE,
        isForged BOOLEAN,
        PRIMARY KEY (docId)
    )
    """,
    """
    CREATE NODE TABLE WatchlistEntity (
        entityId STRING,
        listName STRING,
        listType STRING,
        addedDate DATE,
        PRIMARY KEY (entityId)
    )
    """,

    # ==========================================
    # RELATIONSHIP TABLES (EDGES)
    # ==========================================
    """
    CREATE REL TABLE OWNS_ACCOUNT (
        FROM Person TO Account,
        FROM Company TO Account,
        role STRING,
        since DATE
    )
    """,
    """
    CREATE REL TABLE HAS_ADDRESS (
        FROM Person TO Address,
        FROM Company TO Address,
        addressType STRING,
        isCurrent BOOLEAN
    )
    """,
    """
    CREATE REL TABLE USES_DEVICE (
        FROM Person TO Device,
        FROM Company TO Device,
        firstSeen TIMESTAMP,
        lastSeen TIMESTAMP,
        trustScore DOUBLE
    )
    """,
    """
    CREATE REL TABLE SENT_TX (
        FROM Account TO Transaction,
        postTxBalance DOUBLE
    )
    """,
    """
    CREATE REL TABLE RECEIVED_TX (
        FROM Transaction TO Account,
        postTxBalance DOUBLE
    )
    """,
    """
    CREATE REL TABLE INITIATED_VIA (
        FROM Transaction TO Device,
        locationData STRING
    )
    """,
    """
    CREATE REL TABLE WORKS_FOR (
        FROM Person TO Company,
        jobTitle STRING,
        employmentType STRING,
        startDate DATE,
        salaryRange STRING
    )
    """,
    """
    CREATE REL TABLE OWNS_EQUITY (
        FROM Person TO Company,
        FROM Company TO Company,
        percentage DOUBLE,
        votingRights DOUBLE
    )
    """,
    """
    CREATE REL TABLE DIRECTS (
        FROM Person TO Company,
        role STRING,
        appointedDate DATE
    )
    """,
    """
    CREATE REL TABLE RELATED_TO (
        FROM Person TO Person,
        relationType STRING
    )
    """,
    """
    CREATE REL TABLE PROVIDED_DOC (
        FROM Person TO Document,
        FROM Company TO Document,
        submissionDate TIMESTAMP,
        verificationMethod STRING
    )
    """,
    """
    CREATE REL TABLE MATCHES_WATCHLIST (
        FROM Person TO WatchlistEntity,
        FROM Company TO WatchlistEntity,
        similarityScore DOUBLE,
        matchDate TIMESTAMP,
        status STRING
    )
    """
]

# 4. Execute queries sequentially
print("Creating schema...")
for i, query in enumerate(schema_queries, 1):
    try:
        # Extract the table name for logging purposes
        table_type = "NODE" if "NODE TABLE" in query else "RELATIONSHIP"
        table_name = query.split('TABLE ')[1].split(' (')[0].strip()

        print(f"[{i}/{len(schema_queries)}] Creating {table_type} table: {table_name}")
        conn.execute(query)
    except Exception as e:
        print(f"Error creating table '{table_name}': {e}")
        # Stop execution on failure to prevent broken schemas
        break

print("\nSchema creation complete! The Kuzu database is ready for data ingestion.")