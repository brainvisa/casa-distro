# -*- coding: utf-8 -*-
class ImageBuilder:
    def __init__(self, name):
        self.name = name
        self.steps = []

    def step(self, step_function):
        self.steps.append(step_function)
