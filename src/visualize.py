import pygame
import sys

class Visualizer:
    def __init__(self, locations, width=800, height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Otimização de Rotas - GA")
        self.clock = pygame.time.Clock()
        self.locations = locations

        lats = [lat for _, lat, lon, _, _ in locations]
        lons = [lon for _, lat, lon, _, _ in locations]
        self.min_lat, self.max_lat = min(lats), max(lats)
        self.min_lon, self.max_lon = min(lons), max(lons)

        self.width = width
        self.height = height
        self._last_overlay = None  # texto opcional

    def transform(self, lat, lon):
        x = int((lon - self.min_lon) / (self.max_lon - self.min_lon) * (self.width - 100) + 50)
        y = int((lat - self.min_lat) / (self.max_lat - self.min_lat) * (self.height - 100) + 50)
        return (x, y)

    def _draw_overlay(self, text):
        if not text:
            return
        font = pygame.font.SysFont("Arial", 18)
        lines = text.split("\n")
        y = self.height - (len(lines) * 22) - 10
        overlay_rect = pygame.Rect(0, y - 8, self.width, (len(lines) * 22) + 16)
        pygame.draw.rect(self.screen, (10, 10, 10), overlay_rect)
        for i, line in enumerate(lines):
            surf = font.render(line, True, (255, 255, 255))
            self.screen.blit(surf, (10, y + i * 22))

    def draw(self, generation, route, distance, overlay=None):
        self.screen.fill((30, 30, 30))

        # eventos (permite fechar a janela)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        coords = []
        for name, lat, lon, produto, prioridade in self.locations:
            x, y = self.transform(lat, lon)
            coords.append((x, y))
            if name.lower().startswith("hospital"):
                pygame.draw.circle(self.screen, (255, 255, 0), (x, y), 10)
            else:
                color = (0, 200, 0) if prioridade == "Baixa" else (200, 50, 50)
                pygame.draw.circle(self.screen, color, (x, y), 6)

        if route:
            for i in range(len(route) - 1):
                p1 = coords[route[i]]
                p2 = coords[route[i + 1]]
                pygame.draw.line(self.screen, (0, 150, 250), p1, p2, 2)

        font = pygame.font.SysFont("Arial", 20)
        text1 = font.render(f"Geração: {generation}", True, (255, 255, 255))
        text2 = font.render(f"Distância: {distance:.2f}", True, (255, 255, 255))
        self.screen.blit(text1, (10, 10))
        self.screen.blit(text2, (10, 40))

        self._last_overlay = overlay
        self._draw_overlay(self._last_overlay)

        pygame.display.flip()
        self.clock.tick(30)

    def hold_until_enter(self, message="Pressione ENTER para gerar instruções... (ou ESC para sair)"):
        while True:
            self.draw_overlay_only(message)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return True
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            self.clock.tick(30)

    def draw_overlay_only(self, message):
        # redesenha apenas o overlay sobre o último frame
        if self._last_overlay != message:
            # força re-render do overlay
            self._last_overlay = message
        # não temos o último frame aqui, então apenas preenche fundo escuro
        # para evitar "ghosting" — simples e funcional
        pygame.display.get_surface().fill((30, 30, 30))
        # escreve somente o overlay grande no centro da tela
        font = pygame.font.SysFont("Arial", 24)
        lines = message.split("\n")
        total_h = len(lines) * 30
        start_y = (self.height - total_h) // 2
        for i, line in enumerate(lines):
            surf = font.render(line, True, (255, 255, 255))
            rect = surf.get_rect(center=(self.width // 2, start_y + i * 30))
            self.screen.blit(surf, rect)
        pygame.display.flip()
