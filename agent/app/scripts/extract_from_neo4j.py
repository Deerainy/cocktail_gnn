from neo4j import GraphDatabase
import json

# 导入配置
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config import settings

NEO4J_URI = settings.NEO4J_URI
NEO4J_USER = settings.NEO4J_USER
NEO4J_PASSWORD = settings.NEO4J_PASSWORD

OUTPUT_FILE = "neo4j_business_export.txt"


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    result = session.run("""
        MATCH (a)-[r]->(b)
        RETURN 
            labels(a) AS a_labels,
            properties(a) AS a_props,
            type(r) AS rel_type,
            properties(r) AS r_props,
            labels(b) AS b_labels,
            properties(b) AS b_props
    """)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in result:
            f.write("=== TRIPLE ===\n")
            f.write("FROM_LABELS: " + json.dumps(record["a_labels"], ensure_ascii=False) + "\n")
            f.write("FROM_PROPS: " + json.dumps(record["a_props"], ensure_ascii=False) + "\n")
            f.write("REL_TYPE: " + record["rel_type"] + "\n")
            f.write("REL_PROPS: " + json.dumps(record["r_props"], ensure_ascii=False) + "\n")
            f.write("TO_LABELS: " + json.dumps(record["b_labels"], ensure_ascii=False) + "\n")
            f.write("TO_PROPS: " + json.dumps(record["b_props"], ensure_ascii=False) + "\n")
            f.write("\n")

driver.close()
print(f"导出完成: {OUTPUT_FILE}")