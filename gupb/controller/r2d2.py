from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from gupb.model import arenas, characters, coordinates
from gupb.model.characters import Facing
from gupb import controller

import random
import numpy as np

POSSIBLE_ACTIONS = [
    characters.Action.TURN_LEFT,
    characters.Action.TURN_RIGHT,
    characters.Action.STEP_FORWARD,
    characters.Action.ATTACK,
]

EXPLORE_COEF = 0.2


class R2D2Controller(controller.Controller):
    def __init__(self, first_name: str):
        self.first_name: str = first_name
        self.map = np.zeros((200, 200))
        self.position = None
        self.facing = None
        self.visible_tiles = {}
        self.menhir_position = None
        self.on_menchir = False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, R2D2Controller):
            return self.first_name == other.first_name
        return False

    def __hash__(self) -> int:
        return hash(self.first_name)

    def follow_the_path(self, destination: coordinates.Coords):
        matrix = Grid(matrix=self.map)
        start = matrix.node(self.position.x, self.position.y)
        destination = matrix.node(destination.x, destination.y)
        astar_finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
        path, _ = astar_finder.find_path(start, destination, matrix)

        if path:
            orientation = characters.Facing(coordinates.sub_coords(path[0], self.position))
            turn_right = [(Facing.RIGHT, Facing.DOWN), (Facing.DOWN, Facing.LEFT), (Facing.LEFT, Facing.UP),
                          (Facing.UP, Facing.RIGHT)]
            turn_left = [(Facing.RIGHT, Facing.UP), (Facing.UP, Facing.LEFT), (Facing.LEFT, Facing.DOWN),
                         (Facing.DOWN, Facing.RIGHT)]
            turn_back = [(Facing.RIGHT, Facing.LEFT), (Facing.UP, Facing.DOWN), (Facing.LEFT, Facing.RIGHT),
                         (Facing.DOWN, Facing.UP)]
            if (self.facing, orientation) in turn_right:
                return characters.Action.TURN_RIGHT
            if (self.facing, orientation) in turn_left:
                return characters.Action.TURN_LEFT
            if (self.facing, orientation) in turn_back:
                return characters.Action.TURN_RIGHT
        else:
            if random.random() < EXPLORE_COEF:
                return characters.Action.TURN_RIGHT
            next_step = [self.position.x + self.facing.value[0],
                         self.position.y + self.facing.value[1]]
            if self.map[next_step[0], next_step[1]]:
                return characters.Action.STEP_FORWARD
            return characters.Action.TURN_RIGHT

    def update_knowledge(self, knowledge: characters.ChampionKnowledge):
        self.position = knowledge.position
        self.visible_tiles = knowledge.visible_tiles
        char_description = knowledge.visible_tiles[knowledge.position].character
        self.facing = char_description.facing
        self.map[self.position.x, self.position.y] = 1
        for position, description in self.visible_tiles.items():
            if description.type == "land":
                self.map[position[0], position[1]] = 1
            elif description.type == "menhir":
                self.map[position[0], position[1]] = 1
                self.menhir_position = coordinates.Coords(position[0], position[1])

    def is_enemy_ahead(self, knowledge: characters.ChampionKnowledge) -> bool:
        visible_tile = self.position + self.facing.value
        if knowledge.visible_tiles[visible_tile].character:
            return True
        else:
            return False

    def decide(self, knowledge: characters.ChampionKnowledge) -> characters.Action:
        self.update_knowledge(knowledge)

        if self.on_menchir:
            if self.is_enemy_ahead(knowledge):
                return characters.Action.ATTACK
            else:
                return characters.Action.TURN_RIGHT

        else:
            if self.is_enemy_ahead(knowledge):
                return characters.Action.ATTACK
            if self.menhir_position is not None:
                if (self.position.x - self.menhir_position.x, self.position.y - self.menhir_position.y) == (0, 0):
                    self.on_menchir = True
                    pass
                else:
                    return self.follow_the_path(self.menhir_position)
            else:
                if random.random() < EXPLORE_COEF:
                    return characters.Action.TURN_RIGHT
                next_step = [self.position.x + self.facing.value[0],
                             self.position.y + self.facing.value[1]]
                if self.map[next_step[0], next_step[1]]:
                    return characters.Action.STEP_FORWARD
                return characters.Action.TURN_RIGHT

    def praise(self, score: int) -> None:
        pass

    def reset(self, arena_description: arenas.ArenaDescription) -> None:
        pass

    @property
    def name(self) -> str:
        return self.first_name

    @property
    def preferred_tabard(self) -> characters.Tabard:
        return characters.Tabard.WHITE


POTENTIAL_CONTROLLERS = [
    R2D2Controller("R2D2")
]
