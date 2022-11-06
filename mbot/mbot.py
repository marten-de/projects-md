"""
We assume the following settings for this bot:
Mac screen resolution "scaled", "looks like 1280x800".
Friday Night Funkin (version 0.2.7.1) for Mac OS X, run in window mode
"""

from time import sleep
import os
from PIL import Image
from pynput.keyboard import Controller
from mss import mss
from statistics import mean

# This nested ditionary holds all the color values against which we need to
# check. It is divided into a part for level 1 (1-5) and one for level 6, which
# makes it very easy to call the according values by simply indexing into the
# current level.
color_values = {
    1: {
        "red": (249, 58, 63),
        "magenta": (194, 76, 153),
        "blue": (0, 255, 255),
        "green": (18, 251, 5),
        "red_f": (203, 99, 107),
        "magenta_f": (168, 109, 159),
        "blue_f": (54, 218, 222),
        "green_f": (65, 215, 72)
    },
    6: {
        "red": (255, 140, 86),
        "magenta": (228, 125, 255),
        "blue": (62, 202, 255),
        "green": (113, 227, 0),
        "red_f": (218, 156, 127),
        "magenta_f": (200, 145, 233),
        "blue_f": (101, 196, 233),
        "green_f": (133, 211, 80)
    }
}

# Defining a helper variable to track at which level in the game we are. We can
# just initialize to 1, because we constantly check for this condition anyway.
current_level = 1

# Defining constants that are related to where the area of the game is, that we
# need to capture in order to know what happens in-game. WIDTH and HEIGHT are the
# size of the area and X_PAD and Y_PAD are the position of the top left corner
# on the screen. On Mac, use CMD+SHIFT+4 to see the according coordinates.
X_PAD = 690
Y_PAD = 96
WIDTH = 445
HEIGHT = 150

# Initializing a keyboard to be able to create keyboard outputs
# that are used to play the game.
keyboard = Controller()

# Of course the bot would run without this function, but we think it
# is best practice to give the user a feedback about what is going on
def greet_message():

    # Showing a message that the bot has been activated
    ini_message = "mbot is now active. use CTRL+c to terminate."

    # Using some # padding to make the message stand out among
    # other terminal messages. The padding adapts to the message,
    # so it could be changed at any time. Wouldn't work if the message
    # gets too long.
    print("\n" + "#" * (len(ini_message) + 4) + 
          "\n# " + ini_message + " #\n" + 
          "#" * (len(ini_message) + 4) + "\n" * 2)


# This function is the core of our bot and allows it to see what is going
# on in-game. Here we just take a simple screenshot, but later we will
# access single pixels that are relevant to us.
def capture_screenshot():
    with mss() as sct:

        # Define a window that is relevant for us, so that we don't capture
        # the whole screen. However, we don't need to be too pedantic, the speed
        # gain is not substential if we are already dealing with a rather small
        # screen portion.
        monitor = {"top": Y_PAD, "left": X_PAD, "width": WIDTH, "height": HEIGHT}

        # Capture the part of the screen that is relevant for us using mss,
        # which is supposed to be the quickest by far, and for this bot
        # we definitely need all the speed we can get. Note that the screenshot
        # will be given back with the real screen resolution, that means instead of
        # 445x150 it will be 890x300. We need to consider this when we define the
        # pixels that interest us.
        sct_img = sct.grab(monitor)

        # Convert to PIL/Pillow Image and return
        return Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')


# The game has levels 1-6, of which 1-5 have the same graphics and can be run
# (or played) by our bot in the same way. However, level 6 has a pixalated
# graphic that messes up our detection pattern, so we need to adjust our bot,
# if the player enters level 6. This function takes an image as argument and is
# able to determine, if this image is part of levels 1-5 or level 6.
def check_level(image):

    # Creating a list of grey-value pixels by use of mean() function. We
    # use 2*HEIGHT, because again the image we are dealing with here, has
    # the real screen resolution, which is double, so 300 in this case.
    # One row is enough for our purpose, which is to find out if the graphics
    # are "blocky". To do this in an area where we actually have some edges, we
    # choose x = 65 and vary y all the way from 0 to 299.
    pixel_row = []
    for i in range(HEIGHT * 2):
        pixel_row.append(mean(image.getpixel((65, i))))

    # Creating a list of differences between neighbored pixels
    differences = []
    for i in range((HEIGHT * 2) - 1):
        differences.append(pixel_row[i + 1] - pixel_row[i])

    # Creating a list that holds the position of each major difference from the
    # differences list. As a threshold we use 25, which is a noticeable color
    # change from one pixel to the next.
    color_threshold = 25
    big_diff = []
    for i in range((HEIGHT * 2) - 1):
        if abs(differences[i]) > color_threshold:
            big_diff.append(i)

    # This is the last list we need to create here. It holds the distances between
    # the neighbored positions in the bigg_diff list. This means if one major color
    # change was e.g. at i=37 and the next was at i=50, then the distance is 13. This
    # is useful, because we can see if the distances are always a product of a certain
    # number, e.g. 12. If that is the case, then we are very certain that we are looking
    # at a "blocky", that means pixalated image, and that is our clue, that we are
    # in level 6.
    distances = []
    for i in range(len(big_diff) - 1):
        distances.append(big_diff[i+1] - big_diff[i])

    # We calculate c, which is the number of times, a distance value is divisable
    # by block_factor, which we set at 12 after some experimenting and knowing that
    # this factor is common in level 6 images, but NOT in level 1-5 images.
    c = 0
    block_factor = 12
    for i in range(len(distances)):
        if distances[i] % block_factor == 0:
            c += 1

    # Lastly we calculate an index by dividing by the number of total distances.
    # To make sure our program doesn't crash in case of a white or black screen,
    # we need to include an if-condition that accounts for len(distances) being zero.
    if len(distances) > 0:
        level_indicator = c / len(distances)
    else:
        level_indicator = 'none'

    # Level 1-5 values for the indicator are typically 0-0.2, level 6 values are
    # 0.6-0.8, so we set our threshold at 0.45. If we get an invalid indicator
    # then we just keep the current level. Note that return 1 will be done for
    # levels 1-5, which behave completely identical.
    blocky_threshold = 0.45
    if level_indicator == 'none':
        return current_level

    elif level_indicator > blocky_threshold:
        return 6

    else:
        return 1


# This function updates our current level variable and thus allows us to
# switch our color values, by switching the index we use in accessing
# color_values dictionary.
def switch_level(new_level):

    # To use a global variable inside a function we usually don't need to do anything,
    # but to change it's value we must first declare it as global and then use a separate
    # line of code for our assignment.
    global current_level

    # Updating the current level global variable
    current_level = new_level
    return


def main():

    # Calling greet_message to show that the bot is running
    greet_message()

    # Defining a helper variable that acts as a counter for the level check.
    # We don't want to check for the level on every frame, because that is a waste
    # of computing power. The framerate constant is set to 0.05 because the game
    # needs quick action and we need to monitor everything that is going on. However,
    # setting the rate too low actually gives us worse performance in-game, probably
    # because the program can't keep up.
    i = 0.0
    FRAMERATE = 0.05

    try:
        while True:  # The bot should run until interrupted

            # Here the framerate comes into play. It is actually a forced break
            # between all our computing, both designed to allow for keyboard
            # interrupt and to make sure the program can keep up.
            sleep(FRAMERATE)

            # We are calling our screenshot function to use this as input for our
            # analysis of the game events.
            image = capture_screenshot()
            
            # We define 4 variables that monitor a specific pixel each. The variable
            # name is the letter that should be pressed if the according pixel changes
            # to a defined color (WASD). These pixels track the "pressing" of a key.
            a = image.getpixel((116, 48))
            s = image.getpixel((332, 48))
            w = image.getpixel((560, 48))
            d = image.getpixel((776, 48))

            # Another range of pixels, this time they track the "holding" of a key, which
            # corresponds to longer tones in the game. the "f" in the variable name stands
            # for "faded", because our signal color is faded, compared to the original
            # color that should trigger the variables without the "f".
            af = image.getpixel((116, 130))
            sf = image.getpixel((332, 150))
            wf = image.getpixel((560, 140))
            df = image.getpixel((776, 135))
            
            # Increasing our helper counter by the framerate. Could be done at the end
            # of the while-loop, but doesn't matter too much.
            i += FRAMERATE
            
            # This condition triggers the "d" key. It checks, if the monitored pixel
            # "d" is in color "red" of if "df" is in "red_f" which is faded red. If
            # either of these conditions holds true, the button is pressed, if neither
            # hold true, it is released. Note that because of our high framerate, the
            # concurrent keypresses behave like a hold, which is exactly what we want,
            # in case the game wants us to hold a key. For the "pressing" of a key, it
            # doesn't matter if we press multiple times in a very short timeframe, the
            # game will still only register 1 press.
            if all(d[i] < color_values[current_level]['red'][i] + 15 and d[i] > color_values[current_level]['red'][i] - 15  for i in range(3))\
            or all(df[i] < color_values[current_level]['red_f'][i] + 15 and df[i] > color_values[current_level]['red_f'][i] - 15  for i in range(3)):
                keyboard.press('d')
            else:
                keyboard.release('d')

            # Same for the "a" key. Note that by spelling out all the individual key
            # conditions, we gain a bit more flexibility to adjust the conditions,
            # if necessary. In fact they are not all identical, because some colors
            # need a bigger tolerance to be registered reliably. Faded colors have
            # a higher tolerance by default (+- 15 per each RGB value), whereas
            # normal colors have a tolerance of 5. If we try to detect the EXACT
            # color to trigger the keypresses, we get a lot of missed tones, because
            # the game window sometimes changes a bit, which makes our pixels be
            # at the "wrong" location temporarily. For red and magenta (normal),
            # we also increased the tolerance to 15 because of level 6 peculiarities.
            # It would also be possible to store the according tolerance in a dictionary
            # and call according to level, but the higher tolerance doesn't hurt us, so
            # it is not needed.
            if all(a[i] < color_values[current_level]['magenta'][i] + 15 and a[i] > color_values[current_level]['magenta'][i] - 15  for i in range(3))\
            or all(af[i] < color_values[current_level]['magenta_f'][i] + 15 and af[i] > color_values[current_level]['magenta_f'][i] - 15  for i in range(3)):
                keyboard.press('a')
            else:
                keyboard.release('a')

            # Same for the "s" key.
            if all(s[i] < color_values[current_level]['blue'][i] + 5 and s[i] > color_values[current_level]['blue'][i] - 5  for i in range(3))\
            or all(sf[i] < color_values[current_level]['blue_f'][i] + 15 and sf[i] > color_values[current_level]['blue_f'][i] - 15  for i in range(3)):
                keyboard.press('s')
            else:
                keyboard.release('s')

            # Same for the "w" key.
            if all(w[i] < color_values[current_level]['green'][i] + 5 and w[i] > color_values[current_level]['green'][i] - 5  for i in range(3))\
            or all(wf[i] < color_values[current_level]['green_f'][i] + 15 and wf[i] > color_values[current_level]['green_f'][i] - 15  for i in range(3)):
                keyboard.press('w')
            else:
                keyboard.release('w')
            
            # Approximately every 5 seconds we trigger this check, to see
            # in which level we are and if necessary, change it. Note that
            # for some reason we need i > 5 instead of i = 5. Maybe this is
            # because of floating point imprecision. It doesn't matter, because
            # we will reset the counter anyway and it is not crucial, at which
            # exact point in time we do the check.
            if i > 5:
                level = check_level(image)

                # If the level return value doesn't match our current level,
                # switch and use the new level as argument.
                if level != current_level:
                    switch_level(level)

                # Setting the counter for the level check back to zero
                i = 0
                
    # This exception stops the infinite loop. It is maybe not necessary, because
    # we can also quit with CTRL-c anyways, but probably it is better to incluse
    # this as a safety feature.
    except (KeyboardInterrupt, SystemExit):

        # This command apparently resets the echo state of the terminal (googled)
        # without clearing it, which is what reset would do.
        os.system('stty sane')
        print(' mbot terminated.')


if __name__ == '__main__':
    main()