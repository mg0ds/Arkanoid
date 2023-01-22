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
PADDLE_START_POZ_X = WIDTH // 2 - PADDLE_WIDTH // 2
PADDLE_START_POZ_Y = HEIGHT - PADDLE_HEIGHT - int(HEIGHT * 0.04)
BALL_RADIUS = 7

# game levels, 16 blocks per level
# R, G, B, Y, P are colors, _ is empty space
# Y has 2hp, P has 3hp, other blocks have 1hp
game1 = ["BRBRBRBRBRBRBRBR", "RBRBRBRBRBRBRBRB"]
game2 = ["BRBRBRBRBRBRBRBR", "_B_P__RYYR__P_B_", "RR____________RR", "RBRBRBRBRBRBRBRB"]
game3 = ["GGRR___BP___YYGG", "RR____________RR", "BRGYPBRGYPBRGYPB"]
game4 = ["_G_____RR_____B_", "YPYPYPYPYPYPYPYP", "RBRBRBRBRBRBRBRB"]
game5 = ["BRGYPBRGYPBRGYPB", "RRRBBBGGGGYYYPPP", "RBRBRBRBRBRBRBRB", "YYYYYYYYYYYYYYYY"]
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
    last_x_vel = 0
    last_y_vel = -5
    ball_offset = 0

    def __init__(self, x, y, radius, power_up=False, color=WHITE, max_vel=5, sticky=False, bullet=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.power_up = power_up
        self.color = color
        self.max_vel = self.start_max_vel = max_vel
        self.sticky = sticky
        self.bullet = bullet
        self.x_vel = 0
        self.y_vel = self.max_vel
        if bullet:
            self.y_vel = -self.max_vel

    def draw(self, window):
        pygame.draw.circle(window, self.color, (self.x, self.y), self.radius)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.x_vel = 0
        self.y_vel = self.start_max_vel
        self.sticky = False

    def glued_ball(self):
        if self.x_vel != 0 and self.y_vel != 0:
            self.last_x_vel = self.x_vel
            self.last_y_vel = self.y_vel
        else:
            self.last_x_vel = 0
            self.last_y_vel = -5
        self.x_vel = 0
        self.y_vel = 0

class Block:
    B_WIDTH = 50
    B_HEIGHT = 20

    def __init__(self, x, y, color, reward=10, hp=1):
        self.x = x
        self.y = y
        self.color = color
        self.reward = reward
        self.hp = hp
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


def sticky_ball_release(keys, ball, time_up=False):
    if not ball.power_up and ball.y_vel == 0:
        if keys[pygame.K_SPACE]:
            ball.x_vel = ball.last_x_vel
            ball.y_vel = ball.last_y_vel
            return 1
        elif time_up:
            ball.x_vel = ball.last_x_vel
            ball.y_vel = ball.last_y_vel


def handle_collision(ball, paddle, blocks):
    if ball.power_up is False:  # game ball check
        # collision with walls
        if ball.y - ball.radius <= 0 and not ball.bullet:
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
                    if ball.sticky:
                        # sticky ball power up active, ball don't bounce from paddle automatically
                        # save bounce direction and stop ball in place
                        ball.glued_ball()
                        return 4, ball

        # collision with blocks
        for block in blocks:
            if ball.x + ball.radius >= block.x and ball.x - ball.radius <= block.x + block.B_WIDTH \
                    and ball.y + ball.radius >= block.y and ball.y - ball.radius <= block.y + block.B_HEIGHT:
                if not ball.bullet:
                    # game ball collision with block and bounce
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
                else:
                    # bullet collision with block, remove bullet
                    return 5, block
    else:  # power up collision check
        if ball.x >= paddle.x and ball.x <= paddle.x + paddle.width:
            if ball.y + ball.radius >= paddle.y:
                # power up catch
                return 1, ball
            else:
                # power up still falling
                return 2, ball


def power_up_generate():
    # how often power up will fall
    a = random.randint(0, 10)
    return a


def enlarge_paddle(paddle):
    paddle.width = 200
    paddle.x -= 50


def remove_block(block, block_to_remove):
    # remove block after collision
    block.remove(block_to_remove)


def draw(window, paddles, balls, blocks, score):
    window.fill(BLACK)

    score_text = score_font.render(f"{score}", True, WHITE)
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
    ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_RADIUS)
    balls = [ball]
    paddles = [paddle_1]
    enlarge_paddle_check = False
    sticky_ball_check = False
    ball_glued = False
    shooting_check = False
    bullets_check = False

    while run:
        clock.tick(FPS)
        draw(WINDOW, paddles, balls, blocks, score)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.KEYDOWN and shooting_check:
                if event.key == pygame.K_SPACE:
                    bullets_check = True

        keys = pygame.key.get_pressed()
        handle_paddle_movement(keys, paddle_1)
        for ball in balls:
            ball.move()
            collision_check = handle_collision(ball, paddle_1, blocks)

            if collision_check:
                if ball.power_up is False and collision_check[0] != 4:  # normal ball, collision with ball and block:
                    collision_check[1].hp -= 1
                    if collision_check[1].hp == 0:  # remove block if its hp falls to 0:
                        # check if power_up will spawn and what type:
                        pu_number = power_up_generate()
                        # print(f"power up number {pu_number}")
                        # create power up ball:
                        if pu_number == 0:
                            # enlarge pad
                            balls.append(Ball(collision_check[1].x + 25, collision_check[1].y + 10, 3, True, PINK, 3))
                        elif pu_number == 3:
                            # three balls
                            balls.append(Ball(collision_check[1].x + 25, collision_check[1].y + 10, 3, True, BLUE, 3))
                        elif pu_number == 7:
                            # sticky ball
                            balls.append(Ball(collision_check[1].x + 25, collision_check[1].y + 10, 3, True, YELLOW, 3))
                        elif pu_number == 10:
                            # shoot from paddle
                            balls.append(Ball(collision_check[1].x + 25, collision_check[1].y + 10, 3, True, RED, 3))
                        score += collision_check[1].reward
                        remove_block(blocks, collision_check[1])
                    if collision_check[0] == 5:
                        # bullet collision with block, remove bullet
                        balls.remove(ball)
                elif collision_check[0] == 4 and not ball_glued:
                    # sticky ball power up is active
                    # ball is stuck to paddle, waiting for SPACE key press to release
                    ball_glued = True
                    ball.ball_offset = ball.x - paddle_1.x
                else:  # ball is a power up ball
                    if collision_check[0] == 1:  # power up caught, remove power up ball, modify game by power up
                        try:
                            balls.remove(collision_check[1])  # remove power up ball
                        except:
                            pass

                        if enlarge_paddle_check is False and collision_check[1].color is PINK:
                            # enlarge paddle power up activate
                            print("enlarge paddle\n")
                            enlarge_paddle(paddle_1)
                            enlarge_paddle_check = True
                            enp_start_time = time.time()
                        elif collision_check[1].color is BLUE:
                            print("3 balls\n")
                            # three balls power up
                            for ball in balls[::-1]:
                                if ball.power_up is False:
                                    balls.append(Ball(ball.x, ball.y, BALL_RADIUS))
                                    balls[-1].x_vel += 2
                                    balls[-1].y_vel *= -0.8
                                    balls.append(Ball(ball.x, ball.y, BALL_RADIUS))
                                    balls[-1].x_vel -= 2
                                    balls[-1].y_vel *= -1.2
                        elif collision_check[1].color is YELLOW:
                            # sticky ball power up
                            print("ball sticks to paddle")
                            print("press SPACE to release\n")
                            sticky_ball_check = True
                            sticky_ball_start_time = time.time()
                        elif collision_check[1].color is RED:
                            # shoot bullets from paddle
                            print("shooting paddle")
                            print("press SPACE to shoot\n")
                            shooting_check = True
                            shooting_start_time = time.time()

            # power ups
            if enlarge_paddle_check:  # enlarge paddle timer
                if time.time() - enp_start_time > 10:
                    enlarge_paddle_check = False
                    paddle_1.width = 100
                    paddle_1.x += 50
                    print("enlarge paddle time up\n")

            if sticky_ball_check:
                all_glued_balls = [glued_ball for glued_ball in balls if ball.sticky and not ball.power_up]
                if time.time() - sticky_ball_start_time > 15:
                    sticky_ball_check = False
                    print("sticky ball time up\n")
                    for glued_ball in all_glued_balls:
                        sticky_ball_release(keys, glued_ball, time_up=True)
                        ball_glued = False
                    for ball in balls:
                        ball.sticky = False
                else:
                    ball.sticky = True
                    if ball_glued and ball.sticky and not ball.power_up and ball.y_vel == 0:
                        ball.x = paddle_1.x + ball.ball_offset
                        for glued_ball in all_glued_balls:
                            if sticky_ball_release(keys, glued_ball) == 1:
                                ball_glued = False

            if bullets_check:
                if time.time() - shooting_start_time > 3:
                    shooting_check = False
                    print("shooting time up\n")
                    bullets_check = False
                else:
                    balls.append(Ball(paddle_1.x + 2, paddle_1.y, 2, False, RED, 10, False, True))
                    balls.append(Ball(paddle_1.x + paddle_1.width - 2, paddle_1.y, 2, False, RED, 10, False, True))
                    bullets_check = False

            # balls outside screen
            if ball.power_up is False and ball.bullet is False and ball.y > HEIGHT:
                # player didn't catch game ball
                ball_height_check = ["o" for ball in balls if (not ball.power_up and not ball.bullet)]
                if len(ball_height_check) <= 1:
                    ball.reset()
                    balls = [balls[0]]
                    paddle_1.reset()
                    score = 0
                    enlarge_paddle_check = False
                    sticky_ball_check = False
                    ball_glued = False
                    shooting_check = False
                    bullets_check = False

                    loss_text = wl_font.render("You lost!", True, WHITE)
                    WINDOW.blit(loss_text, ((WIDTH // 2) - (loss_text.get_width() // 2), HEIGHT // 2))
                    pygame.display.update()
                    pygame.time.delay(2000)
                else:
                    balls.remove(ball)
            if (ball.power_up and ball.y > HEIGHT) or (ball.bullet and ball.y < 0):
                # remove ball
                # player didn't catch power up ball
                # bullet out of screen
                try:
                    balls.remove(ball)
                except:
                    pass

        # all blocks are destroyed
        if blocks == []:
            balls = [balls[0]]
            balls[0].reset()
            paddle_1.reset()
            score += 100
            enlarge_paddle_check = False
            sticky_ball_check = False
            ball_glued = False

            next_level_text = wl_font.render("Next level!", True, WHITE)
            WINDOW.blit(next_level_text, ((WIDTH // 2) - (next_level_text.get_width() // 2), HEIGHT // 2))
            pygame.display.update()
            game += 1
            if game == len(games):
                # all levels finished
                win_text = wl_font.render("You WON!", True, WHITE)
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
