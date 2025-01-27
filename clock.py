import time
from adafruit_display_text.label import Label
from base_view import BaseView


class ClockView(BaseView):
    def __init__(self, palette, font, display, blink=True):
        super().__init__(palette, font, display)

        self.clock_label = Label(font)
        self.group.append(self.clock_label)

        self.blink = blink
        self.palette = palette

    def update(self):
        # Called every loop iteration. Just update_time for the clock.
        self.update_time()

    def update_time(self, hours=None, minutes=None, show_colon=False):
        now = time.localtime()  # Get the time values we need
        if hours is None:
            hours = now[3]
        if hours >= 18 or hours < 6:  # evening hours to morning
            self.clock_label.color = self.palette[1]
        else:
            self.clock_label.color = self.palette[3]  # daylight hours
        if hours > 12:  # Handle times later than 12:59
            hours -= 12
        elif not hours:  # Handle times between 0:00 and 0:59
            hours = 12

        if minutes is None:
            minutes = now[4]

        seconds = now[5]

        if self.blink:
            colon = ":" if show_colon or now[5] % 2 else " "
        else:
            colon = ":"

        self.clock_label.text = "{hours}{colon}{minutes:02d}{colon}{seconds:02d}".format(
            hours=hours, minutes=minutes, colon=colon, seconds=seconds
        )

        bbx, bby, bbwidth, bbh = self.clock_label.bounding_box
        # Center the label
        self.clock_label.x = round(self.display.width / 2 - bbwidth / 2)
        self.clock_label.y = self.display.height // 2
