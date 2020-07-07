import sys
import cv2
from skimage.measure import find_contours, points_in_poly, approximate_polygon
from skimage import io
from skimage import color
import matplotlib.pyplot as plt

lat = 51.581314
lng = -0.23119

url = "http://maps.googleapis.com/maps/api/staticmap?center=%s,%s&zoom=21&size=640x640&maptype=roadmap&style=visibility:off&style=feature:landscape.man_made|element:geometry.stroke|visibility:on|color:0xffffff|weight:1&key=AIzaSyD4XzpPLesutnm9k0ZVZ-OCugAVHmqe58c" % (
    lat, lng)

im = io.imread(url)

im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
ret, thresh = cv2.threshold(imgray, 127, 255, 0)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# im = cv2.drawContours(im, contours, -1, (0, 255, 0), 1)
# plt.imshow(im)
# plt.show()

imageSize = 640
min_distance = sys.maxsize
contour_ind = -1
for idx, contour in enumerate(contours):
    distance = cv2.pointPolygonTest(contour, (imageSize / 2, imageSize / 2), True)
    if distance > 0 and distance < min_distance:
        min_distance = distance
        contour_ind = idx
    # im = cv2.drawContours(im, [contours[idx]], -1, (0, 255, 0), 2)
    # plt.imshow(im)
    # plt.show()

if contour_ind > -1:
    im = cv2.drawContours(im, [contours[contour_ind]], -1, (0, 255, 0), 2)
    plt.imshow(im)
    plt.show()
else:
    print("contour not found")
