from django.shortcuts import render
from uuid import uuid4
from django.http import HttpResponse
#from PIL import Image, ImageChops
import qrcode

def index(request):
  return render(request, 'qr/index.html')


# generates UUIDs for the QR codes, the number is in the "count" parameter
def codes(request):
	uuids = []
	count = int(request.GET.get('count'))
	for i in range(count):
		uuids.append("dande.li/ics/" + str(uuid4()))
	return HttpResponse('\n'.join(uuids))


# def images(request):
#   ROWS = int(request.GET.get('rows'))
#   COLS = int(request.GET.get('cols'))
  
#   # all sizes are in pixels
#   QR_SIZE = 120
#   STICKER_SIZE = 150     
#   X_OFFSET = 188
#   Y_OFFSET = 9
#   X_SPACING = 111
#   Y_SPACING = 150

#   count = ROWS * COLS
#   width = (X_OFFSET * 2) + (STICKER_SIZE * ROWS) + (X_SPACING * (ROWS-1))
#   height = (Y_OFFSET * 2) + (STICKER_SIZE * COLS) + (Y_SPACING * (COLS-1))
#   diff = (STICKER_SIZE - QR_SIZE)/2

#   img = Image.new("RGB", (width, height), "white")

#   for i in range(count):
#     code_text = "dande/" + str(uuid4()).translate(None, '-')
#     qr = qrcode.QRCode(
#       version=None,
#       error_correction=qrcode.constants.ERROR_CORRECT_L,
#       box_size=10,
#       border=0,
#     )
#     qr.add_data(code_text)
#     qr.make(fit=True)
#     qr_img = qr.make_image().resize((QR_SIZE, QR_SIZE))

#     x = i/COLS
#     y = i % COLS 
#     x_pos = X_OFFSET + x*STICKER_SIZE + x*X_SPACING + diff
#     y_pos = Y_OFFSET + y*STICKER_SIZE + y*Y_SPACING + diff
#     img.paste(qr_img, (x_pos, y_pos, x_pos + QR_SIZE, y_pos + QR_SIZE))

#   brown = Image.new("RGB", (width, height), "#9f8958")
#   final = ImageChops.lighter(brown, img)
#   response = HttpResponse(content_type="image/png")
#   final.save(response, "PNG")
#   return response


