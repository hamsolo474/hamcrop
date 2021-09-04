from PIL import Image

#size = [int(i) for i in input("res:").split('x')]
fg = Image.open('example.jpg').convert('RGBA')
fg = fg.rotate(45, expand=True)
size = (fg.width, fg.height)
single = Image.open('tbs.png')
#wunit = int(size[0]/single.width)
#hunit = int(size[1]/single.height)
#print("size",wunit,'\nwunit',wunit,'\nhunit',hunit)
img    = Image.new('RGBA', size)

#for y in range(hunit+1):
#    # while img.height is less than size[1]
#    for x in range(wunit+1):
#        # the tuple is size not location
#        print('ran')
#        img.paste(single, (x*single.width, y*single.height))

img.show()
input("Press enter key to continue . . . .")

img.paste(fg,(0,0))
        
#img.save('tbs.png')
img.show()