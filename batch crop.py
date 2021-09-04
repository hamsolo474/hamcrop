from PIL import Image
import argparse

img = ""

#cres = [None,None]


def get_res(file):
    with Image.open(file) as img:
        return (img.width, img.height)

def custom_resolution_crop(cres, rres):
    cres = [int(i) for i in cres.split('x')]
    #rres = (3960, 4096)
    crops = []
    x,y = cres
    while True:
        crops.append((x-cres[0],y-cres[1],x,y))
        if x < rres[0]:
            x+=cres[0]
        elif x > rres[0]:
            x = cres[0]
            y+=cres[1]
        if y > rres[1]:
            break
    return crops

def divided_resolution_crop(divs,rres):
    divs=[int(i) for i in divs.split('/')]
    cres = (int(rres[0]/divs[0]),int(rres[1]/divs[1]))
    crops = []
    for y in range(divs[1]):
        for x in range(divs[0]):
            crops.append((cres[0]*x,     cres[1]*y ,
                          cres[0]*(x+1), cres[1]*(y+1)))
    return crops

def crop_list(name, crops):
    with Image.open(name) as im:
        for count, piece in enumerate(crops):
            fname = ''.join([name.split('.')[0],' ', str(count),'.jpg'])
            print(fname, piece)
            im.crop(piece).save(fname)
    
cmdline = argparse.ArgumentParser(description="Batch crop")
cmdline.add_argument('--divisions','-d', action="store", dest='divs')
cmdline.add_argument('--custom-resolution','-c', action="store", dest='cres')
cmdline.add_argument('file', action="store")
args = cmdline.parse_args()

rres = get_res(args.file)

if args.divs:
    crops = divided_resolution_crop(args.divs, rres)
elif args.cres:
    crops = custom_resolution_crop(args.cres, rres)
crop_list(args.file, crops)
