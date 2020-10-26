from PIL import Image
import io
import wave
import os


def is_video(path):
    ext = path.split(".")[-1]
    print(ext)
    if ext in ["mp4", "m4v", "mkv", "webm", "mov", "avi", "wmv", "mpg", "flv"]:
        return True
    else:
        return False


def is_image(path):
    ext = path.split(".")[-1]
    if ext.lower() in ["jpeg", "jpg", "gif", "bmp", "png", "ppm", "pgm", "webp", "svg"]:
        return True
    else:
        return False


def is_txt_file(path):
    ext = path.split(".")[-1]
    return True if ext == "txt" else False


def is_external_path(path):
    if "http" == path[:4]:
        return True
    else:
        return False


def alImage_to_PIL(alImg):
    """
    Converts a ALImage from the naoqi API ALVideoDeviceProxy::getImageRemote.
    :param alImg: The ALimage object as returned from the API.
    :return: A Pillow image.
    """
    im_w = alImg[0]
    im_h = alImg[1]
    im_arr = alImg[6]

    im_str = str(bytearray(im_arr))
    pil_img = Image.frombytes("RGB", (im_w, im_h), im_str)

    return pil_img


def PIL_to_JPEG_BYTEARRAY(pil_img):
    """
    Converts a Pillow image to a JPEG bytearray
    :param pil_img: The pillow image object
    :return: TThe jpeg bytearray
    """
    imgByteArr = io.BytesIO()
    pil_img.save(imgByteArr, format="jpeg")
    jpeg_bytes = imgByteArr.getvalue()

    return jpeg_bytes


def rawToWav(filename):
    """
    Waves a raw audio signal as physical .wav file
    """
    rawfile = filename + ".raw"
    if not os.path.isfile(rawfile):
        return

    outfile = wave.open(filename + ".wav", "wb")
    outfile.setframerate(48000)
    outfile.setnchannels(1)
    outfile.setsampwidth(2)

    f = open(rawfile, "rb")
    sample = f.read(4096)
    print 'writing file: ' + filename + '.wav'

    while sample != "":
        outfile.writeframes(sample)
        sample = f.read(4096)

    outfile.close()

    os.remove(rawfile)


