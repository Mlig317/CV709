import os
import cv2
import numpy as np
import csv
import time

interFolder = 'interim'

if not os.path.exists(interFolder):
    os.makedirs(interFolder)

fPath = "Set 1"
def magic(path,lastMid,lastAvg):

    iff = 0
    name, exten = os.path.splitext(os.path.basename(path))
    interPath = os.path.join(interFolder, name + '_B_'+'InterimResult' + str(iff) + exten)

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.GaussianBlur(img[0:400], (3, 3), 0)

    kernel = np.ones((5, 5), np.uint8) 
    kernel[3,3] = 10
    img = cv2.erode(img, kernel, iterations=1) 
    img = cv2.dilate(img, kernel, iterations=2) 
    img = cv2.erode(img, kernel, iterations=1)


    cut = cv2.Canny(img, 90, 190)

    white = np.where(cut[70] == 255)[0]
    
    
    if white.size == 2: #if there are only two white points
        
        weldgapCords = white.tolist()
        avg = (weldgapCords[-1] - weldgapCords[0]) / 2 #find the weld gap width
        if(avg >5): #if the width is greater than what the spec says it could be
            weld = closestWeld(white.tolist(), lastMid) #grab the white pixel coordinate closest to the last weld gap location
            if(weld < lastMid): #and add the last weld gap width to the current line that is closest to normal weld gap width. 
                 middlecord = int(weld + lastAvg)
            else:
                 middlecord = int(weld - lastAvg)
            avg = lastAvg 
        else:
            middlecord = int(weldgapCords[0] + avg) 
            
        
    elif(white.size >0): #if there are white pixels
        if white.size > 2: #and theres a pixel on the y = 70 that isn't the weld gap
            
            weldgapCords = weldGapPoints(white.tolist()) #return the two points that have the largest weld gap under 10 (10 being the max defined by the sheet)
            avg = (weldgapCords[-1] - weldgapCords[0]) / 2 #find the distance between the first and last pixel
            if(avg < 2): #if its really small
                weld = closestWeld(white.tolist(), lastMid) #basically find the pixel closest to the last weld gap middle
                if(weld < lastMid):#and add or subtract the spacing depending on if the point is to the left or right of the last weld gap
                 middlecord = int(weld + lastAvg)
                else:
                 middlecord = int(weld - lastAvg)
                avg = lastAvg #update the average
            
            else:
                middlecord = int(weldgapCords[0] + avg)#if the weld gap is normal sized
                print(f"{path}","HERE")

        else:
           
            if(white[0] < lastMid): #if there is only one pixel, repeat the above process of using past data
                
                middlecord = int(white[0] - lastAvg)
            else:
                middlecord = int(white[0] - lastAvg)
            avg = lastAvg    
    else:#no white pixels found, return the last values
        middlecord = lastMid
        avg = lastAvg
        
    print(f"{path}", middlecord)
    
    cv2.imwrite(interPath, img[0:400,middlecord-200:middlecord+200])#blurred image interim ROI
    iff = 1
    interPath = os.path.join(interFolder, name + '_B_'+'InterimResult' + str(iff) + exten)
    cv2.imwrite(interPath, cut[0:400,middlecord-200:middlecord+200])#canny image interim ROI

    finalPath = os.path.join(interFolder, name + '_A_'+'WeldGapPosition' + exten)
    cv2.line(img, (0, 75), (cut.shape[1], 70), (255, 0, 0), thickness=1) 
    cv2.line(img, (middlecord, 0), (middlecord, cut.shape[0]), (255, 0, 0), thickness=1)
    cv2.imwrite(finalPath, img[0:400,middlecord-200:middlecord+200])#final image cropped tho

    #cv2.line(cut, (0, 75), (cut.shape[1], 70), (255, 255, 255), thickness=1) #viewing stuff
    #cv2.line(cut, (middlecord, 0), (middlecord, cut.shape[0]), (255, 255, 255), thickness=1)
    #cv2.imshow(path, cut)
    #cv2.waitKey(500)  # Display each image for 1 second
    #cv2.destroyAllWindows()
    return middlecord,avg

def closestWeld(points, last): #helper function, returns the closest element within points to last
    closest = points[0]
    difference = 0
    minn = last
    for element in points:
        difference = abs(element - last)
        if difference < minn:
            minn = difference
            closest = element
    
    return closest
    
def allImage(): #helper function that executes all the images in the folder
    lastMid = 0;
    lastAvg = 0;
    conf = 0
    with open('WeldGapPositions.csv', mode='w',newline='') as file: #open the file
                scribbleman = csv.writer(file) #tell the scribble man to do his job
                scribbleman.writerow(['Image path','Coordinate','Confident?'])
                for filename in os.listdir(fPath):
                   if filename.endswith(("jpg")):
                      imgPath = os.path.join(fPath, filename)
                      lastMid,lastAvg = magic(imgPath,lastMid,lastAvg)
                      if lastAvg > 5:
                          mid = -1
                          conf = 0
                      else:
                          mid = lastMid
                          conf = 1
                      scribbleman.writerow([imgPath,mid,conf])#scribbleman instructions
                


def weldGapPoints(array): #helper function that returns the two adjacent points that have the largest weld gap under 10
    closest = 20
    for i in range(len(array) - 1):
        difference = abs(array[i] - array[i+1])
        if difference < 10 and abs(difference - 10) < abs(closest - 10):
            closest = difference
            pair = (array[i], array[i+1])
    
    return pair



start_time = time.time()
allImage()
print("--- %s seconds ---" % (time.time() - start_time))