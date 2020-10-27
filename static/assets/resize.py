import glob
import cv2


for i in glob.glob('g*.jpg'):
    img = cv2.imread(i, 1)
    resized_img = cv2.resize(img, (1920, 1080))
    cv2.imwrite('resized_{}'.format(i), resized_img)
    cv2.imshow('resized image', resized_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
