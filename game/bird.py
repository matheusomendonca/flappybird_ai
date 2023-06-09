"""Birds classes."""

import abc
import pickle

import numpy as np
import pygame

from game.pipe import Pipe
from model.constants import Constants
from model.neural_network import NeuralNetwork


class BaseBird(metaclass=abc.ABCMeta):
    """Base class for birds."""
    bird_image = pygame.image.load("img/bird.png")

    def __init__(self,
                 screen,
                 x_coordinate: int = Constants.SCREEN_WIDTH.value // 2,
                 y_coordinate: int = Constants.SCREEN_HEIGHT.value // 2) -> None:

        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.screen = screen
        self.image = self.bird_image.copy()

        self.velocity = 0
        self.alive = True
        self.score = 0
        self.neural_network = NeuralNetwork()

    def jump(self):
        """Jump method."""
        self.velocity = -Constants.JUMP_VELOCITY.value

    def move(self):
        """Move method."""
        self.velocity += Constants.GRAVITY.value
        self.y_coordinate += self.velocity

    def draw(self):
        """Draw bird on screen method."""
        self.screen.blit(self.image, (self.x_coordinate - Constants.BIRD_RADIUS.value,
                         int(self.y_coordinate) - Constants.BIRD_RADIUS.value))

    def change_color(self, color: tuple):
        """Change bird color."""
        self.image.fill(color, special_flags=pygame.BLEND_RGB_MULT)

    def compute_score(self, pipes=list[Pipe]):
        """Compute bird score: number of overcame pipes."""

        for pipe in pipes:
            pipe_checkpoint = pipe.x_coordinate + Constants.PIPE_WIDTH.value/2
            bird_checkpoint = self.x_coordinate
            if pipe_checkpoint > bird_checkpoint and pipe_checkpoint - bird_checkpoint < Constants.PIPE_SPEED.value:
                self.score += 1

    @abc.abstractmethod
    def compute_fitness(self):
        """Fitness for optimization."""


class AIBird(BaseBird):
    """Concrete class for training Birds."""

    def __init__(self,
                 screen,
                 x_coordinate: int = Constants.SCREEN_WIDTH.value // 2,
                 y_coordinate: int = Constants.SCREEN_HEIGHT.value // 2):
        super().__init__(screen=screen,
                         x_coordinate=x_coordinate,
                         y_coordinate=y_coordinate)
        self.manual_play = False
        self.neural_network_inputs = None
        self.fitness = 0

    def jump_decision(self, pipes: list[Pipe]):
        """Checks sensors and decide whether to jump."""

        # neural network inputs update
        self._bird_sensors(pipes=pipes)

        # Pass inputs through neural network and make jump decision
        decision = self.neural_network.predict(
            self.neural_network_inputs)[0, 0]
        if decision > 0.5:
            self.jump()

    def load_neural_network_weights(self, filename: str):
        """Load pre-saved NN weights."""

        # Load the pickled bird instance
        with open(filename, "rb") as file:
            bird_parameters = pickle.load(file)

        # load weights
        self.neural_network.weights1 = bird_parameters['weights1']
        self.neural_network.weights2 = bird_parameters['weights2']
        self.neural_network.biases1 = bird_parameters['biases1']
        self.neural_network.biases2 = bird_parameters['biases2']

    def _bird_sensors(self, pipes: list[Pipe]) -> np.ndarray:
        """Bird sensors on environment."""

        # find closest upcoming pipe
        distance_to_pipes = np.array([pipe.x_coordinate - self.x_coordinate for pipe in pipes])
        distance_to_pipes[distance_to_pipes < 0] = 1e6
        index_closest_pipe = np.argmin(distance_to_pipes)
        closest_pipe = pipes[index_closest_pipe]

        # distance to midpoint (y-axis)
        distance_to_mid_point_closest = (
            closest_pipe.bottom_start + closest_pipe.top_height)/2 - self.y_coordinate

        # horizontal distance to next pipe
        horizontal_distance = closest_pipe.x_coordinate + Constants.PIPE_WIDTH.value/2 - self.x_coordinate

        # Prepare inputs for neural network
        self.neural_network_inputs = np.array([[
            distance_to_mid_point_closest,
            horizontal_distance,
            self.y_coordinate
        ]])

    def compute_fitness(self) -> None:
        """Fitness for optimization."""

        vertical_distance_score = 1/(self.neural_network_inputs[0][0]+1e4)
        self.fitness += 1/Constants.SCREEN_WIDTH.value + vertical_distance_score


class ManualBird(BaseBird):
    """Concrete class for Birds in manual mode."""

    def __init__(self,
                 screen,
                 x_coordinate: int = Constants.SCREEN_WIDTH.value // 2,
                 y_coordinate: int = Constants.SCREEN_HEIGHT.value // 2):
        super().__init__(screen=screen,
                         x_coordinate=x_coordinate,
                         y_coordinate=y_coordinate)
        self.manual_play = True
        self.change_color(color=(255, 0, 0))

    def compute_fitness(self) -> None:
        pass
