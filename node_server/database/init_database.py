from helper import Database

table_transaction_sql = '''
CREATE TABLE IF NOT EXISTS "transactions" (
	"id"	INTEGER,
	"type"	TEXT NOT NULL,
	"user_name"	TEXT NOT NULL,
	"IP"	TEXT NOT NULL,
	"datetime"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);'''

table_content_sql = '''
CREATE TABLE IF NOT EXISTS "content" (
	"text"	TEXT,
	"name"	TEXT,
	"email"	TEXT,
	"id_transaction"	INTEGER NOT NULL,
	FOREIGN KEY("id_transaction") REFERENCES "transactions"("id")
);
'''

database = Database()

database.execute(table_transaction_sql)

database.execute(table_content_sql)

database.close_connection()