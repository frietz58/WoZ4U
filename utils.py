from PIL import Image
import io


def is_url(path):
    # determines whether a path is a url or not
    if "http" in path:
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

