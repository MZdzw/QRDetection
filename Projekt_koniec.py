import cv2
import numpy as np
from pyzbar.pyzbar import decode
import math
import time



def line_equation(point1_x, point1_y, point2_x, point2_y):
    if abs(point1_x - point2_x) < 1:                  #umownie, prosta nigdy nie bedzie miec takich wspolczynnikow na 
        a = 0
        b = 0
        return a, b
    a = (point1_y - point2_y) / (point1_x - point2_x)
    b = - (point1_y - point2_y) / (point1_x - point2_x) * point1_x + point1_y
    return a, b

def lines_intersection(a1, b1, a2, b2):
    if a1 == 0 and b1 == 0:
        x = 0
        y = 0
        return x, y 
    x = (b1 - b2) / (a2 - a1)
    y = x * a1 + b1
    return x, y

def pattern_on_diagonal_reversed_coordinates(point1_x, point2_x, point1_y, point2_y, qr_code, c, d):             #point1_x, point2_x - x coordinate of two polygon's corner, which lay on the same diagonal line
    #print(diagonals[3,0])
    #print(diagonals[2,0])
    once = False
    colors = np.zeros((1, 5))
    proportions = np.zeros((1, 5))   #contains number of pixel of the same color in which perform in a row
    coordinates = np.zeros((1, 2), dtype = int)
    present = 0
    previous = 0
    which = 0
    leng = int(math.sqrt((point1_x-point2_x)**2+(point1_y-point2_y)**2))
    current_x = int(round(point2_x, 0))
    current_x_prev = current_x - 1
    for i in range(0, leng):
        #actual pixel position in image (on diagonal)
        if point1_x - point2_x > 0:
        #   (point2_x)---------(1)       
        #   |x                  |
        #   |      x            |   
        #   |            x      |
        #   |                  x|
        #   (0)---------(point1_x)
            if once ==True:
                current_x_prev = current_x    
            current_x = int(round(point2_x + (point1_x-point2_x)/leng*i, 0))
            current_y = int(round(c*current_x - d, 0))
            #print(current_y)
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
            current_y = int(round(c*current_x - d, 0))

        # if point1_y == point2_y: 
        #     print(current_x, current_y)

        #only one execution of below commands (for previous and present pixel in loop)
        if once == False:
            once = True
            present = qr_code[current_x, current_y]      #contain value (0-255) of present pixel
        
        if current_x_prev != current_x:
            previous = present
            present = qr_code[current_x, current_y]
            #print(current_x)
            if present != previous or i == leng-1:     #change of color
                proportions_div = proportions / proportions[0,0]                                                  #divide proportions vector by the first element
                proportions_div_bool = np.all((proportions_div > 0.7) & (proportions_div < 1.5), axis = 0)        #check if elements in vector fulfill proprtions of qrcode pattern 1 (with deviation)
                proportions_div_bool_2 = np.all((proportions_div > 2.3) & (proportions_div < 3.5), axis = 0)      # check if element in vector fulfill proprtions of qrcode pattern 3 (with deviation) 
                proportions_div_bool[2] = proportions_div_bool_2[2]                                              #assign middle element to first boolean vector
                if np.all(proportions_div_bool) and colors[0, 0] == 0:                                           #corner is detected!!!!
                    #print('Detected corner')
                    #print(proportions_div_bool)
                    offset_x = int(round(np.sum(proportions[0, 2:]) - proportions[0,2 ] / 2,0))
                    #offset_y = int(round(np.sum(proportions[0, 2:]) - proportions[0,2 ] / 2,0))
                    offset_y = int(round(c*offset_x, 0))
                    #print(proportions[0])
                    #print(current_y, current_x)
                     #coordinates = (current_x-offset_x, current_y-offset_y)
                     #cv2.circle(qr_code, coordinates, radius=5, color=125, thickness=5)
                    coordinates = np.append(coordinates, [[current_y-offset_y, current_x-offset_x]], axis = 0)
                     #print(coordinates)

                #przesuniecie ostatnich pieciu sekwencji dodac warunek jesli bedzie sprawdzana juz 6 sekwencja (5)
                which += 1  
                if which > 4:
                    proportions[0, 0] = proportions[0, 1]
                    colors[0, 0] = colors[0, 1]
                    proportions[0, 1] = proportions[0, 2]
                    colors[0, 1] = colors[0, 2]
                    proportions[0, 2] = proportions[0, 3]
                    colors[0, 2] = colors[0, 3]
                    proportions[0, 3] = proportions[0, 4]
                    colors[0, 3] = colors[0, 4]
                    proportions[0, 4] = 1
                    colors[0, 4] = qr_code[current_x, current_y]
                else:
                    proportions[0, which] += 1
                    colors[0, which] = qr_code[current_x, current_y]
                    

            else:                               #nie nastapiła zmiana koloru
                if which > 4:
                    proportions[0, 4] += 1             #zwiekszaj o jeden 
                    colors[0, 4] = qr_code[current_x, current_y]
                else:
                    proportions[0, which] += 1 
                    colors[0, which] = qr_code[current_x, current_y]
    return coordinates

def pattern_on_diagonal(point1_x, point2_x, point1_y, point2_y, qr_code, a, b):             #point1_x, point2_x - x coordinate of two polygon's corner, which lay on the same diagonal line
    #print(diagonals[3,0])
    #print(diagonals[2,0])
    once = False
    colors = np.zeros((1, 5))
    proportions = np.zeros((1, 5))   #contains number of pixel of the same color in which perform in a row
    coordinates = np.zeros((1, 2), dtype = int)
    present = 0
    previous = 0
    which = 0
    leng = abs(point1_x-point2_x)
    current_x = int(round(point2_x, 0))
    current_x_prev = current_x - 1
    for i in range(0, leng+1):
        #actual pixel position in image (on diagonal)
        if point1_x - point2_x > 0:
        #   (point2_x)---------(1)       
        #   |x                  |
        #   |      x            |   
        #   |            x      |
        #   |                  x|
        #   (0)---------(point1_x)   
            current_x = int(round(point2_x + i, 0))
            current_y = int(round(a*current_x + b, 0))
            #print(current_x)
        else:
        #   (3)---------(point2_x)           (point1_x)----------(3)          (0)----------(point2_x) 
        #   |                  x|    or      | x                   |    or    |                    x|
        #   |             x     |            |       x             |          |              x      |
        #   |       x           |            |             x       |          |        x            |
        #   |  x                |            |                   x |          | x                   |
        #   (point1_x)---------(2)           (2)----------(point2_x)          (point1_x)----------(1) 
            current_x = int(round(point1_x + i, 0))
            current_y = int(round(a*current_x + b, 0))
        #print(current_x, current_y)

        #only one execution of below commands (for previous and present pixel in loop)
        if once == False:
            once = True
            present = qr_code[current_y, current_x]      #contain value (0-255) of present pixel

        previous = present
        present = qr_code[current_y, current_x]
        #print(current_x)
        if present != previous or i == leng:     #change of color or if it is last step in for loop
            proportions_div = proportions / proportions[0,0]                                                  #divide proportions vector by the first element
            #print(proportions_div)
            proportions_div_bool = np.all((proportions_div > 0.7) & (proportions_div < 1.5), axis = 0)        #check if elements in vector fulfill proprtions of qrcode pattern 1 (with deviation)
            proportions_div_bool_2 = np.all((proportions_div > 2.3) & (proportions_div < 3.5), axis = 0)      # check if element in vector fulfill proprtions of qrcode pattern 3 (with deviation) 
            proportions_div_bool[2] = proportions_div_bool_2[2]                                               #assign middle element to first boolean vector
            if np.all(proportions_div_bool) and colors[0, 0] == 0:                                            #corner is detected!!!!
                #print('Detected corner')
                #print(proportions_div)
                offset_x = int(round(np.sum(proportions[0, 2:]) - proportions[0,2 ] / 2,0))
                offset_y = int(round(a*offset_x, 0))
                #coordinates = (current_x-offset_x, current_y-offset_y)
                #cv2.circle(qr_code, coordinates, radius=5, color=125, thickness=5)
                coordinates = np.append(coordinates, [[current_x - offset_x, current_y - offset_y]], axis = 0)
                #print(coordinates)

            #przesuniecie ostatnich pieciu sekwencji dodac warunek jesli bedzie sprawdzana juz 6 sekwencja (5)
            which += 1  
            if which > 4:
                proportions[0, 0] = proportions[0, 1]
                colors[0, 0] = colors[0, 1]
                proportions[0, 1] = proportions[0, 2]
                colors[0, 1] = colors[0, 2]
                proportions[0, 2] = proportions[0, 3]
                colors[0, 2] = colors[0, 3]
                proportions[0, 3] = proportions[0, 4]
                colors[0, 3] = colors[0, 4]
                proportions[0, 4] = 1
                colors[0, 4] = qr_code[current_y, current_x]
            else:
                proportions[0, which] += 1
                colors[0, which] = qr_code[current_y, current_x]

        else:                               #nie nastapiła zmiana koloru
            if which > 4:
                proportions[0, 4] += 1             #zwiekszaj o jeden 
                colors[0, 4] = qr_code[current_y, current_x]
            else:
                proportions[0, which] += 1 
                colors[0, which] = qr_code[current_y, current_x]
    return coordinates

def decoder(image):
    gray_img = cv2.cvtColor(image,0)
    code = decode(gray_img)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    for obj in code:
        if obj.type != 'QRCODE':
            cv2.putText(frame, 'This isn\'t QRCODE!', (10, 22), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
            continue
        #print(obj)
        points = obj.polygon
        (x, y, w, h) = obj.rect
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
        diagonals = np.append(diagonals, pts[1::2].reshape((-1, 2)), axis = 0)
        #pts = np.append(pts, diagonals, axis=0)
        pts = pts.reshape((-1, 1, 2))
        #print(pts)
        cv2.polylines(frame, [pts], True, (0, 0, 255), 4)
        
        #diagonals calculation (lines equation)
        #y=ax+b
        #   (3)---------(1)                     (0)----------(3)
        #   |  x       x  |          or         |  x        x  |
        #   |     x x     |                     |     x  x     |
        #   |     x x     |                     |     x  x     |
        #   |  x       x  |                     |  x        x  |
        #   (0)---------(2)                     (2)----------(1)

        
        #Binarization of image
        ret2, gray = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        cv2.imshow('binarization', gray)
        #print(diagonals[2,0], diagonals[3,0])
        if diagonals[0,0] == diagonals[1,0]:        #punkty na przekatnej leza na pionowej linii
            x_intersection = diagonals[0,0]
            y_intersection = diagonals[2,1]-(diagonals[2,1]-diagonals[3,1])/2
            cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
            cord2 = pattern_on_diagonal(diagonals[2, 0], diagonals[3, 0], diagonals[2, 1], diagonals[3, 1], gray, a2, b2)
            print('Jestem pod wierzcholkiem')
        #obsługa patternow
        elif diagonals[2,0] == diagonals[3,0]:              #w sumie 2-3 to zawsze te wierzcholki pod soba
            x_intersection = diagonals[2,0]
            y_intersection = diagonals[2,1]-(diagonals[2,1]-diagonals[3,1])/2
            print('Jestem pod wierzcholkiem')
            #obsługa patternow (modyfikacja rownan linii)
            a1, b1 = line_equation(diagonals[0, 0], diagonals[0, 1], diagonals[1, 0], diagonals[1, 1])
            cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
            c2 = 0
            d2 = diagonals[2,0]
            cord2 = pattern_on_diagonal_reversed_coordinates(diagonals[2, 1], diagonals[3, 1], diagonals[2, 0], diagonals[3, 0], gray, c2, -d2)
            print('Wspolrzedne y wierzcholkow', diagonals[3,1], diagonals[2,1])
            print('Wspolrzedne y wierzcholkow', diagonals[3,0], diagonals[2,0])
        else:
            a1, b1 = line_equation(diagonals[0, 0], diagonals[0, 1], diagonals[1, 0], diagonals[1, 1])
            a2, b2 = line_equation(diagonals[2, 0], diagonals[2, 1], diagonals[3, 0], diagonals[3, 1])
            c1=1/a1
            d1=b1/a1
            c2=1/a2
            d2=b2/a2
            #print(a1, a2)
            if abs(a1) > 1 and abs(a2) < 1:                 #przekatna jest powyżej 45st
                y_intersection = int((-a2*d1+b2)/(1-a2*c1))
                x_intersection = int(c1*y_intersection-d1)
                #cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
                #cord2 = pattern_on_diagonal(diagonals[2, 0], diagonals[3, 0], diagonals[2, 1], diagonals[3, 1], gray, a2, b2)
                #print('pierwszy warunek')
                #obsługa patternow
                cord1 = pattern_on_diagonal_reversed_coordinates(diagonals[0, 1], diagonals[1, 1], diagonals[0, 0], diagonals[0, 1], gray, c1, d1)
                cord2 = pattern_on_diagonal(diagonals[2, 0], diagonals[3, 0], diagonals[2, 1], diagonals[3, 1], gray, a2, b2)
            elif abs(a1) < 1 and abs(a2) > 1:
                c2=1/a2
                d2=b2/a2
                y_intersection = int((-a1*d2+b1)/(1-a1*c2))
                x_intersection = int(c2*y_intersection-d2)
                #print('drugi warunek')
                #print(a1)
                #print(a2)

                #obsługa patternow
                cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
                cord2 = pattern_on_diagonal_reversed_coordinates(diagonals[2, 1], diagonals[3, 1], diagonals[2, 0], diagonals[3, 0], gray, c2, d2)
            elif abs(a1) > 1 and abs(a2) > 1:               #dwa wspolczynniki wieksze
                x_intersection, y_intersection = lines_intersection(a1, b1, a2, b2)
                cord1 = pattern_on_diagonal_reversed_coordinates(diagonals[0, 1], diagonals[1, 1], diagonals[0, 0], diagonals[0, 1], gray, c1, d1)
                cord2 = pattern_on_diagonal_reversed_coordinates(diagonals[2, 1], diagonals[3, 1], diagonals[2, 0], diagonals[3, 0], gray, c2, d2)
                #obsluga patternow
            else:                                           #dwa wspolczynniki mniejsze
                x_intersection, y_intersection = lines_intersection(a1, b1, a2, b2)
                cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
                cord2 = pattern_on_diagonal(diagonals[2, 0], diagonals[3, 0], diagonals[2, 1], diagonals[3, 1], gray, a2, b2)
                #obsługa patternow 

            #narazie defaultowo tak samo niezaleznie od wspolczynnikow prostej
            # cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
            # cord2 = pattern_on_diagonal_reversed_coordinates(diagonals[2, 1], diagonals[3, 1], diagonals[2, 0], diagonals[3, 0], gray, c2, d2)
            #print(diagonals[2,0], diagonals[3,0])


        # a1, b1, success1 = line_equation(diagonals[0, 0], diagonals[0, 1], diagonals[1, 0], diagonals[1, 1])
        # print(a1)
        # a2, b2, success2 = line_equation(diagonals[2, 0], diagonals[2, 1], diagonals[3, 0], diagonals[3, 1])
        # print(a2)

        # if success1 == 0:
        #     x_intersection = diagonals[0, 0]
        #     y_intersection = diagonals[0, 1]-abs(diagonals[0, 1]-diagonals[1, 1])/2
        # if success2 == 0:
        #     x_intersection = diagonals[2, 0]
        #     y_intersection = diagonals[2, 1]-abs(diagonals[2, 1]-diagonals[3, 1])/2
        # #intersection point of diagonals (the center of polygon)
        # if success1 != 0 and success2 != 0:
        #     x_intersection, y_intersection = lines_intersection(a1, b1, a2, b2)
        

        #center display
        cv2.circle(frame, (int(np.round(x_intersection, 0)), int(np.round(y_intersection, 0))), radius = 3, color = (0, 0, 255), thickness = 5)

        # #Binarization of image
        # ret2, gray = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        # cv2.imshow('binarization', gray)
        #two loops through diagonals
        # cord1 = pattern_on_diagonal(diagonals[0, 0], diagonals[1, 0], diagonals[0, 1], diagonals[1, 1], gray, a1, b1)
        # cord2 = pattern_on_diagonal(diagonals[2, 0], diagonals[3, 0], diagonals[2, 1], diagonals[3, 1], gray, a2, b2)
        #show the binarized image
        numberOfCorner = 1
        if cord1.shape[0] != 0:
           for i in range(1, cord1.shape[0]):
                cv2.circle(frame, (cord1[i, 0], cord1[i, 1]), radius = 3, color = (240 - numberOfCorner * 70, 40 + numberOfCorner * 50, 240 - numberOfCorner * 70), thickness = 5)
                cv2.putText(frame, '(' + str(cord1[i, 0]) + ', ' + str(cord1[i, 1]) + ')', (112, 400 + numberOfCorner * 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (240 - numberOfCorner * 70, 40 + numberOfCorner * 50, 240 - numberOfCorner * 70), 1)
                numberOfCorner += 1
        
        if cord2.shape[0] != 0:
            for i in range(1, cord2.shape[0]):
                cv2.circle(frame, (cord2[i, 0], cord2[i, 1]), radius = 3, color = (240 - numberOfCorner * 70, 40 + numberOfCorner * 50, 240 - numberOfCorner * 70), thickness = 5)
                cv2.putText(frame, '(' + str(cord2[i, 0]) + ', ' + str(cord2[i, 1]) + ')', (112, 400 + numberOfCorner * 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (240 - numberOfCorner * 70, 40 + numberOfCorner * 50, 240 - numberOfCorner * 70), 1)
                numberOfCorner += 1

        cv2.putText(frame, 'Corner 1:', (12, 420), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (170, 90, 170), 1)
        cv2.putText(frame, 'Corner 2:', (12, 440), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (100, 140, 100), 1)
        cv2.putText(frame, 'Corner 3:', (12, 460), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (30, 190, 30), 1)

        text = obj.type + ' : ' + obj.data.decode('utf-8')
        center = 'Center: (' + str(int(x_intersection)) + ', ' + str(int(y_intersection)) + ')'

        cv2.putText(frame, text[0:50], (10, 22), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
        cv2.putText(frame, text[50:100], (10, 42), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
        cv2.putText(frame, text[100:150], (10, 62), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
        cv2.putText(frame, text[150:200], (10, 82), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
        cv2.putText(frame, text[200:250], (10, 102), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
        cv2.putText(frame, text[250:], (10, 122), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255, 0, 0), 1)
        cv2.putText(frame, center, (12, 400), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0, 0, 255), 1)

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if ret == True:
        decoder(frame)
        cv2.imshow('QR Scanner', frame)
        code = cv2.waitKey(10)

        if code == ord('q') or code == ord('Q'):
            break
    else:
        break