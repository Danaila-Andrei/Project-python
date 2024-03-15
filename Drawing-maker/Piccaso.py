import cv2
import turtle
import numpy as np
from playsound import playsound
import winsound
import time


# Citirea imaginii
image = cv2.imread("mos.png")

# Flip orizontal pentru a corecta orientarea
image = cv2.flip(image, 0)

# Roteste imaginea cu 180 de grade
image = cv2.rotate(image, cv2.ROTATE_180)

# Convertirea imaginii în tonuri de gri
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Aplicarea unui filtru Laplacian pentru evidențierea marginilor
laplacian = cv2.Laplacian(gray, cv2.CV_64F)
laplacian = np.uint8(np.absolute(laplacian))

# Aplicarea unui prag pentru evidențierea marginilor
_, interior_contur = cv2.threshold(laplacian, 50, 255, cv2.THRESH_BINARY)

# Găsirea contururilor exterioare în imagine
contours_exterior, _ = cv2.findContours(interior_contur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Găsirea contururilor interioare în imagine
contours_interior, _ = cv2.findContours(interior_contur, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

# Inițializare Turtle pentru toate contururile
turtle.speed("fastest")
turtle.hideturtle()
turtle.bgcolor("black")
turtle.color("red")

# Desenarea cu Turtle peste imagine
turtle.up()

# Initializare setari ecran si imagine fundal
screen = turtle.Screen()
screen.setup(956 , 720)
screen.bgpic('Winter_BG.gif')

# Redare Melodie Craciun
winsound.PlaySound('We_Wish_You_A_Merry_Xmas.wav',winsound.SND_ASYNC|winsound.SND_LOOP)

# Desenare contururi exterioare
for contur in contours_exterior:
    turtle.penup()
    for punct in contur:
        turtle_x, turtle_y = punct[0][0] - image.shape[1] / 2, image.shape[0] / 2 - punct[0][1]
        turtle.goto(turtle_x, turtle_y)
        turtle.pendown()

# Desenare contururi interioare
for contur in contours_interior:
    turtle.penup()
    for punct in contur:
        turtle_x, turtle_y = punct[0][0] - image.shape[1] / 2, image.shape[0] / 2 - punct[0][1]
        turtle.goto(turtle_x, turtle_y)
        turtle.pendown()

# Așteaptă până când utilizatorul închide fereastra
turtle.mainloop()
