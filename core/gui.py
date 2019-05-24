from .engine import Engine
from os import listdir
from .constants import VOID, NEUTRAL, BUILDING_TYPE
from .building import Building
from .unit import Unit
import pygame

DISPLAY_SIZE = 960, 540
OFFSET = 433, 33
TILE_LENGTH = 39
GAP = 2

class GUIEngine(Engine):

    instance = None

    def __init__(self, *args, **kwargs):
        if GUIEngine.instance:
            print("Only one GUI instance is available")
            exit(1)
        else:
            super().__init__(*args, **kwargs)
            pygame.init()
            pygame.font.init()
            self.screen = pygame.display.set_mode(DISPLAY_SIZE)
            pygame.display.set_caption("A Code of Fire and Ice")
            self.load_images()
            GUIEngine.instance = self

    def load_images(self):
        self.images = {filename.replace(".png", "").replace(".jpg", ""): pygame.image.load("./core/images/" + filename) \
            for filename in listdir("./core/images")}

        self.background = pygame.transform.scale(self.images["background"], DISPLAY_SIZE)

        for image_name in self.images:
            if image_name != "background" and "panel" not in image_name and image_name != "icon":
                self.images[image_name] = pygame.transform.scale(self.images[image_name], (TILE_LENGTH, TILE_LENGTH))   

        pygame.display.set_icon(self.images["icon"])        

    def gameloop(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.restart()

        # Draw background
        self.screen.blit(self.background, (0, 0))

        grid = self.get_map()

        # Draw background tiles and units
        for row in grid:
            for cell in row:
                
                kind = ""
                owner = cell.get_owner()
                if owner == 0:
                    if cell.is_active():
                        kind = "fire_enabled"
                    else:
                        kind = "fire_disabled"
                elif owner == 1:
                    if cell.is_active():
                        kind = "ice_enabled"
                    else:
                        kind = "ice_disabled"
                elif owner == VOID:
                    kind = "block"
                elif owner == NEUTRAL:
                    kind = "neutral"
                else:
                    print("kms")

                self.screen.blit(self.images[kind], (OFFSET[0] + cell.get_x() * (TILE_LENGTH + GAP),
                    OFFSET[1] + cell.get_y() * (TILE_LENGTH + GAP)))

                icon = ""
                building_icon = ""

                
                if cell.is_mine():
                    building_icon = "mine_cart" if cell.get_building() else "mine"
                elif owner == VOID or owner == NEUTRAL:
                    continue

                prefix = ["fire", "ice"][owner]
                if cell.get_unit():
                    level = cell.get_unit().get_level()
                    icon = f'{prefix}_soldier{level}'

                if cell.get_building():
                    building: Building = cell.get_building()
                    if building.get_type() == BUILDING_TYPE.HQ:
                        icon = f'{prefix}_hq'
                    elif building.get_type() == BUILDING_TYPE.MINE:
                        building_icon = f'{prefix}_mine'
                    elif building.get_type() == BUILDING_TYPE.TOWER:
                        building_icon = f'{prefix}_tower'
                    else:
                        print("kms x2")

                if building_icon:
                    self.screen.blit(self.images[building_icon], (OFFSET[0] + cell.get_x() * (TILE_LENGTH + GAP),
                        OFFSET[1] + cell.get_y() * (TILE_LENGTH + GAP)))

                if icon:
                    self.screen.blit(self.images[icon], (OFFSET[0] + cell.get_x() * (TILE_LENGTH + GAP),
                        OFFSET[1] + cell.get_y() * (TILE_LENGTH + GAP)))

        p1, p2 = str(self.get_player(0))[:5], str(self.get_player(1))[:5]
        income1, income2 = self.get_income(0), self.get_income(1)
        gold1, gold2 = self.get_gold(0), self.get_gold(1)
        turns = self.get_turns()

        pos_or_neg = lambda x: "+" + str(x) if x >= 0 else str(x)
        income1 = pos_or_neg(income1)
        income2 = pos_or_neg(income2)

        font = pygame.font.SysFont("Sans", 30, bold=True)
        font2 = pygame.font.SysFont("Sans", 24, bold=True)

        p1_text = font.render(p1, True, (255,0,0))
        p2_text = font.render(p2, True, (33, 168, 221))

        turn_text = font.render(f'Turn {turns // 2}', True, (33, 168, 221)) if not turns % 2 else \
            font.render(f'Turn {turns // 2}', True, (255,0,0))

        gold1_text = font2.render(f'Gold: {gold1}', True, (255, 255, 255))
        gold2_text = font2.render(f'Gold: {gold2}', True, (255, 255, 255))

        income1_text = font2.render(f'Income: {income1}', True, (255, 255, 255))
        income2_text = font2.render(f'Income: {income2}', True, (255, 255, 255))

        self.screen.blit(p1_text, (140, 87))
        self.screen.blit(p2_text, (140, 357))
        self.screen.blit(turn_text, (168, 248))
        self.screen.blit(gold1_text, (145, 120))
        self.screen.blit(income1_text, (145, 150))
        self.screen.blit(gold2_text, (145, 390))
        self.screen.blit(income2_text, (145, 420))
        
        pygame.display.flip()
        
        super().gameloop()