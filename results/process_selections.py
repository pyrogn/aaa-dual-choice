import os
from dotenv import load_dotenv
import pandas as pd
import psycopg
import choix
import numpy as np

resp = load_dotenv()
assert resp

db_host = "db"
db_port = "5432"
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
assert db_password, "where is password?"

with psycopg.connect(
    host=db_host,
    port=db_port,
    dbname=db_name,
    user=db_user,
    password=db_password,
) as conn:
    with conn.cursor() as cur:
        query = "SELECT * FROM image_selections"
        cur.execute(query)

        rows = cur.fetchall()
        assert cur.description

        column_names = [desc[0] for desc in cur.description]

        df = pd.DataFrame(rows, columns=column_names)

assert df.shape[0] != 0, "df is empty"
print(
    f"{df.user_id.nunique()} unique users\n",
    f"{df.shape[0]} selections\n",
    f"{df.shape[0] / df.user_id.nunique() :.1f} selections per user\n",
    sep="",
)

df.to_csv("/app/results/selection_results.csv", index=False)

n_items = df.selected_id.nunique()
data = df[["selected_id", "other_id"]].to_numpy()

params = choix.ilsr_pairwise(n_items, data)
print("ilsr_pairwise params:", params)
print("ranking (worst to best):", np.argsort(params))
