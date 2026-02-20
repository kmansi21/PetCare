db.createCollection("users");
db.users.createIndex({ email: 1 }, { unique: true })