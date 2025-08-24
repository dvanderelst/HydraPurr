import myBT
bt = myBT.myBT()
bt.send('hello')
r = bt.receive()
print(r)