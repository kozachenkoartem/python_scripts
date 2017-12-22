# -*- coding: utf-8 -*-
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    import sys
    import os
    import exifread
    from shutil import  copyfile
except ImportError as e:
    print (e)
    print("Try to install it with command 'pip install [module name]'")
    sys.exit(1)

max_size = 999999 # bytes
min_size = 3500   # pixels
compression_rate = 70

def resize_image(path, percentage):
    path = path.decode('cp1251')
    image = Image.open(path)
    if max(image.size[0], image.size[0]) < min_size :
        print(path + " no compress needed")
        return;
    old = path + ".backup"
    copyfile(path, old)
    exif = image.info['exif']
    old_w = image.size[0];
    old_h = image.size[1];
    try:
        newsize = (image.size[0] * percentage/100, image.size [1] * percentage/100 )
        image = image.resize(newsize, Image.ANTIALIAS)
        print("%s : %dx%d -> %dx%d " % (path, old_w, old_h, image.size[0], image.size[1]))
        image.save(path, exif = exif)
    except Exception, err:
        print(str(err))
        copyfile(old, path)
        os.remove(old)
        return
    os.remove(old)



def main():
    images_path = "."
    if len(sys.argv) >= 2 : images_path = sys.argv[1]
    for path, subdirs, files in os.walk(images_path):
        for filename in files:
            if filename.endswith(('.jpg', '.jpeg', '.JPG')):
                full_path = os.path.join(path, filename)
                if os.path.getsize(full_path) > max_size:
                    resize_image(full_path, compression_rate)
                else :
                    print(full_path + " no compress needed")


if __name__ == '__main__':
 main()