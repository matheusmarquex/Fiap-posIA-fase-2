import pygame
import sys


class Visualizer:
    def __init__(self, locations, width=800, height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Otimização de Rotas - GA")
        self.clock = pygame.time.Clock()
        self.locations = locations

        # normaliza coordenadas para caber na tela
        lats = [lat for _, lat, lon in locations]
        lons = [lon for _, lat, lon in locations]
        self.min_lat, self.max_lat = min(lats), max(lats)
        self.min_lon, self.max_lon = min(lons), max(lons)

        self.width = width
        self.height = height

    def transform(self, lat, lon):
        """Converte coordenadas reais para pixels na tela"""
        x = int((lon - self.min_lon) / (self.max_lon - self.min_lon) * (self.width - 100) + 50)
        y = int((lat - self.min_lat) / (self.max_lat - self.min_lat) * (self.height - 100) + 50)
        return (x, y)

    def draw(self, generation, route, distance):
        self.screen.fill((30, 30, 30))

        # eventos (para poder fechar janela)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # desenha pontos
        coords = []
        for name, lat, lon in self.locations:
            x, y = self.transform(lat, lon)
            coords.append((x, y))
            color = (200, 50, 50) if name.lower().startswith("hospital") else (50, 200, 50)
            pygame.draw.circle(self.screen, color, (x, y), 8)

        # desenha rota
        if route:
            for i in range(len(route) - 1):
                p1 = coords[route[i]]
                p2 = coords[route[i + 1]]
                pygame.draw.line(self.screen, (0, 150, 250), p1, p2, 2)

        # textos
        font = pygame.font.SysFont("Arial", 20)
        text1 = font.render(f"Geração: {generation}", True, (255, 255, 255))
        text2 = font.render(f"Distância: {distance:.2f}", True, (255, 255, 255))
        self.screen.blit(text1, (10, 10))
        self.screen.blit(text2, (10, 40))

        pygame.display.flip()
        self.clock.tick(30)  # até 30 fps
