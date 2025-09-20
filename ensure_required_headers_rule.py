import os, sqlite3, json, time

DB = r"C:\Users\monti\Projects\DashValidator\app.db"
assert os.path.exists(DB), f"DB not found at {DB}"

def table_info(con, table):
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    # cols: cid, name, type, notnull (0/1), dflt_value, pk
    rows = cur.fetchall()
    return { r[1]: {"type": r[2], "notnull": bool(r[3]), "default": r[4]} for r in rows }

con = sqlite3.connect(DB)
cur = con.cursor()

# 1) Ensure params column exists
cols = table_info(con, "rules")
if "params" not in cols:
    cur.execute("ALTER TABLE rules ADD COLUMN params TEXT")
    con.commit()
    print("Added column: params TEXT")
else:
    print("Column 'params' already exists")

# 2) Upsert the Required Headers rule
params = {
    "required_headers": ["#", "Facture", "ID RAMQ", "Date de Service", "Début", "Fin", "Periode",
                         "Lieu de pratique", "Secteur d'activité", "Diagnostic", "Code", "Unités",
                         "Règle", "Élément de contexte", "Montant Preliminaire", "Montant payé",
                         "Doctor Info",
                         "DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalPrelAmount",
                         "DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalFinalAmount",
                         "DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalCount",
                         "Agence", "Patient", "Grand Total"],
    "delimiter": ";",
    "ignore_extras": True,
    "case_insensitive": True,
    "trim_whitespace": True
}
rule = {
    "code": "REQUIRED_HEADERS",
    "name": "required_headers",
    "description": "Validates that all mandatory CSV headers are present (extras allowed).",
    "category": "input_format",
    "severity": "error",
    "is_active": 1,
    "params": json.dumps(params, ensure_ascii=False),
}
now = time.strftime("%Y-%m-%d %H:%M:%S")

cols = table_info(con, "rules")
has_created_at = "created_at" in cols and cols["created_at"]["notnull"]
has_updated_at = "updated_at" in cols and cols["updated_at"]["notnull"]

cur.execute("SELECT 1 FROM rules WHERE name=?", (rule["name"],))
exists = cur.fetchone() is not None

if exists:
    set_parts = ["description=?", "category=?", "severity=?", "is_active=1", "params=?"]
    values = [rule["description"], rule["category"], rule["severity"], rule["params"]]
    if has_updated_at:
        set_parts.append("updated_at=?")
        values.append(now)
    values.append(rule["name"])
    sql = f"UPDATE rules SET {', '.join(set_parts)} WHERE name=?"
    cur.execute(sql, values)
    print("Updated existing 'required_headers' rule.")
else:
    cols_list = ["code","name","description","category","severity","is_active","params"]
    vals_list = ["?","?","?","?","?","1","?"]
    values = [rule["code"], rule["name"], rule["description"], rule["category"], rule["severity"], rule["params"]]
    if has_created_at:
        cols_list.append("created_at"); vals_list.append("?"); values.append(now)
    if has_updated_at:
        cols_list.append("updated_at"); vals_list.append("?"); values.append(now)
    sql = f"INSERT INTO rules ({', '.join(cols_list)}) VALUES ({', '.join(vals_list)})"
    cur.execute(sql, values)
    print("Inserted new 'required_headers' rule.")

con.commit()

# Show result
cur.execute("SELECT code,name,category,severity,is_active,substr(params,1,40)||'...' FROM rules WHERE name=?", (rule["name"],))
print("Row:", cur.fetchone())
con.close()
