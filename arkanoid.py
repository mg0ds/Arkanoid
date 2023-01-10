import pygame
import random
import time

# initiate pygame
pygame.init()

WIDTH = 800
HEIGHT = 600

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arkanoid")
score_font = pygame.font.SysFont("arial", 50)
wl_font = pygame.font.SysFont("arial", 80)

# max speed
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 0, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_START_POZ_X = WIDTH//2 - PADDLE_WIDTH//2
PADDLE_START_POZ_Y = HEIGHT - PADDLE_HEIGHT - int(HEIGHT * 0.04)
BALL_RADIUS = 7

# game levels, 16 signs per level
# R, G, B, Y, P are colors, _ is empty space
# Y has 2hp, P has 3hp, other blocks have 1hp
game1 = ["BRBRBRBRBRBRBRBR"]
game2 = ["_B_P__RYYR__P_B_"]
game3 = ["GGRR___BP___YYGG", "RR____________RR", "BRGYPBRGYPBRGYPB"]
game4 = ["_G_____RR_____B_", "YPYPYPYPYPYPYPYP"]
game5 = ["BRGYPBRGYPBRGYPB", "RRRBBBGGGGYYYPPP"]
game6 = ["PPPPPPPPPPPPPPPP", "RRRRRRRRRRRRRRRR", "GGGGGGGGGGGGGGGG", "BBBBBBBBBBBBBBBB", "YYYYYYYYYYYYYYYY"]
games = [game1, game2, game3, game4, game5, game6]


class Paddle:
    COLOR = WHITE
    VEL = 4

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = self.starting_width = width
        self.height = self.starting_height = height

    def draw(self, window):
        pygame.draw.rect(window, self.COLOR, (self.x, self.y, self.width, self.height))

    def move(self, left=True):
        if left:
            self.x -= self.VEL
        else:
            self.x += self.VEL

    def reset(self):
        self.width = self.starting_width
        self.height = self.starting_height
        self.x = PADDLE_START_POZ_X
        self.y = PADDLE_START_POZ_Y


class Ball:
    def __init__(self, x, y, radius, power_up=False, color=WHITE, max_vel=5):
        self.x = x
        self.y = y
        self.radius = radius
        self.power_up = power_up
        self.color = color
        self.max_vel = max_vel
        self.x_vel = 0
        self.y_vel = self.max_vel

    def draw(self, window):
        pygame.draw.circle(window, self.color, (self.x, self.y), self.radius)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.x_vel = 0
        self.y_vel = self.max_vel


class Block:
    B_WIDTH = 50
    B_HEIGHT = 20

    def __init__(self, x, y, color, reward=10, hp=1, active=True):
        self.x = x
        self.y = y
        self.color = color
        self.reward = reward
        self.hp = hp
        self.active = active
        if self.color == YELLOW:
            self.hp = 2
            self.reward = 25
        if self.color == PINK:
            self.hp = 3
            self.reward = 40

    def draw(self, window):
        pygame.draw.rect(window, self.color, (self.x, self.y, self.B_WIDTH, self.B_HEIGHT))


def generate_board(game):
    block_x_poz = 0
    block_y_poz = int(HEIGHT * 0.07)
    blocks = []
    colordict = {"B": BLUE, "R": RED, "G": GREEN, "Y": YELLOW, "P": PINK}
    for row in game:
        for bl in row:
            if bl != "_":
                blocks.append(Block(block_x_poz, block_y_poz, colordict[bl]))
                block_x_poz += 50
            else:
                block_x_poz += 50
        block_x_poz = 0
        block_y_poz += 20
    return blocks


def handle_paddle_movement(keys, paddle_1):
    if keys[pygame.K_LEFT] and paddle_1.x - paddle_1.VEL >= 0:
        paddle_1.move(left=True)
    elif keys[pygame.K_RIGHT] and paddle_1.x + paddle_1.width + paddle_1.VEL <= WIDTH:
        paddle_1.move(left=False)


def handle_collision(ball, paddle, blocks):

    if ball.power_up == False:  # game ball check
        # collision with walls
        if ball.y - ball.radius <= 0:
            ball.y_vel *= -1
        elif ball.x - ball.radius <= 0:
            ball.x_vel *= -1
        elif ball.x + ball.radius >= WIDTH:
            ball.x_vel *= -1

        # collision with paddle
        if ball.y_vel > 0:
            if ball.x >= paddle.x and ball.x <= paddle.x + paddle.width:
                if ball.y + ball.radius >= paddle.y:
                    ball.y_vel *= -1

                    # ball bounce angle change
                    middle_x = paddle.x + paddle.width / 2
                    difference_in_x = middle_x - ball.x
                    reduction_factor = (paddle.width / 2) / ball.max_vel
                    x_vel = difference_in_x / reduction_factor
                    ball.x_vel = x_vel * -1


        # collision with blocks
        for block in blocks:
            if ball.x + ball.radius >= block.x and ball.x - ball.radius <= block.x + block.B_WIDTH \
                    and ball.y + ball.radius >= block.y and ball.y - ball.radius <= block.y + block.B_HEIGHT:
                if ball.y + ball.radius >= block.y - 6 and ball.y + ball.radius <= block.y + 6:
                    ball.y_vel *= -1
                if ball.y - ball.radius <= block.y + block.B_HEIGHT + 6 \
                        and ball.y - ball.radius >= block.y + block.B_HEIGHT - 6:
                    ball.y_vel *= -1
                if ball.x + ball.radius >= block.x - 6 and ball.x + ball.radius <= block.x + 6:
                    ball.x_vel *= -1
                if ball.x - ball.radius <= block.x + block.B_WIDTH + 6 \
                        and ball.x - ball.radius >= block.x + block.B_WIDTH - 6:
                    ball.x_vel *= -1
                return 3, block
    else:  # power up collision check
        if ball.x >= paddle.x and ball.x <= paddle.x + paddle.width:
            if ball.y + ball.radius >= paddle.y:
                # power up catch
                return 1, ball
            else:
                # power up still falling
                return 2, ball


def power_up_generate():
    # how often powerup will fall
    a = random.randint(0, 1)
    return a


def enlarge_paddle(paddle):
    paddle.width = 200
    paddle.x -= 50


def remove_block(block, block_to_remove):
    # remove block after collision
    block.remove(block_to_remove)


def draw(window, paddles, balls, blocks, score):
    window.fill(BLACK)

    score_text = score_font.render(f"{score}", 1, WHITE)
    window.blit(score_text, (WIDTH // 4 - score_text.get_width() // 2, 200))

    for paddle in paddles:
        paddle.draw(window)

    for block in blocks:
        block.draw(window)

    for ball in balls:
        ball.draw(window)

    pygame.display.update()


def main():
    run = True
    clock = pygame.time.Clock()

    score = 0
    game = 0
    blocks = generate_board(games[game])
    paddle_1 = Paddle(PADDLE_START_POZ_X, PADDLE_START_POZ_Y, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = Ball(WIDTH//2, HEIGHT//2, BALL_RADIUS)
    balls = [ball]
    paddles = [paddle_1]
    #enlarge_paddle(paddle_1)
    power_up = False
    enlarge_paddle_check = False

    while run:
        clock.tick(FPS)
        draw(WINDOW, paddles, balls, blocks, score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        ball_no = 1
        keys = pygame.key.get_pressed()
        handle_paddle_movement(keys, paddle_1)
        for ball in balls:
            ball.move()
            collision_check = handle_collision(ball, paddle_1, blocks)

            if collision_check:
                if ball.power_up == False:  # normal ball, collision with ball and block:
                    collision_check[1].hp -= 1
                    if collision_check[1].hp == 0:  # remove block if its hp falls to 0:
                        # check if power_up will spawn and what type:
                        pu_number = power_up_generate()
                        print(pu_number)
                        if pu_number == 0:
                            # create power up ball:

                            # add some code for different power ups
                            balls.append(Ball(collision_check[1].x + 25, collision_check[1].y + 10, 3, True, PINK, 3))
                            print(balls)
                        score += collision_check[1].reward
                        remove_block(blocks, collision_check[1])
                else:  # ball is a power up ball
                    if collision_check[0] == 1:  # power up caught, remove power up ball, modify game by power up
                        print("zlapane")
                        balls.remove(collision_check[1])
                        if enlarge_paddle_check is False:  # only one enlarge paddle power up at the time
                            enlarge_paddle(paddle_1)
                            enlarge_paddle_check = True
                            enp_start_time = time.time()
                    power_up = False


            if ball.power_up is False and ball.y > HEIGHT:
                # player didn't catch game ball
                ball.reset()
                balls = [balls[0]]
                paddle_1.reset()
                score = 0
                loss_text = wl_font.render("You lose!", 1, WHITE)
                WINDOW.blit(loss_text, ((WIDTH // 2) - (loss_text.get_width() // 2), HEIGHT // 2))
                pygame.display.update()
                pygame.time.delay(2000)
            if ball.power_up and ball.y > HEIGHT:
                # player didn't catch power up ball
                balls.remove(ball)

            if enlarge_paddle_check:  # enlarge paddle timer
                if time.time() - enp_start_time > 10:
                    enlarge_paddle_check = False
                    paddle_1.width = 100
                    paddle_1.x += 50



        # all blocks are destroyed
        if blocks == []:
            ball.reset()
            paddle_1.reset()
            score += 100

            next_level_text = wl_font.render("Next level!", 1, WHITE)
            WINDOW.blit(next_level_text, ((WIDTH // 2) - (next_level_text.get_width() // 2), HEIGHT // 2))
            pygame.display.update()
            game += 1
            if game == len(games):
                # all levels finished
                win_text = wl_font.render("You WON!", 1, WHITE)
                WINDOW.blit(win_text, ((WIDTH // 2) - (win_text.get_width() // 2), HEIGHT // 2))
                pygame.display.update()
                pygame.time.delay(2000)
                pygame.quit()
            else:
                # load next board
                blocks = generate_board(games[game])
                pygame.time.delay(2000)



    pygame.quit()


if __name__ == "__main__":
    main()
