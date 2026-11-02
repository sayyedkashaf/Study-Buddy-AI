with open('app.py','rb') as f:
    data = f.read()
lines = data.split(b'\n')
for i,l in enumerate(lines[:10]):
    print(i, repr(l))
