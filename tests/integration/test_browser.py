import time
import random
from dotenv import dotenv_values
from seleniumbase import BaseCase

config = dotenv_values(".env")


class ImageSelectionTest(BaseCase):
    def test_image_selection(self):
        self.open("http://localhost:8001")
        while self.is_element_visible(".image-container img"):
            images = self.find_elements(".image-container img")
            if images:
                image_to_click = random.choice(images)
                image_to_click.click()
                time.sleep(0.05)
            else:
                break
        assert not self.is_element_visible(
            ".image-container img"
        ), "Survey is not completed."
