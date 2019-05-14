from __future__ import print_function
import cv2 as cv
import numpy as np
import random as rng
import os
import csv
from PIL import Image

#This script
#1) Gets images from a folder (segmentation or id maps)
#2) Generates bounding boxes of the form x1, y1, x2, y2 for upright bounding boxes (bottem left coordinate and top right coordinate in pixels
#3) Saves data to csv file
#4) Displays the sources and bounding box images (optional below)
#5) Saves the bounding box images to file (optional below)

##limitations:
#only segments one colour at a time, but could be adapted if you want
#if instances of a colour/class in a segmentation image are too close together such that their bounding boxes would overlap, then only one of them is detected/recorded

#CHANGE PATHS TO MAKE SENSE FOR YOUR PROJECT
segs_path = 'C:\\Users\\Ben\\Pictures\\'
box_images_path = 'C:\\Users\\Ben\\Pictures\\boxes\\'

#IMAGE FILE EXTENSION
seg_file_extension = ".png"

#CHANGE TO COLOUR YOU WANT TO SEGMENT
lower_hsv = np.array([-5, 50, 50])
upper_hsv = np.array([5, 255, 255])

#OUTPUT OPTIONS FOR VISUALISATION OF BOUNDING BOXES
show_output = True
save_bounding_box_images = True


def get_iou(bb1, bb2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.

    Parameters
    ----------
    bb1 : dict
        Keys: {'x1', 'x2', 'y1', 'y2'}
        The (x1, y1) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner
    bb2 : dict
        Keys: {'x1', 'x2', 'y1', 'y2'}
        The (x, y) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner

    Returns
    -------
    float
        in [0, 1]
    """
    assert bb1['x1'] < bb1['x2']
    assert bb1['y1'] < bb1['y2']
    assert bb2['x1'] < bb2['x2']
    assert bb2['y1'] < bb2['y2']

    # determine the coordinates of the intersection rectangle
    x_left = max(bb1['x1'], bb2['x1'])
    y_top = max(bb1['y1'], bb2['y1'])
    x_right = min(bb1['x2'], bb2['x2'])
    y_bottom = min(bb1['y2'], bb2['y2'])

    if x_right < x_left or y_bottom < y_top:
        #print("not")

        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    return intersection_area

with open('testAnnotation.csv', mode='w', newline='') as test:
    test_writer = csv.writer(test, delimiter=',', escapechar=' ', quoting=csv.QUOTE_NONE)

    header = 'filename,x1,y1,x2,y2'
    test_writer.writerow([header])

    segs_folder = os.listdir(segs_path)

    segs_list = []
    segs_pathlist = []



    for seg in segs_folder:
        if seg.endswith(seg_file_extension):
            filepath = segs_path+seg
            segs_list.append(filepath)
            segs_pathlist.append(seg)
            #print(filepath)

        rng.seed(12345)

    for index, seg_img in enumerate(segs_list):
        src = cv.imread(seg_img)


        if src is None:
            print('Could not open or find the image')
            exit(0)

        hsv = cv.cvtColor(src, cv.COLOR_BGR2HSV)



        src_gray = cv.inRange(hsv, lower_hsv, upper_hsv)
        src_gray = cv.blur(src_gray, (4,4))

        res = cv.bitwise_and(src, src, mask=src_gray)
        #cv.imshow('frame', src)
        #cv.imshow('mask', mask)
        #cv.imshow('res', res)

        threshold = 100

        canny_output = cv.Canny(src_gray, threshold, threshold * 2)

        contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        contours_poly = [None] * len(contours)
        boundRect = [None] * len(contours)
        #centers = [None] * len(contours)
        #radius = [None] * len(contours)
        for i, c in enumerate(contours):
            contours_poly[i] = cv.approxPolyDP(c, 3, True)
            boundRect[i] = cv.boundingRect(contours_poly[i])
            #centers[i], radius[i] = cv.minEnclosingCircle(contours_poly[i])

        drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

        boundingboxes = []

        #generate bounding boxes
        for i in range(len(contours)):
            if boundRect[i][2] > 1 and boundRect[i][3] > 1:  # i%2 == 1:
                color = (rng.randint(0, 256), rng.randint(0, 256), rng.randint(0, 256))

                x1 = int(boundRect[i][0])
                y1 = int(boundRect[i][1])
                x2 = int(boundRect[i][0] + boundRect[i][2])
                y2 = int(boundRect[i][1] + boundRect[i][3])

                box = {"x1":x1,"x2":x2,"y1":y1,"y2":y2}

                #test if box overlaps any previous box
                test = True;
                for _box in boundingboxes:
                    intersection = get_iou(box,_box)
                    if intersection != 0.0:
                        test = False

                if test:
                    cv.rectangle(drawing, (x1, y1), (x2, y2), color, 2)
                    row = segs_pathlist[index], x1, y1, x2, y2
                    test_writer.writerow(row)
                    boundingboxes.append(box)




        #save bounding box images to file
        if save_bounding_box_images:
            box_img = Image.fromarray(drawing)
            box_img.save(box_images_path + str("%04d" % (index + 1)) + '_box' + ".png", "PNG")

        #show bounding box images, and source images
        if show_output:
            cv.imshow('Contours' + str(index), drawing)
            source_window = 'Source' + str(index)
            cv.namedWindow(source_window)
            cv.imshow(source_window, src)

    cv.waitKey()

