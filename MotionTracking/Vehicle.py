from Common import utility as Utility
from colorama import Fore

num_frame_stationary = 3


class Vehicle:
    """
    Vehicle class.
    """

    def __init__(self, name, coordinates, direction="Unknown"):

        self.name = name

        # Array with 4 coordinates of the bouding box.
        self.coordinates = coordinates
        self.centroid = Utility.get_centroid(coordinates)

        self.color = Utility.get_random_color()
        self.velocity = 0
        self.direction = direction

        ### Field to manage stationary vehicles ###
        self.is_stationary = False
        self.iteration = 0

        # Minimum num frame before deleting the vehicle (if stationary)
        self.num_frame_to_remove_vehicle = num_frame_stationary

    def set_coordinates(self, new_coordinates):
        """
        Update cordinates and centroid.

        :param new_coordinates: new corddinates.
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
        self.direction = new_direction

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
                           f"[Color]: {self.color}\n[Coordinates]: {self.coordinates}")
