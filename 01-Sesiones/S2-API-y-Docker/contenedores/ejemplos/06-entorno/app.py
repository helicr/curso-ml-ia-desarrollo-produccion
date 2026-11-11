import os

print("saludo:", os.environ.get("SALUDO", "(sin definir)"))
print("token presente:", "TOKEN_API" in os.environ)
