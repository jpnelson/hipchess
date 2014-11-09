from PIL import Image, ImageDraw, ImageFont
import os

BOARD_SIZE = 320
CELL_SIZE = 40
BOARD_AND_GUTTER_SIZE = BOARD_SIZE + CELL_SIZE
CELL_PADDING = 4
BOARD_PADDING = 10

def render(game, path):
    size = (BOARD_AND_GUTTER_SIZE, BOARD_AND_GUTTER_SIZE)
    im = Image.new('RGBA', size)
    draw = ImageDraw.Draw(im)

    draw.rectangle([(0, 0), (BOARD_AND_GUTTER_SIZE, BOARD_AND_GUTTER_SIZE)], fill=(255, 255, 255))

    for y in range(0, 8):
        draw.text((BOARD_SIZE + BOARD_PADDING, y * CELL_SIZE + CELL_SIZE/2), str(8 - y), (0, 0, 0))

        for x in range(0, 8):
            draw.text((x * CELL_SIZE + CELL_SIZE/2, BOARD_SIZE + BOARD_PADDING), chr(x + 97), (0, 0, 0))

            background_color = (255, 255, 255)
            if (x + y * 7) % 2 == 0:
                background_color = (123, 123, 123)

            if game.last_move[0] == (x, y) or game.last_move[1] == (x, y):
                (bg_r, bg_g, bg_b) = background_color
                background_color = (bg_r, bg_g, bg_b - 50)

            draw.rectangle(
                [
                    (x * CELL_SIZE, y * CELL_SIZE),
                    ((x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE)
                ],
                background_color
            )

            sprite = game.board[y][x]
            if sprite != '':
                sprite_file = Image.open(os.path.abspath('sprites/' + sprite + '.png')).convert('RGBA')
                im.paste(sprite_file, (x * CELL_SIZE + CELL_PADDING, y * CELL_SIZE + CELL_PADDING), mask=sprite_file)

    im.save(path, 'PNG')