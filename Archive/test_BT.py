import myBT
bt = myBT.MyBT()
bt.send('hello')
r = bt.receive()
print(r)