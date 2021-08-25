from Common import utility as Utility
from colorama import Fore
from Common.utility import UP, DOWN, LEFT, RIGHT

num_frame_stationary = 10  # TODO changed it!
UNKNOWN = "Unknown"


class Vehicle:
    """
    Vehicle class.
    """

    def __init__(self, name, coordinates, av_intensity, color, direction=UNKNOWN):

        self.name = name

        # Array with 4 coordinates of the bounding box.
        self.coordinates = coordinates
        self.centroid = Utility.get_centroid(coordinates)

        self.color = color
        self.velocity = 0
        self.direction = [direction]
        self.average_intensity = av_intensity

        ### Field to manage stationary vehicles ###
        self.is_stationary = False
        self.iteration = 0

        # Minimum num frame before deleting the vehicle (if stationary)
        self.num_frame_to_remove_vehicle = num_frame_stationary

    def set_coordinates(self, new_coordinates):
        """
        Update coordinates and centroid.

        :param new_coordinates: new coordinates.
        """
        self.is_stationary = False
        self.coordinates = new_coordinates
        self.centroid = Utility.get_centroid(new_coordinates)

    def set_velocity(self, new_value):
        """
        Update velocity.

        :param new_value: new velocity.
        """
        self.velocity = round(new_value, 3)

    def set_direction(self, new_direction):
        """
        Update the direction.

        :param new_direction: new direction.
        """
        self.direction.insert(0, new_direction)

        if len(self.direction) > 10:
            del self.direction[-1]

    def get_direction(self):
        """
        Get direction of the vehicle.
        """

        count_up = 0
        count_down = 0
        count_left = 0
        count_right = 0

        for direction in self.direction:
            if direction == UP:
                count_up += 1

            elif direction == DOWN:
                count_down += 1

            elif direction == LEFT:
                count_left += 1

            elif direction == RIGHT:
                count_right += 1

        max_direction = max(count_up, count_down, count_left, count_right)

        text_direction = ""
        if max_direction == count_up:
            text_direction = UP

        elif max_direction == count_down:
            text_direction = DOWN

        elif max_direction == count_right:
            text_direction = RIGHT

        elif max_direction == count_left:
            text_direction = LEFT

        return text_direction

    def set_intensity(self, intensity):
        """
        Set the new intensity.

        :param intensity: new intensity to update.
        """
        self.average_intensity = intensity

    def marked_as_stationary(self):
        """
        Mark the vehicle as stationary.
        """
        self.is_stationary = True
        self.velocity = 0

    def unmarked_as_stationary(self):
        """
        Unmark the vehicle as stationary.
        """
        self.is_stationary = False
        self.reset_frame_stationary()

    def decrease_frame_stationary(self):
        """
        Decrease number of frame for stationary vehicle.
        """
        if self.is_stationary:
            self.num_frame_to_remove_vehicle -= 1

            return self.num_frame_to_remove_vehicle

        else:
            raise Exception(f"{self.name} not is stationary!")

    def set_iteration(self, iter):
        """
        Update number iterations for stationary vehicle.

        :param iter: new value iteration.
        """
        self.iteration = iter

    def reset_frame_stationary(self):
        """
        Resets (sets default value) the number of frame to remove vehicle into list.
        """
        self.num_frame_to_remove_vehicle = num_frame_stationary

    def to_string(self):
        """
        Print vehicle information.
        """

        return (Fore.RED + f"[Name]: {self.name}\n[Is stationary]: {self.is_stationary}\n[Velocity]: {self.velocity}\n"
                           f"[Direction]: {self.direction}\n[Color]: {self.color}\n[Coordinates]: {self.coordinates}\n"
                           f"[Intensity HSV]: {self.average_intensity}")
