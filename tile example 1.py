from PIL import Image

src_im = Image.open("example.jpg")
angle = 45
#size = 100, 100


im = src_im.convert('RGBA')
rot = im.rotate( angle, expand=1 )#.resize(size)
dst_im = Image.new("RGBA", (rot.width,rot.height), "blue" )
dst_im.paste( rot, (0, 0), rot )
dst_im.show()