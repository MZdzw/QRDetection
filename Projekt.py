import cv2
import numpy as np
from pyzbar.pyzbar import decode
import math
import time

def line_equation(point1_x, point1_y, point2_x, point2_y):
    a=(point1_y-point2_y)/(point1_x-point2_x)
    b=-(point1_y-point2_y)/(point1_x-point2_x)*point1_x+point1_y
    return a, b 

def lines_intersection(a1, b1, a2, b2):
    x=(b1-b2)/(a2-a1)
    y=x*a1+b1
    return x, y

def pattern_on_diagonal(point1_x, point2_x, point1_y, point2_y, qr_code, a, b):             #point1_x, point2_y - x coordinate of two polygon's corner, which lay on the same diagonal line
    #print(diagonals[3,0])
    #print(diagonals[2,0])
    once = False
    colors = np.zeros((1,5))
    proportions = np.zeros((1, 5))   #contains number of pixel of the same color in which perform in a row
    coordinates = np.zeros((1,2), dtype=int)
    present = 0
    previous=0
    which = 0
    leng = int(math.sqrt((point1_x-point2_x)**2+(point1_y-point2_y)**2))
    current_x = int(round(point2_x, 0))
    current_x_prev = current_x - 1
    for i in range(0, leng+5):
        #actual pixel position in image (on diagonal)
        if point1_x-point2_x > 0:
        #   (point2_x)---------(1)       
        #   |x                  |
        #   |      x            |   
        #   |            x      |
        #   |                  x|
        #   (0)---------(point1_x)
        # 
            if once ==True:
                current_x_prev = current_x
            current_x = int(round(point2_x + (point1_x-point2_x)/leng*i, 0))
            current_y = int(round(a*current_x + b, 0))
            #current_x = int(round(point2_x + i, 0))
            #print(current_x)
        else:
        #   (3)---------(point2_x)           (point1_x)----------(3)          (0)----------(point2_x) 
        #   |                  x|    or      | x                   |    or    |                    x|
        #   |             x     |            |       x             |          |              x      |
        #   |       x           |            |             x       |          |        x            |
        #   |  x                |            |                   x |          | x                   |
        #   (point1_x)---------(2)           (2)----------(point2_x)          (point1_x)----------(1) 
            if once ==True:
                current_x_prev = current_x
            current_x = int(round(point1_x + (point2_x-point1_x)/leng*i, 0))
            current_y = int(round(a*current_x + b, 0))
            print(current_x)
            #current_x = int(round(point1_x + i, 0))

        #only one execution of below commands (for previous and present pixel in loop)
        if once == False:
            once = True
            present = qr_code[current_y, current_x]      #contain value (0-255) of present pixel
        
        if current_x != current_x_prev:                 #check if it isn't the same x coordinate as in previous step loop
            #print(current_x)
            previous = present
            present = qr_code[current_y, current_x]
            if present != previous:     #change of color
                proportions_div = proportions/proportions[0,0]                                                  #divide proportions vector by the first element
                proportions_div_bool = np.all((proportions_div > 0.7) & (proportions_div < 1.5), axis=0)        #check if elements in vector fulfill proprtions of qrcode pattern 1 (with deviation)
                proportions_div_bool_2 = np.all((proportions_div > 2.3) & (proportions_div < 3.5), axis=0)      # check if element in vector fulfill proprtions of qrcode pattern 3 (with deviation) 
                proportions_div_bool[2] =proportions_div_bool_2[2]                                              #assign middle element to first boolean vector
                if np.all(proportions_div_bool) and colors[0,0] == 0:                                           #corner is detected!!!!
                    print('Detected corner')
                    print(proportions_div_bool)
                    offset_x = int(round(np.sum(proportions[0, 2:])-proportions[0,2]/2,0))
                    offset_y = int(round(a*offset_x, 0))
                    #coordinates = (current_x-offset_x, current_y-offset_y)
                    #cv2.circle(qr_code, coordinates, radius=5, color=125, thickness=5)
                    coordinates = np.append(coordinates, [[current_x-offset_x, current_y-offset_y]], axis=0)
                    print(coordinates)

                #przesuniecie ostatnich pieciu sekwencji dodac warunek jesli bedzie sprawdzana juz 6 sekwencja (5)
                which+=1  
                if which > 4:
                    proportions[0,0] = proportions[0, 1]
                    colors[0,0] = colors[0,1]
                    proportions[0,1] = proportions[0,2]
                    colors[0,1] = colors[0,2]
                    proportions[0,2] = proportions[0,3]
                    colors[0,2] = colors[0,3]
                    proportions[0,3] = proportions[0,4]
                    colors[0,3] = colors[0,4]
                    proportions[0,4] = 1
                    colors[0,4] = qr_code[current_y, current_x]
                else:
                    proportions[0,which]+=1
                    colors[0,which] = qr_code[current_y,current_x]
                    

            else:                               #nie nastapiła zmiana koloru
                if which > 4:
                    proportions[0, 4] += 1             #zwiekszaj o jeden 
                    colors[0,4] = qr_code[current_y, current_x]
                else:
                    proportions[0, which] += 1 
                    colors[0,which] = qr_code[current_y, current_x]
    return coordinates



def decoder(image):
    gray_img = cv2.cvtColor(image,0)
    barcode = decode(gray_img)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    for obj in barcode:
        points = obj.polygon
        (x,y,w,h) = obj.rect
        pts = np.array(points, np.int32)
        #vertex of diagonals
        #   for example
        #   (3)---------(2)                     (0)-----------(3)
        #   |             |          or         |               |
        #   |             |                     |               |
        #   |             |                     |               |
        #   |             |                     |               |
        #   (0)---------(1)                     (1)-----------(2)

        diagonals = pts[0::2].reshape((-1, 2))
        diagonals = np.append(diagonals, pts[1::2].reshape((-1, 2)), axis=0)
        #pts = np.append(pts, diagonals, axis=0)
        pts = pts.reshape((-1, 1, 2))
        #print(pts)
        cv2.polylines(image, [pts], True, (0, 0, 255), 3)
        
        #diagonals calculation (lines equation)
        #y=ax+b
        #   (3)---------(1)                     (0)----------(3)
        #   |  x       x  |          or         |  x        x  |
        #   |     x x     |                     |     x  x     |
        #   |     x x     |                     |     x  x     |
        #   |  x       x  |                     |  x        x  |
        #   (0)---------(2)                     (2)----------(1)
        a1, b1 = line_equation(diagonals[0, 0], diagonals[0, 1], diagonals[1, 0], diagonals[1, 1])
        a2, b2 = line_equation(diagonals[2, 0], diagonals[2, 1], diagonals[3, 0], diagonals[3, 1])
        #intersection point of diagonals (the center of polygon)
        x_intersection, y_intersection = lines_intersection(a1, b1, a2, b2)
        #center display
        cv2.circle(image, (int(np.round(x_intersection,0)),int(np.round(y_intersection,0))), radius=5, color=(0, 255, 0), thickness=3)

        #Binarization of image
        ret2,gray = cv2.threshold(gray,150,255,cv2.THRESH_BINARY)
        #two loops through diagonals
        cord1 = pattern_on_diagonal(diagonals[0,0], diagonals[1,0],diagonals[0,1], diagonals[1,1], gray, a1, b1)
        cord2 = pattern_on_diagonal(diagonals[2,0], diagonals[3,0],diagonals[2,1],diagonals[3,1], gray, a2, b2)
        #show the binarized image
        if(cord1.shape[0] != 0):
            for i in range(1, cord1.shape[0]):
                cv2.circle(frame, (cord1[i, 0], cord1[i, 1]), radius=5, color=125, thickness=5)
        if(cord2.shape[0] != 0):
            for i in range(1, cord2.shape[0]):
                cv2.circle(frame, (cord2[i, 0], cord2[i, 1]), radius=5, color=125, thickness=5)

        cv2.imshow('Obrazek',gray)


        barcodeData = obj.data.decode("utf-8")
        barcodeType = obj.type
        string = "Data " + str(barcodeData) + " | Type " + str(barcodeType)

        cv2.putText(frame, string, (x,y), cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,0,0), 2)
    

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if (ret == True):
        decoder(frame)
        cv2.imshow('Image', frame)
        code = cv2.waitKey(1)

        if code == ord('q'):
            break
    else:
        break