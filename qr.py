import qrcode

data = "streets.jpg"

qr = qrcode.make(data)

qr.save("streets.png")

